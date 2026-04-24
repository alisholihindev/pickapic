from __future__ import annotations

import flet as ft

from pickpic.ui.components.group_row import make_group_row
from pickpic.config import RESULTS_PAGE


class ResultsView(ft.ListView):
    def __init__(
        self,
        con,
        group_type: str,
        selected_ids: set,
        on_select: callable,
        on_preview: callable | None = None,
        display_orientation: str = "landscape",
    ):
        super().__init__(spacing=0, expand=True)
        self.con = con
        self.group_type = group_type
        self.selected_ids = selected_ids
        self.on_select = on_select
        self.on_preview = on_preview
        self.display_orientation = display_orientation
        self._groups: list[dict] = []
        self._offset = 0
        self._total = 0

    def _select_all_current(self, _=None):
        for group in self._groups:
            for member in group["members"]:
                self.on_select(member, True)
        self._rebuild_controls()
        self.update()

    def load_page(self, reset: bool = False):
        from pickpic.core.index import (
            count_groups,
            get_blurry_images,
            get_groups_page,
            get_images_not_facing_north,
            get_images_without_geotag,
        )

        if reset:
            self._offset = 0
            self._groups = []

        if self.group_type == "blurry":
            if reset:
                rows = get_blurry_images(self.con)
                self._total = len(rows)
                self._groups = [
                    {
                        "id": None,
                        "members": [{
                            "id": r["id"],
                            "path": r["path"],
                            "blur_score": r["blur_score"],
                            "is_blurry": 1,
                            "size": r["size"] or 0,
                            "width": r["width"] or 0,
                            "height": r["height"] or 0,
                            "has_gps": r["has_gps"],
                            "gps_lat": r["gps_lat"],
                            "gps_lon": r["gps_lon"],
                            "gps_heading": r["gps_heading"],
                            "gps_heading_ref": r["gps_heading_ref"],
                            "is_facing_north": r["is_facing_north"],
                            "score": r["blur_score"],
                        }],
                    }
                    for r in rows
                ]
        elif self.group_type == "no_geotag":
            if reset:
                rows = get_images_without_geotag(self.con)
                self._total = len(rows)
                self._groups = [
                    {
                        "id": None,
                        "members": [{
                            "id": r["id"],
                            "path": r["path"],
                            "blur_score": r["blur_score"],
                            "is_blurry": 0,
                            "size": r["size"] or 0,
                            "width": r["width"] or 0,
                            "height": r["height"] or 0,
                            "has_gps": 0,
                            "gps_lat": None,
                            "gps_lon": None,
                            "score": 0,
                        }],
                    }
                    for r in rows
                ]
        elif self.group_type == "not_north":
            if reset:
                rows = get_images_not_facing_north(self.con)
                self._total = len(rows)
                self._groups = [
                    {
                        "id": None,
                        "members": [{
                            "id": r["id"],
                            "path": r["path"],
                            "blur_score": r["blur_score"],
                            "is_blurry": 0,
                            "size": r["size"] or 0,
                            "width": r["width"] or 0,
                            "height": r["height"] or 0,
                            "has_gps": r["has_gps"],
                            "gps_lat": r["gps_lat"],
                            "gps_lon": r["gps_lon"],
                            "gps_heading": r["gps_heading"],
                            "gps_heading_ref": r["gps_heading_ref"],
                            "is_facing_north": 0,
                            "score": 0,
                        }],
                    }
                    for r in rows
                ]
        else:
            self._total = count_groups(self.con, self.group_type)
            new = get_groups_page(self.con, self.group_type, self._offset, RESULTS_PAGE)
            self._groups.extend(new)
            self._offset += len(new)

        self._rebuild_controls()

    def _rebuild_controls(self):
        if not self._groups:
            self.controls = [
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.Alignment.CENTER,
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=64, color=ft.Colors.OUTLINE),
                            ft.Text("No results in this category.", size=16, color=ft.Colors.OUTLINE),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                )
            ]
            return

        rows: list[ft.Control] = []

        if self.group_type in {"blurry", "no_geotag"}:
            summary_text = (
                f"{self._total:,} blurry images"
                if self.group_type == "blurry"
                else f"{self._total:,} images without GPS"
            )
            rows.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=8),
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                summary_text,
                                size=13,
                                color=ft.Colors.OUTLINE,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "Select All",
                                icon=ft.Icons.SELECT_ALL,
                                on_click=self._select_all_current,
                                style=ft.ButtonStyle(
                                    padding=ft.padding.symmetric(horizontal=8)
                                ),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )

        rows.extend(
            make_group_row(
                g,
                self.selected_ids,
                self.on_select,
                self.group_type,
                on_preview=self.on_preview,
                display_orientation=self.display_orientation,
                on_bulk_change=self.refresh,
            )
            for g in self._groups
        )

        remaining = self._total - len(self._groups)
        if remaining > 0 and self.group_type not in {"blurry", "no_geotag", "not_north"}:
            rows.append(
                ft.TextButton(
                    f"Load more ({remaining} remaining)",
                    on_click=lambda _: self._load_more(),
                )
            )

        self.controls = rows

    def _load_more(self):
        self.load_page()
        self.update()

    def refresh(self):
        self.load_page(reset=True)
        self.update()
