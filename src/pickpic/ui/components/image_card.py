from __future__ import annotations

import base64
import io
from functools import lru_cache
from pathlib import Path

import flet as ft
from PIL import Image, ImageOps, UnidentifiedImageError

from pickpic.config import THUMB_SIZE


@lru_cache(maxsize=512)
def _thumb_b64(path: str) -> str | None:
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail(THUMB_SIZE, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            return base64.b64encode(buf.getvalue()).decode()
    except (UnidentifiedImageError, OSError):
        return None


def _fmt_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def make_image_card(
    member: dict,
    on_select: callable,
    selected: bool = False,
    on_preview: callable | None = None,
    display_orientation: str = "landscape",
) -> ft.Control:
    path = member["path"]
    name = Path(path).name
    size_str = _fmt_size(member.get("size", 0))
    w, h = member.get("width") or 0, member.get("height") or 0
    dim_str = f"{w}×{h}" if w and h else ""
    blur_score = member.get("blur_score")
    is_blurry = bool(member.get("is_blurry"))
    has_gps = member.get("has_gps")
    gps_lat = member.get("gps_lat")
    gps_lon = member.get("gps_lon")
    gps_heading = member.get("gps_heading")
    gps_heading_ref = member.get("gps_heading_ref")
    is_facing_north = member.get("is_facing_north")

    if display_orientation == "portrait":
        thumb_width = 128
        thumb_height = 176
        card_width = 140
    else:
        thumb_width = 148
        thumb_height = 120
        card_width = 160

    b64 = _thumb_b64(path)
    if b64:
        thumb = ft.Container(
            width=thumb_width,
            height=thumb_height,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
            alignment=ft.alignment.Alignment.CENTER,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Image(
                src=f"data:image/jpeg;base64,{b64}",
                width=thumb_width,
                height=thumb_height,
                fit=ft.BoxFit.CONTAIN,
            ),
        )
    else:
        thumb = ft.Container(
            width=thumb_width,
            height=thumb_height,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
            content=ft.Icon(ft.Icons.BROKEN_IMAGE, size=40, color=ft.Colors.OUTLINE),
            alignment=ft.alignment.Alignment.CENTER,
        )

    badges = []
    if is_blurry:
        badges.append(
            ft.Container(
                content=ft.Text("Blurry", size=9, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.ERROR,
                border_radius=4,
                padding=ft.padding.symmetric(horizontal=4, vertical=2),
            )
        )
    if has_gps == 0:
        badges.append(
            ft.Container(
                content=ft.Text("No GPS", size=9, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.AMBER,
                border_radius=4,
                padding=ft.padding.symmetric(horizontal=4, vertical=2),
            )
        )
    if is_facing_north == 0:
        badges.append(
            ft.Container(
                content=ft.Text("Not North", size=9, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.ORANGE,
                border_radius=4,
                padding=ft.padding.symmetric(horizontal=4, vertical=2),
            )
        )

    thumb_stack = ft.Stack(
        controls=[
            thumb,
            ft.Container(
                content=ft.Checkbox(
                    value=selected,
                    on_change=lambda e, m=member: on_select(m, e.control.value),
                ),
                alignment=ft.alignment.Alignment.TOP_LEFT,
                padding=4,
            ),
            ft.Container(
                content=ft.Row(badges, spacing=2),
                alignment=ft.alignment.Alignment.BOTTOM_LEFT,
                padding=4,
            ),
        ],
    )

    if on_preview:
        thumb_stack = ft.GestureDetector(
            content=thumb_stack,
            on_tap=lambda _, p=path: on_preview(p),
        )

    meta_rows = [
        ft.Text(
            name,
            size=11,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            weight=ft.FontWeight.W_500,
        ),
        ft.Text(size_str, size=10, color=ft.Colors.OUTLINE),
    ]
    if dim_str:
        meta_rows.append(ft.Text(dim_str, size=10, color=ft.Colors.OUTLINE))
    if is_blurry and blur_score is not None:
        meta_rows.append(
            ft.Text(f"Score: {blur_score:.1f}", size=10, color=ft.Colors.ERROR)
        )
    if has_gps == 0:
        meta_rows.append(ft.Text("EXIF GPS missing", size=10, color=ft.Colors.AMBER))
    elif gps_lat is not None and gps_lon is not None:
        meta_rows.append(
            ft.Text(f"GPS: {gps_lat:.6f}, {gps_lon:.6f}", size=10, color=ft.Colors.OUTLINE)
        )
    if gps_heading is not None:
        ref = f" {gps_heading_ref}" if gps_heading_ref else ""
        color = ft.Colors.GREEN if is_facing_north == 1 else ft.Colors.ORANGE
        meta_rows.append(ft.Text(f"Heading: {gps_heading:.1f}°{ref}", size=10, color=color))

    return ft.Container(
        width=card_width,
        border_radius=8,
        border=ft.border.all(2, ft.Colors.PRIMARY if selected else ft.Colors.OUTLINE_VARIANT),
        bgcolor=ft.Colors.SURFACE,
        content=ft.Column(
            spacing=0,
            controls=[
                thumb_stack,
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=6, vertical=4),
                    content=ft.Column(spacing=2, controls=meta_rows),
                ),
            ],
        ),
    )
