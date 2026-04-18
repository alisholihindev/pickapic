from __future__ import annotations

import base64
import io
import os
import threading
from pathlib import Path

import flet as ft
from PIL import Image, UnidentifiedImageError

from pickpic.config import APP_NAME, Settings
from pickpic.core import index as db
from pickpic.core import actions
from pickpic.core.scanner import scan_new_only
from pickpic.core.similarity import find_hash_groups
from pickpic.ui.components.sidebar import make_sidebar
from pickpic.ui.components.action_bar import ActionBar
from pickpic.ui.views.scanner import ScannerView
from pickpic.ui.views.results import ResultsView
from pickpic.ui.views.settings import SettingsView


class PickPicApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = APP_NAME
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
        self.page.padding = 0
        self.page.spacing = 0

        db.init_db()
        self.con = db.get_conn()

        self._settings = Settings.load()
        self.folders: list[str] = []
        self.active_tab = "exact"
        self._settings_active = False
        self.selected_ids: set[int] = set()
        self.selected_paths: dict[int, str] = {}
        self._scanning = False

        self._folder_picker = ft.FilePicker()
        self._move_picker = ft.FilePicker()

        self._action_bar = ActionBar(
            on_delete=self._handle_delete,
            on_move=self._handle_move,
            on_rename=self._handle_rename,
            on_undo=self._handle_undo,
        )
        self._sidebar_slot = ft.Container(content=self._make_sidebar(), width=220)
        self._main_content = ft.Container(content=self._empty_view(), expand=True)

        page.add(
            ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Row(
                        expand=True,
                        spacing=0,
                        controls=[self._sidebar_slot, self._main_content],
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    self._action_bar,
                ],
            )
        )

    # ──────────────────────────────────────────────
    # Layout helpers
    # ──────────────────────────────────────────────

    def _make_sidebar(self) -> ft.Control:
        return make_sidebar(
            folders=self.folders,
            counts=self._get_counts(),
            active_tab=self.active_tab,
            on_add_folder=self._add_folder,
            on_remove_folder=self._remove_folder,
            on_tab_change=self._switch_tab,
            on_scan=self._start_scan,
            on_settings=self._open_settings,
            settings_active=self._settings_active,
        )

    def _get_counts(self) -> dict:
        return {
            "exact": db.count_groups(self.con, "exact"),
            "similar": db.count_groups(self.con, "similar"),
            "blurry": db.count_blurry(self.con),
            "total": db.count_scanned(self.con),
        }

    def _empty_view(self) -> ft.Control:
        return ft.Container(
            expand=True,
            alignment=ft.alignment.Alignment.CENTER,
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.PHOTO_LIBRARY, size=80, color=ft.Colors.OUTLINE),
                    ft.Text(
                        "Add folders and click Scan to start",
                        size=16,
                        color=ft.Colors.OUTLINE,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            ),
        )

    def _refresh_sidebar(self):
        self._sidebar_slot.content = self._make_sidebar()
        self._sidebar_slot.update()

    def _set_main(self, control: ft.Control):
        self._main_content.content = control
        self._main_content.update()

    def _show_results(self):
        view = ResultsView(
            con=self.con,
            group_type=self.active_tab,
            selected_ids=self.selected_ids,
            on_select=self._toggle_select,
            on_preview=self._show_preview,
        )
        view.load_page(reset=True)
        self._set_main(view)

    # ──────────────────────────────────────────────
    # Folder management
    # ──────────────────────────────────────────────

    async def _add_folder(self, e=None):
        path = await self._pick_directory(self._folder_picker)
        if path and path not in self.folders:
            self.folders.append(path)
            self._refresh_sidebar()

    def _remove_folder(self, folder: str):
        self.folders = [f for f in self.folders if f != folder]
        self._refresh_sidebar()

    # ──────────────────────────────────────────────
    # Scan pipeline
    # ──────────────────────────────────────────────

    async def _start_scan(self, e=None):
        import asyncio
        if self._scanning:
            return
        if not self.folders:
            self._snack("Add at least one folder first.")
            return

        self._scanning = True
        scanner_view = ScannerView()
        self._set_main(scanner_view)

        threading.Thread(target=self._run_scan, args=(scanner_view,), daemon=True).start()

        while self._scanning:
            scanner_view.render(self.page)
            await asyncio.sleep(0.2)

        scanner_view.render(self.page)

    def _run_scan(self, scanner_view: ScannerView):
        scan_con = db.get_conn()
        try:
            def progress(done, total, path):
                if total == 0:
                    scanner_view.set_stage(0)
                else:
                    if scanner_view.current_stage != 1:
                        scanner_view.set_stage(1)
                    scanner_view.update_progress(done, total, path)

            results = scan_new_only(
                self.folders,
                is_cached_fn=lambda p, m, s: db.is_cached(scan_con, p, m, s),
                progress_cb=progress,
                blur_threshold=self._settings.blur_threshold,
                min_file_size_bytes=self._settings.min_file_size_kb * 1024,
            )

            scan_con.execute("BEGIN")
            for r in results:
                db.upsert_image(scan_con, **r)
            scan_con.commit()

            scanner_view.set_stage(2)
            hashes = db.get_all_hashes(scan_con)

            exact_groups, similar_groups = find_hash_groups(
                hashes,
                hash_distance_similar=self._settings.hash_distance_similar,
            )

            scan_con.execute("BEGIN")
            db.clear_groups(scan_con)
            for g in exact_groups:
                db.insert_group(scan_con, "exact", [{"image_id": i, "score": 1.0} for i in g])
            for g in similar_groups:
                db.insert_group(scan_con, "similar", [{"image_id": i, "score": 0.9} for i in g])
            scan_con.commit()

            self._refresh_sidebar()
            self._show_results()
        except Exception as exc:
            self._snack(f"Scan error: {exc}")
        finally:
            scan_con.close()
            self._scanning = False

    # ──────────────────────────────────────────────
    # Tab switching & selection
    # ──────────────────────────────────────────────

    def _switch_tab(self, key: str):
        self.active_tab = key
        self._settings_active = False
        self.selected_ids.clear()
        self.selected_paths.clear()
        self._action_bar.update_count(0)
        self._refresh_sidebar()
        self._show_results()

    def _open_settings(self):
        self._settings_active = True
        self._refresh_sidebar()
        self._set_main(SettingsView(
            settings=self._settings,
            on_save=self._apply_settings,
            on_reset_db=self._handle_reset_db,
        ))

    def _handle_reset_db(self):
        def confirm(e):
            self.page.pop_dialog()
            db.reset_db(self.con)
            self._clear_selection()
            self._refresh_sidebar()
            self._set_main(self._empty_view())
            self._snack("Cache cleared. Add folders and scan again.")

        dlg = ft.AlertDialog(
            title=ft.Text("Reset Cache?"),
            content=ft.Text(
                "This will delete all scanned data and duplicate groups.\n"
                "Your image files will not be touched."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ft.TextButton(
                    "Reset",
                    on_click=confirm,
                    style=ft.ButtonStyle(color=ft.Colors.ERROR),
                ),
            ],
        )
        self.page.show_dialog(dlg)

    def _apply_settings(self):
        self._settings_active = False
        self._refresh_sidebar()
        self._snack("Settings saved. Re-grouping...")
        threading.Thread(target=self._regroup, daemon=True).start()

    def _regroup(self):
        con = db.get_conn()
        try:
            threshold = self._settings.blur_threshold
            rows = con.execute(
                "SELECT id, blur_score FROM images WHERE blur_score IS NOT NULL"
            ).fetchall()
            con.execute("BEGIN")
            for row in rows:
                con.execute(
                    "UPDATE images SET is_blurry=? WHERE id=?",
                    (1 if row["blur_score"] < threshold else 0, row["id"]),
                )
            con.commit()

            hashes = db.get_all_hashes(con)
            exact_groups, similar_groups = find_hash_groups(
                hashes,
                hash_distance_similar=self._settings.hash_distance_similar,
            )
            con.execute("BEGIN")
            db.clear_groups(con)
            for g in exact_groups:
                db.insert_group(con, "exact", [{"image_id": i, "score": 1.0} for i in g])
            for g in similar_groups:
                db.insert_group(con, "similar", [{"image_id": i, "score": 0.9} for i in g])
            con.commit()

            self._refresh_sidebar()
            self._show_results()
            self._snack("Re-grouping complete.")
        except Exception as exc:
            self._snack(f"Re-group error: {exc}")
        finally:
            con.close()

    def _toggle_select(self, member: dict, checked: bool):
        iid = member["id"]
        if checked:
            self.selected_ids.add(iid)
            self.selected_paths[iid] = member["path"]
        else:
            self.selected_ids.discard(iid)
            self.selected_paths.pop(iid, None)
        self._action_bar.update_count(len(self.selected_ids))

    # ──────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────

    def _handle_delete(self, e=None):
        if not self.selected_paths:
            return
        paths = list(self.selected_paths.values())

        def confirm(e):
            self.page.pop_dialog()
            actions.delete(self.con, paths)
            self._clear_selection()
            self._refresh_sidebar()
            self._show_results()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete files?"),
            content=ft.Text(f"Send {len(paths)} file(s) to trash?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ft.TextButton(
                    "Delete",
                    on_click=confirm,
                    style=ft.ButtonStyle(color=ft.Colors.ERROR),
                ),
            ],
        )
        self.page.show_dialog(dlg)

    async def _handle_move(self, e=None):
        if not self.selected_paths:
            return
        path = await self._pick_directory(self._move_picker)
        if path:
            actions.move(self.con, list(self.selected_paths.values()), path)
            self._clear_selection()
            self._refresh_sidebar()
            self._show_results()

    def _handle_rename(self, e=None):
        if len(self.selected_paths) != 1:
            self._snack("Select exactly one image to rename.")
            return

        _, path = next(iter(self.selected_paths.items()))
        old_name = os.path.basename(path)
        field = ft.TextField(value=old_name, autofocus=True, label="New filename")

        def do_rename(e):
            new_name = field.value.strip()
            if not new_name:
                return
            try:
                actions.rename(self.con, path, new_name)
                self.page.pop_dialog()
                self._clear_selection()
                self._show_results()
            except FileExistsError:
                field.error_text = "A file with that name already exists."
                field.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Rename file"),
            content=field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                ft.TextButton("Rename", on_click=do_rename),
            ],
        )
        self.page.show_dialog(dlg)

    def _handle_undo(self, e=None):
        n = actions.undo_last(self.con)
        msg = f"Undid {n} operation(s)." if n else "Nothing to undo."
        self._snack(msg)
        if n:
            self._show_results()

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _show_preview(self, path: str):
        try:
            with Image.open(path) as img:
                img.thumbnail((800, 600), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode()
                orig_w, orig_h = img.size
        except (UnidentifiedImageError, OSError):
            self._snack("Could not open image.")
            return

        size = Path(path).stat().st_size if Path(path).exists() else 0
        size_str = f"{size / 1024 / 1024:.2f} MB" if size >= 1024 * 1024 else f"{size / 1024:.1f} KB"

        dlg = ft.AlertDialog(
            title=ft.Text(Path(path).name, overflow=ft.TextOverflow.ELLIPSIS),
            content=ft.Column(
                tight=True,
                controls=[
                    ft.Image(src=f"data:image/jpeg;base64,{b64}", fit=ft.BoxFit.CONTAIN, width=800, height=550),
                    ft.Text(path, size=10, color=ft.Colors.OUTLINE, selectable=True),
                    ft.Text(f"{orig_w}×{orig_h}  ·  {size_str}", size=11, color=ft.Colors.OUTLINE),
                ],
            ),
            actions=[ft.TextButton("Close", on_click=lambda _: self.page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    async def _pick_directory(self, picker: ft.FilePicker) -> str | None:
        try:
            return await picker.get_directory_path()
        except Exception:
            return await self._pick_directory_text()

    async def _pick_directory_text(self) -> str | None:
        import asyncio
        result: list[str | None] = [None]
        done = asyncio.Event()
        field = ft.TextField(
            label="Folder path",
            hint_text="/home/user/Pictures",
            autofocus=True,
            expand=True,
        )

        def confirm(e):
            val = field.value.strip()
            result[0] = val if val else None
            self.page.pop_dialog()
            done.set()

        def cancel(e):
            self.page.pop_dialog()
            done.set()

        dlg = ft.AlertDialog(
            title=ft.Text("Enter folder path"),
            content=field,
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.TextButton("OK", on_click=confirm),
            ],
        )
        self.page.show_dialog(dlg)
        await done.wait()
        path = result[0]
        if path and not Path(path).is_dir():
            self._snack(f"Not a valid directory: {path}")
            return None
        return path

    def _clear_selection(self):
        self.selected_ids.clear()
        self.selected_paths.clear()
        self._action_bar.update_count(0)

    def _snack(self, msg: str):
        self.page.show_dialog(ft.SnackBar(ft.Text(msg)))
