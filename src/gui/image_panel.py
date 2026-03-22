"""Floating image panel window — runs in a daemon thread."""
import signal as _signal
import flet as ft
from src.gui.panel_bridge import bridge


def panel_main(page: ft.Page):
    page.title = "Image Panel"
    page.window.frameless = True
    page.window.title_bar_hidden = True
    page.window.width = bridge.panel_w
    page.window.height = bridge.main_h
    page.window.left = bridge.main_x + bridge.main_w
    page.window.top = bridge.main_y
    page.window.visible = False
    page.window.min_width = bridge.panel_w
    page.window.max_width = bridge.panel_w
    page.padding = 0
    page.bgcolor = "#FAFAFA"

    title_text = ft.Text(
        "",
        size=13,
        weight=ft.FontWeight.W_600,
        color="#2D3748",
        expand=True,
        overflow=ft.TextOverflow.ELLIPSIS,
        no_wrap=True,
    )

    def on_close(e):
        bridge.close()

    header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED, size=16, color="#FFFFFF"),
                title_text,
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=14,
                    icon_color="#FFFFFF",
                    on_click=on_close,
                    width=32,
                    height=32,
                    style=ft.ButtonStyle(
                        overlay_color={ft.ControlState.HOVERED: "#E55A5A"},
                    ),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor="#FF6B6B",
    )

    image_grid = ft.GridView(
        runs_count=2,
        max_extent=140,
        child_aspect_ratio=1.0,
        spacing=6,
        run_spacing=6,
        expand=True,
        padding=ft.padding.all(10),
    )

    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    content=image_grid,
                    border=ft.border.only(left=ft.BorderSide(1, "#E2E8F0")),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )

    bridge.register(page, image_grid, title_text)


def run_panel():
    """Entry point for the panel daemon thread.

    ft.run() sets up signal handlers internally which only works on the main
    thread.  We suppress that call so the panel can start from a daemon thread.
    """
    _orig = _signal.signal
    _signal.signal = lambda *a, **k: None
    try:
        ft.run(panel_main)
    finally:
        _signal.signal = _orig
