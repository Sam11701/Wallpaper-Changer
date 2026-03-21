"""Reusable status card component."""
import flet as ft


def create_status_card(icon: str, title: str, value: str) -> ft.Card:
    """
    Create a status display card.

    Args:
        icon: Icon name from ft.icons (e.g., ft.Icons.FOLDER)
        title: Card title (e.g., "Current Source")
        value: Display value (e.g., "Documents/Wallpapers")

    Returns:
        ft.Card with icon, title, and value
    """
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=32, color=ft.Colors.PRIMARY),
                    ft.Text(
                        title,
                        size=12,
                        weight=ft.FontWeight.W_400,
                        color="#718096",  # Gray
                    ),
                    ft.Text(
                        value,
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color="#2D3748",  # Dark charcoal
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=24,
        ),
        elevation=2,
    )
