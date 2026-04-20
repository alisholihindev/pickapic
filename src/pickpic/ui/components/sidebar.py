from __future__ import annotations

import flet as ft


def make_sidebar(
    folders: list[str],
    counts: dict,
    active_tab: str,
    on_add_folder,
    on_remove_folder,
    on_tab_change,
    on_scan,
    scan_label: str = "Scan",
    scan_icon=ft.Icons.SEARCH,
    on_settings=None,
    settings_active: bool = False,
) -> ft.Control:

    def tab_item(label: str, key: str, icon, count: int) -> ft.Control:
        is_active = active_tab == key
        return ft.Container(
            border_radius=8,
            bgcolor=ft.Colors.PRIMARY_CONTAINER if is_active else ft.Colors.TRANSPARENT,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            on_click=lambda _, k=key: on_tab_change(k),
            content=ft.Row(
                controls=[
                    ft.Icon(
                        icon,
                        size=16,
                        color=ft.Colors.ON_PRIMARY_CONTAINER if is_active else ft.Colors.OUTLINE,
                    ),
                    ft.Text(
                        label,
                        size=13,
                        weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                        color=ft.Colors.ON_PRIMARY_CONTAINER if is_active else ft.Colors.ON_SURFACE,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text(str(count), size=11, color=ft.Colors.OUTLINE),
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    ),
                ],
                spacing=8,
            ),
        )

    folder_chips = [
        ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OUTLINED, size=14, color=ft.Colors.PRIMARY),
                    ft.Text(f, size=12, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        icon_size=14,
                        on_click=lambda _, fld=f: on_remove_folder(fld),
                        tooltip="Remove",
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=6, vertical=4),
            border_radius=6,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
        )
        for f in folders
    ]

    total_groups = sum(counts.get(k, 0) for k in ("exact", "similar"))

    return ft.Container(
        width=220,
        bgcolor=ft.Colors.SURFACE,
        border=ft.border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        padding=ft.padding.symmetric(horizontal=12, vertical=16),
        content=ft.Column(
            controls=[
                ft.Text("PickPic", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=12),
                ft.Text("Folders", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.OUTLINE),
                ft.Column(controls=folder_chips, spacing=4),
                ft.ElevatedButton(
                    "Add Folder",
                    icon=ft.Icons.ADD,
                    on_click=on_add_folder,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
                ft.Divider(height=12),
                ft.FilledButton(
                    scan_label,
                    icon=scan_icon,
                    on_click=on_scan,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
                ft.Divider(height=12),
                ft.Text("Categories", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.OUTLINE),
                tab_item("Exact Dupes", "exact", ft.Icons.COPY_ALL, counts.get("exact", 0)),
                tab_item("Similar", "similar", ft.Icons.COMPARE, counts.get("similar", 0)),
                tab_item("Blurry", "blurry", ft.Icons.BLUR_ON, counts.get("blurry", 0)),
                ft.Divider(height=12),
                ft.Container(
                    border_radius=8,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER if settings_active else ft.Colors.TRANSPARENT,
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    on_click=lambda _: on_settings() if on_settings else None,
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.TUNE,
                                size=16,
                                color=ft.Colors.ON_PRIMARY_CONTAINER if settings_active else ft.Colors.OUTLINE,
                            ),
                            ft.Text(
                                "Settings",
                                size=13,
                                weight=ft.FontWeight.W_600 if settings_active else ft.FontWeight.W_400,
                                color=ft.Colors.ON_PRIMARY_CONTAINER if settings_active else ft.Colors.ON_SURFACE,
                                expand=True,
                            ),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Divider(height=12),
                ft.Text("Stats", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.OUTLINE),
                ft.Text(f"Scanned: {counts.get('total', 0):,}", size=12),
                ft.Text(f"Groups: {total_groups:,}", size=12),
                ft.Text(f"Blurry: {counts.get('blurry', 0):,}", size=12),
            ],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
