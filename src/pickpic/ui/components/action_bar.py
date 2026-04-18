from __future__ import annotations

import flet as ft


class ActionBar(ft.Row):
    def __init__(self, on_delete, on_move, on_rename, on_undo):
        self._count_text = ft.Text("0 selected", size=13, weight=ft.FontWeight.W_500)
        super().__init__(
            controls=[
                ft.Container(
                    height=52,
                    expand=True,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    padding=ft.padding.symmetric(horizontal=16),
                    border=ft.border.only(top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                    content=ft.Row(
                        controls=[
                            self._count_text,
                            ft.VerticalDivider(width=1),
                            ft.TextButton(
                                "Delete",
                                icon=ft.Icons.DELETE_OUTLINE,
                                on_click=on_delete,
                                style=ft.ButtonStyle(color=ft.Colors.ERROR),
                            ),
                            ft.TextButton(
                                "Move to...",
                                icon=ft.Icons.DRIVE_FILE_MOVE_OUTLINE,
                                on_click=on_move,
                            ),
                            ft.TextButton(
                                "Rename",
                                icon=ft.Icons.EDIT_OUTLINED,
                                on_click=on_rename,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "Undo",
                                icon=ft.Icons.UNDO,
                                on_click=on_undo,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ],
        )

    def update_count(self, n: int):
        self._count_text.value = f"{n} selected"
        try:
            self._count_text.update()
        except Exception:
            pass
