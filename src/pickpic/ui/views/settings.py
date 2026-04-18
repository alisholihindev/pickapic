from __future__ import annotations

import flet as ft

from pickpic.config import Settings, PRESETS


class SettingsView(ft.Column):
    def __init__(self, settings: Settings, on_save: callable, on_reset_db: callable = None):
        self._settings = settings
        self._on_save = on_save
        self._on_reset_db = on_reset_db

        self._preset_row = ft.Row(spacing=8, wrap=True)

        self._sim_slider = ft.Slider(
            min=0, max=30, divisions=30,
            on_change=self._on_sim_change,
        )
        self._sim_label = ft.Text(size=12, color=ft.Colors.OUTLINE)

        self._blur_slider = ft.Slider(
            min=10, max=500, divisions=49,
            on_change=self._on_blur_change,
        )
        self._blur_label = ft.Text(size=12, color=ft.Colors.OUTLINE)

        self._size_field = ft.TextField(
            label="Min file size (KB)",
            hint_text="0 = disabled",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200,
        )

        super().__init__(
            controls=[self._build()],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self._populate()

    def _build(self) -> ft.Control:
        return ft.Container(
            padding=32,
            content=ft.Column(
                spacing=24,
                controls=[
                    ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),

                    ft.Text("Detection Preset", size=14, weight=ft.FontWeight.W_600,
                            color=ft.Colors.OUTLINE),
                    ft.Text(
                        "Quick presets — adjust sliders below for fine-tuning.",
                        size=12, color=ft.Colors.OUTLINE,
                    ),
                    self._preset_row,
                    ft.Divider(),

                    ft.Text("Similar Images Sensitivity", size=14, weight=ft.FontWeight.W_600),
                    ft.Text(
                        "pHash hamming distance threshold. Lower = stricter, fewer false positives.",
                        size=12, color=ft.Colors.OUTLINE,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("Strict", size=11, color=ft.Colors.OUTLINE),
                            ft.Container(content=self._sim_slider, expand=True),
                            ft.Text("Loose", size=11, color=ft.Colors.OUTLINE),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._sim_label,
                    ft.Divider(),

                    ft.Text("Blur Detection Sensitivity", size=14, weight=ft.FontWeight.W_600),
                    ft.Text(
                        "Laplacian variance threshold. Lower = only catches very blurry images.",
                        size=12, color=ft.Colors.OUTLINE,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("Strict", size=11, color=ft.Colors.OUTLINE),
                            ft.Container(content=self._blur_slider, expand=True),
                            ft.Text("Loose", size=11, color=ft.Colors.OUTLINE),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._blur_label,
                    ft.Divider(),

                    ft.Text("File Size Filter", size=14, weight=ft.FontWeight.W_600),
                    ft.Text(
                        "Skip images smaller than this during scan (0 = no filter).",
                        size=12, color=ft.Colors.OUTLINE,
                    ),
                    self._size_field,
                    ft.Divider(),

                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                "Save & Apply",
                                icon=ft.Icons.CHECK,
                                on_click=self._save,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                            ),
                            ft.OutlinedButton(
                                "Reset to Normal",
                                icon=ft.Icons.RESTORE,
                                on_click=self._reset,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                            ),
                        ],
                        spacing=12,
                    ),

                    ft.Divider(),
                    ft.Text("Danger Zone", size=14, weight=ft.FontWeight.W_600,
                            color=ft.Colors.ERROR),
                    ft.Text(
                        "Clear all scanned image data and duplicate groups from the cache. "
                        "Your actual image files will not be affected.",
                        size=12, color=ft.Colors.OUTLINE,
                    ),
                    ft.OutlinedButton(
                        "Reset Cache",
                        icon=ft.Icons.DELETE_SWEEP,
                        on_click=lambda _: self._on_reset_db() if self._on_reset_db else None,
                        style=ft.ButtonStyle(
                            color=ft.Colors.ERROR,
                            side=ft.BorderSide(1, ft.Colors.ERROR),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
            ),
        )

    def _populate(self):
        self._sim_slider.value = float(self._settings.hash_distance_similar)
        self._blur_slider.value = float(self._settings.blur_threshold)
        self._size_field.value = str(self._settings.min_file_size_kb)
        self._update_sim_label()
        self._update_blur_label()
        self._rebuild_preset_chips()

    def _rebuild_preset_chips(self):
        active = self._settings.active_preset
        chips = []
        for name in ("strict", "normal", "loose"):
            is_active = name == active
            chips.append(
                ft.Container(
                    content=ft.Text(
                        name.capitalize(),
                        size=13,
                        weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                        color=ft.Colors.ON_PRIMARY_CONTAINER if is_active else ft.Colors.ON_SURFACE,
                    ),
                    bgcolor=ft.Colors.PRIMARY_CONTAINER if is_active else ft.Colors.SURFACE_CONTAINER,
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    on_click=lambda _, n=name: self._apply_preset(n),
                )
            )
        self._preset_row.controls = chips
        try:
            self._preset_row.update()
        except Exception:
            pass

    def _apply_preset(self, name: str):
        self._settings.apply_preset(name)
        self._sim_slider.value = float(self._settings.hash_distance_similar)
        self._blur_slider.value = float(self._settings.blur_threshold)
        self._update_sim_label()
        self._update_blur_label()
        self._rebuild_preset_chips()
        try:
            self._sim_slider.update()
            self._blur_slider.update()
            self._sim_label.update()
            self._blur_label.update()
        except Exception:
            pass

    def _on_sim_change(self, e):
        self._settings.hash_distance_similar = int(e.control.value)
        self._update_sim_label()
        self._rebuild_preset_chips()
        try:
            self._sim_label.update()
        except Exception:
            pass

    def _on_blur_change(self, e):
        self._settings.blur_threshold = float(e.control.value)
        self._update_blur_label()
        self._rebuild_preset_chips()
        try:
            self._blur_label.update()
        except Exception:
            pass

    def _update_sim_label(self):
        d = self._settings.hash_distance_similar
        if d <= 5:
            desc = "Strict — very close matches only"
        elif d <= 12:
            desc = "Normal — balanced detection"
        else:
            desc = "Loose — catches more potential duplicates"
        self._sim_label.value = f"Distance ≤ {d}  ·  {desc}"

    def _update_blur_label(self):
        t = self._settings.blur_threshold
        if t < 75:
            desc = "Strict — only very blurry images"
        elif t < 150:
            desc = "Normal — moderate blur detection"
        else:
            desc = "Loose — catches mildly blurry images"
        self._blur_label.value = f"Threshold < {t:.0f}  ·  {desc}"

    def _save(self, e=None):
        try:
            kb = int(self._size_field.value or "0")
            self._settings.min_file_size_kb = max(0, kb)
        except ValueError:
            self._settings.min_file_size_kb = 0
        self._settings.save()
        self._on_save()

    def _reset(self, e=None):
        self._settings.apply_preset("normal")
        self._settings.save()
        self._populate()
        try:
            self._sim_slider.update()
            self._blur_slider.update()
            self._sim_label.update()
            self._blur_label.update()
            self._size_field.update()
        except Exception:
            pass
