"""Path list item widget with delete button."""
import flet as ft


def create_path_list_item(
    path: str,
    on_delete: callable,
) -> ft.ListTile:
    """
    Create a list item for a wallpaper folder path.

    Args:
        path: Full folder path
        on_delete: Callback when delete button clicked (receives path)

    Returns:
        ft.ListTile with path and delete button
    """
    return ft.ListTile(
        leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, color=ft.Colors.PRIMARY),
        title=ft.Text(path, size=14),
        trailing=ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ft.Colors.ERROR,
            tooltip="Remove folder",
            on_click=lambda e: on_delete(path),
        ),
    )


if __name__ == "__main__":
    def test_main(page: ft.Page):
        def handle_delete(path):
            print(f"Delete: {path}")

        page.add(
            create_path_list_item(
                path="C:\\Users\\User\\Pictures\\Wallpapers",
                on_delete=handle_delete,
            )
        )
    ft.app(target=test_main)
