from __future__ import annotations

import flet as ft


class AboutView(ft.Column):
    def __init__(
        self,
        app_name: str,
        repo_url: str,
        support_url: str,
        on_open_repo: callable,
        on_open_support: callable,
    ):
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    padding=32,
                    content=ft.Column(
                        spacing=20,
                        controls=[
                            ft.Text(app_name, size=28, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "A desktop app for cleaning image collections faster. "
                                "Find exact duplicates, similar images, blurry shots, "
                                "missing geotags, and photos that are not facing north.",
                                size=14,
                                color=ft.Colors.OUTLINE,
                            ),
                            ft.ResponsiveRow(
                                controls=[
                                    self._info_card(
                                        "What It Does",
                                        [
                                            "Detects exact duplicates and visually similar photos",
                                            "Flags blurry images for cleanup",
                                            "Surfaces images without EXIF geotag data",
                                            "Groups images that are not facing north from EXIF heading",
                                        ],
                                    ),
                                    self._info_card(
                                        "Built For",
                                        [
                                            "Camera roll cleanup",
                                            "Field documentation review",
                                            "Batch image triage before archiving",
                                            "Fast local scanning with cached metadata",
                                        ],
                                    ),
                                ]
                            ),
                            ft.Container(
                                border_radius=12,
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                padding=20,
                                content=ft.Column(
                                    spacing=10,
                                    controls=[
                                        ft.Text("Support The Project", size=18, weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            "If Pickapic helps you, give the GitHub repo a star. "
                                            "It helps people discover the project and signals which features matter. "
                                            "If you want to support development directly, you can also send support via Ko-fi.",
                                            size=13,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                                        ),
                                        ft.Row(
                                            wrap=True,
                                            spacing=12,
                                            controls=[
                                                ft.FilledButton(
                                                    "Give Star on GitHub",
                                                    icon=ft.Icons.STAR,
                                                    on_click=lambda _: on_open_repo(),
                                                    style=ft.ButtonStyle(
                                                        shape=ft.RoundedRectangleBorder(radius=10)
                                                    ),
                                                ),
                                                ft.OutlinedButton(
                                                    "Support on Ko-fi",
                                                    icon=ft.Icons.FAVORITE_OUTLINE,
                                                    on_click=lambda _: on_open_support(),
                                                    style=ft.ButtonStyle(
                                                        color=ft.Colors.ON_PRIMARY_CONTAINER,
                                                        side=ft.BorderSide(1, ft.Colors.ON_PRIMARY_CONTAINER),
                                                        shape=ft.RoundedRectangleBorder(radius=10),
                                                    ),
                                                ),
                                            ],
                                        ),
                                        ft.TextButton(
                                            repo_url,
                                            on_click=lambda _: on_open_repo(),
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                                                padding=ft.padding.all(0),
                                            ),
                                        ),
                                        ft.TextButton(
                                            support_url,
                                            on_click=lambda _: on_open_support(),
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                                                padding=ft.padding.all(0),
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                )
            ],
        )

    def _info_card(self, title: str, items: list[str]) -> ft.Control:
        return ft.Container(
            col={"xs": 12, "md": 6},
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            padding=18,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                    *[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.PRIMARY),
                                ft.Text(item, size=12, color=ft.Colors.OUTLINE, expand=True),
                            ],
                        )
                        for item in items
                    ],
                ],
            ),
        )
