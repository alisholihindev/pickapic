from __future__ import annotations

import flet as ft


class ScannerView(ft.Column):
    def __init__(self):
        self._phase = ft.Text(
            "Discovering files...",
            size=18,
            weight=ft.FontWeight.W_600,
        )
        self._percent = ft.Text(
            "",
            size=48,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.PRIMARY,
        )
        self._bar = ft.ProgressBar(value=None, width=400)  # indeterminate initially
        self._total_label = ft.Text(
            "",
            size=13,
            weight=ft.FontWeight.W_500,
        )
        self._count = ft.Text(
            "",
            size=13,
            color=ft.Colors.OUTLINE,
        )
        self._file = ft.Text(
            "",
            size=11,
            color=ft.Colors.OUTLINE,
            overflow=ft.TextOverflow.ELLIPSIS,
            width=400,
        )
        super().__init__(
            controls=[
                ft.Container(expand=True),
                ft.Icon(ft.Icons.IMAGE_SEARCH, size=64, color=ft.Colors.PRIMARY),
                ft.Container(height=4),
                self._phase,
                ft.Container(height=4),
                self._total_label,
                ft.Container(height=12),
                self._percent,
                ft.Container(height=8),
                self._bar,
                ft.Container(height=6),
                self._count,
                self._file,
                ft.Container(expand=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            expand=True,
        )

    def update_progress(self, done: int, total: int, current: str):
        if total > 0:
            pct = int(done / total * 100)
            self._bar.value = done / total
            self._phase.value = "Scanning images..."
            self._total_label.value = f"Total: {total:,} files found"
        else:
            pct = 0
            self._bar.value = None

        self._percent.value = f"{pct}%"
        self._count.value = f"{done:,} / {total:,} processed" if total > 0 else ""
        self._file.value = current[-60:] if current else ""

        try:
            self._phase.update()
            self._total_label.update()
            self._percent.update()
            self._bar.update()
            self._count.update()
            self._file.update()
        except Exception:
            pass

    def set_phase(self, label: str):
        self._phase.value = label
        self._percent.value = ""
        self._bar.value = None
        self._count.value = ""
        self._file.value = ""
        try:
            self._phase.update()
            self._percent.update()
            self._bar.update()
            self._count.update()
            self._file.update()
        except Exception:
            pass
