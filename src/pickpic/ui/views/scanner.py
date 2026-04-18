from __future__ import annotations

import time

import flet as ft

STAGES = [
    (ft.Icons.SEARCH, "Discovering files"),
    (ft.Icons.IMAGE_SEARCH, "Scanning images"),
    (ft.Icons.COMPARE_ARROWS, "Finding duplicates"),
]


class ScannerView(ft.Column):
    def __init__(self):
        self.current_stage = 0
        self._start_time: float | None = None
        self.done = 0
        self.total = 0
        self.current_file = ""

        self._stage_dots: list[ft.Container] = []
        self._stage_icons: list[ft.Icon] = []
        self._stage_labels: list[ft.Text] = []
        self._stage_rows: list[ft.Row] = []
        for icon_name, label in STAGES:
            ic = ft.Icon(icon_name, size=14, color=ft.Colors.OUTLINE)
            dot = ft.Container(
                width=28, height=28, border_radius=14,
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                alignment=ft.alignment.Alignment.CENTER,
                content=ic,
            )
            lbl = ft.Text(label, size=13, color=ft.Colors.OUTLINE)
            self._stage_dots.append(dot)
            self._stage_icons.append(ic)
            self._stage_labels.append(lbl)
            self._stage_rows.append(ft.Row(controls=[dot, lbl], spacing=10))

        self._percent = ft.Text("", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY)
        self._bar = ft.ProgressBar(value=None, width=440)
        self._detail = ft.Text("", size=13, color=ft.Colors.OUTLINE)
        self._eta = ft.Text("", size=13, color=ft.Colors.PRIMARY)
        self._file = ft.Text(
            "", size=11, color=ft.Colors.OUTLINE,
            overflow=ft.TextOverflow.ELLIPSIS, width=440,
        )
        self._spinner = ft.ProgressRing(
            width=20, height=20, stroke_width=2, color=ft.Colors.PRIMARY
        )

        super().__init__(
            controls=[
                ft.Container(expand=True),
                ft.Icon(ft.Icons.PHOTO_LIBRARY, size=56, color=ft.Colors.PRIMARY),
                ft.Container(height=24),
                *self._stage_rows,
                ft.Container(height=24),
                self._percent,
                ft.Container(height=8),
                self._bar,
                ft.Container(height=6),
                self._detail,
                self._eta,
                self._file,
                ft.Container(height=8),
                self._spinner,
                ft.Container(expand=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            expand=True,
        )

    # Called from scan thread — only mutates plain Python state
    def set_stage(self, stage: int):
        self.current_stage = stage
        self._start_time = time.monotonic() if stage == 1 else None
        self.done = 0
        self.total = 0
        self.current_file = ""

    def update_progress(self, done: int, total: int, current: str):
        if self._start_time is None and done > 0:
            self._start_time = time.monotonic()
        self.done = done
        self.total = total
        self.current_file = current

    # Called from Flet's async event loop — safe to update controls
    def render(self, page: ft.Page):
        done, total = self.done, self.total

        for i in range(len(STAGES)):
            icon_name, _ = STAGES[i]
            dot = self._stage_dots[i]
            ic = self._stage_icons[i]
            lbl = self._stage_labels[i]

            if i < self.current_stage:
                dot.bgcolor = ft.Colors.PRIMARY
                ic.name = ft.Icons.CHECK
                ic.color = ft.Colors.ON_PRIMARY
                lbl.color = ft.Colors.ON_SURFACE
                lbl.weight = ft.FontWeight.W_400
            elif i == self.current_stage:
                dot.bgcolor = ft.Colors.PRIMARY_CONTAINER
                ic.name = icon_name
                ic.color = ft.Colors.PRIMARY
                lbl.color = ft.Colors.ON_SURFACE
                lbl.weight = ft.FontWeight.W_600
            else:
                dot.bgcolor = ft.Colors.SURFACE_CONTAINER
                ic.name = icon_name
                ic.color = ft.Colors.OUTLINE
                lbl.color = ft.Colors.OUTLINE
                lbl.weight = ft.FontWeight.W_400

        if total > 0:
            pct = int(done / total * 100)
            self._bar.value = done / total
            self._percent.value = f"{pct}%"
            self._detail.value = f"{done:,} / {total:,} files"
            self._eta.value = self._calc_eta(done, total)
        else:
            self._bar.value = None
            self._percent.value = ""
            self._detail.value = ""
            self._eta.value = ""

        self._file.value = self.current_file[-60:] if self.current_file else ""
        page.update()

    def _calc_eta(self, done: int, total: int) -> str:
        if not self._start_time or done == 0:
            return ""
        elapsed = time.monotonic() - self._start_time
        rate = done / elapsed
        remaining = (total - done) / rate
        if remaining < 60:
            return f"ETA: {int(remaining)}s"
        minutes, seconds = divmod(int(remaining), 60)
        if minutes < 60:
            return f"ETA: {minutes}m {seconds}s"
        hours, minutes = divmod(minutes, 60)
        return f"ETA: {hours}h {minutes}m"

    def set_phase(self, label: str):
        pass
