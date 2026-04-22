from __future__ import annotations

import flet as ft

from pickpic.ui.components.image_card import make_image_card


def make_group_row(
    group: dict,
    selected_ids: set,
    on_select: callable,
    group_type: str,
    on_preview: callable | None = None,
    display_orientation: str = "landscape",
) -> ft.Control:
    members = group["members"]
    count_text = f"{len(members)} images"

    def _select_all(_):
        for m in members:
            on_select(m, True)

    def _keep_best(_):
        best = max(members, key=lambda m: (m.get("width") or 0) * (m.get("height") or 0))
        for m in members:
            on_select(m, m["id"] != best["id"])

    cards = [
        make_image_card(
            m,
            on_select=on_select,
            selected=m["id"] in selected_ids,
            on_preview=on_preview,
            display_orientation=display_orientation,
        )
        for m in members
    ]

    header = ft.Container(
        padding=ft.padding.symmetric(horizontal=4, vertical=6),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED, size=14, color=ft.Colors.OUTLINE),
                ft.Text(
                    f"Group  ·  {count_text}",
                    size=12,
                    color=ft.Colors.OUTLINE,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(expand=True),
                ft.TextButton(
                    "Select All",
                    on_click=_select_all,
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=6)),
                ),
                ft.TextButton(
                    "Keep Best",
                    on_click=_keep_best,
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=6)),
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    card_row = ft.Row(
        controls=cards,
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.CrossAxisAlignment.START,
        tight=True,
    )

    return ft.Container(
        padding=ft.padding.symmetric(vertical=6, horizontal=4),
        content=ft.Column(
            spacing=4,
            controls=[
                header,
                card_row,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            ],
        ),
    )
