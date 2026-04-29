from __future__ import annotations

import time

import flet as ft

ALL_STAGES = [
    (0, ft.Icons.SEARCH, "Discovering files"),
    (1, ft.Icons.IMAGE_SEARCH, "Scanning images"),
    (2, ft.Icons.COMPARE_ARROWS, "Finding duplicates"),
    (3, ft.Icons.PLACE, "Grouping geotags"),
]


def _build_stages(feature_duplicates: bool = True, feature_gps: bool = True) -> list[tuple]:
    stages = [
        (ft.Icons.SEARCH, "Discovering files"),
        (ft.Icons.IMAGE_SEARCH, "Scanning images"),
    ]
    if feature_duplicates:
        stages.append((ft.Icons.COMPARE_ARROWS, "Finding duplicates"))
    if feature_gps:
        stages.append((ft.Icons.PLACE, "Grouping geotags"))
    return stages


# Keep backward-compatible default
STAGES = _build_stages()


class ScannerView(ft.Column):
    def __init__(self, on_pause_resume=None, on_abort=None,
                 feature_duplicates: bool = True, feature_gps: bool = True):
        self._active_stages = _build_stages(feature_duplicates, feature_gps)
        # Map from global stage index (0-3) to local display index
        self._stage_map: dict[int, int] = {}
        local = 0
        self._stage_map[0] = local; local += 1  # discover always present
        self._stage_map[1] = local; local += 1  # scan always present
        if feature_duplicates:
            self._stage_map[2] = local; local += 1
        if feature_gps:
            self._stage_map[3] = local; local += 1

        self.current_stage = 0
        self._start_time: float | None = None
        self.done = 0
        self.total = 0
        self.phase_label = ""
        self.current_file = ""
        self.is_paused = False
        self.is_aborting = False
        self._on_pause_resume = on_pause_resume
        self._on_abort = on_abort

        self._stage_dots: list[ft.Container] = []
        self._stage_icons: list[ft.Icon] = []
        self._stage_labels: list[ft.Text] = []
        self._stage_rows: list[ft.Row] = []
        for icon_name, label in self._active_stages:
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
        self._status = ft.Text("", size=12, color=ft.Colors.PRIMARY)
        self._file = ft.Text(
            "", size=11, color=ft.Colors.OUTLINE,
            overflow=ft.TextOverflow.ELLIPSIS, width=440,
        )
        self._spinner = ft.ProgressRing(
            width=20, height=20, stroke_width=2, color=ft.Colors.PRIMARY
        )
        self._pause_button = ft.OutlinedButton(
            "Pause",
            icon=ft.Icons.PAUSE,
            on_click=self._on_pause_resume,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self._abort_button = ft.OutlinedButton(
            "Abort",
            icon=ft.Icons.STOP,
            on_click=self._on_abort,
            style=ft.ButtonStyle(
                color=ft.Colors.ERROR,
                side=ft.BorderSide(1, ft.Colors.ERROR),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        self._actions = ft.Row(
            controls=[self._pause_button, self._abort_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
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
                self._status,
                self._file,
                ft.Container(height=8),
                self._spinner,
                ft.Container(height=16),
                self._actions,
                ft.Container(expand=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            expand=True,
        )

    # Called from scan thread — only mutates plain Python state
    def set_stage(self, stage: int):
        # Map global stage index to local display index
        local = self._stage_map.get(stage, stage)
        self.current_stage = local
        self._start_time = time.monotonic() if local > 0 else None
        self.done = 0
        self.total = 0
        self.phase_label = (
            self._active_stages[local][1]
            if 0 <= local < len(self._active_stages)
            else ""
        )
        self.current_file = ""

    def update_progress(self, done: int, total: int, current: str):
        if self._start_time is None and done > 0:
            self._start_time = time.monotonic()
        self.done = done
        self.total = total
        self.current_file = current

    def set_run_state(self, *, paused: bool, aborting: bool):
        self.is_paused = paused
        self.is_aborting = aborting

    # Called from Flet's async event loop — safe to update controls
    def render(self, page: ft.Page):
        done, total = self.done, self.total

        for i in range(len(self._active_stages)):
            icon_name, _ = self._active_stages[i]
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
            unit = "pairs" if "duplicates" in self.phase_label.lower() else "files"
            prefix = f"{self.phase_label} • " if self.phase_label else ""
            self._detail.value = f"{prefix}{done:,} / {total:,} {unit}"
            self._eta.value = self._calc_eta(done, total)
        else:
            self._bar.value = None
            self._percent.value = ""
            self._detail.value = self.phase_label
            self._eta.value = ""

        if self.is_aborting:
            self._status.value = "Stopping scan..."
            self._status.color = ft.Colors.ERROR
            self._spinner.visible = True
            self._pause_button.disabled = True
            self._abort_button.disabled = True
        elif self.is_paused:
            self._status.value = "Paused"
            self._status.color = ft.Colors.TERTIARY
            self._spinner.visible = False
            self._pause_button.text = "Resume"
            self._pause_button.icon = ft.Icons.PLAY_ARROW
            self._pause_button.disabled = False
            self._abort_button.disabled = False
        else:
            self._status.value = "Scanning in progress"
            self._status.color = ft.Colors.PRIMARY
            self._spinner.visible = True
            self._pause_button.text = "Pause"
            self._pause_button.icon = ft.Icons.PAUSE
            self._pause_button.disabled = False
            self._abort_button.disabled = False

        self._file.value = self.current_file[-60:] if self.current_file else ""
        page.update()

    def _calc_eta(self, done: int, total: int) -> str:
        if not self._start_time or done <= 0 or total <= done:
            return ""
        elapsed = time.monotonic() - self._start_time
        if elapsed <= 0:
            return "ETA: calculating..."
        rate = done / elapsed
        if rate <= 0:
            return "ETA: calculating..."
        remaining = (total - done) / rate
        if remaining < 60:
            return f"ETA: {int(remaining)}s"
        minutes, seconds = divmod(int(remaining), 60)
        if minutes < 60:
            return f"ETA: {minutes}m {seconds}s"
        hours, minutes = divmod(minutes, 60)
        return f"ETA: {hours}h {minutes}m"

    def set_phase(self, label: str):
        self.phase_label = label
