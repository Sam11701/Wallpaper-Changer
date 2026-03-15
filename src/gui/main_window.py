"""Main window for Wallpaper Changer using Flet framework."""
import flet as ft


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

    # Temporary content
    page.add(
        ft.Text("Wallpaper Changer - Flet UI", size=24, weight=ft.FontWeight.BOLD)
    )


if __name__ == "__main__":
    ft.run(main)
