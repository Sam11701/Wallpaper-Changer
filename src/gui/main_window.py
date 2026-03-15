"""Main window for Wallpaper Changer using Flet framework."""
import flet as ft
from src.gui.widgets.status_card import create_status_card


def main(page: ft.Page):
    """Main entry point for Flet app."""
    # Window configuration
    page.title = "Wallpaper Changer"
    page.window_width = 800
    page.window_height = 600
    page.window_min_width = 600
    page.window_min_height = 500

    # Theme configuration
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#8B5CF6",  # Soft purple
            secondary="#FF6B6B",  # Warm coral
            surface="#FFFFFF",  # White cards
            on_primary="#FFFFFF",  # White text on purple
            on_surface="#2D3748",  # Dark text on white
        ),
        use_material3=True,
    )
    page.bgcolor = "#FAFAFA"  # Off-white background

    # AppBar
    page.appbar = ft.AppBar(
        title=ft.Text("Wallpaper Changer", weight=ft.FontWeight.W_600),
        center_title=False,
        bgcolor="#8B5CF6",
        color="#FFFFFF",
    )

    # Status Cards Row
    status_cards = ft.ResponsiveRow(
        [
            ft.Container(
                content=create_status_card(
                    icon=ft.icons.FOLDER,
                    title="Current Source",
                    value="No folder selected"
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=create_status_card(
                    icon=ft.icons.TIMER,
                    title="Timer",
                    value="Stopped"
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=create_status_card(
                    icon=ft.icons.KEYBOARD,
                    title="Hotkeys",
                    value="0 shortcuts active"
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
        ],
        spacing=16,
    )

    # Quick Actions Section
    change_now_button = ft.FilledButton(
        text="Change Wallpaper Now",
        icon=ft.icons.WALLPAPER,
        style=ft.ButtonStyle(
            bgcolor=ft.colors.PRIMARY,
            color=ft.colors.ON_PRIMARY,
        ),
        height=50,
    )

    timer_button = ft.FilledButton(
        text="Start Timer",
        icon=ft.icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            bgcolor={"": "#718096"},  # Gray when stopped
            color=ft.colors.WHITE,
        ),
        height=50,
    )

    quick_actions = ft.ResponsiveRow(
        [
            ft.Container(
                content=change_now_button,
                col={"xs": 12, "md": 6},
            ),
            ft.Container(
                content=timer_button,
                col={"xs": 12, "md": 6},
            ),
        ],
        spacing=16,
    )

    # Main layout
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    status_cards,
                    quick_actions,
                ],
                spacing=24,
            ),
            padding=24,
        )
    )


if __name__ == "__main__":
    ft.run(main)
