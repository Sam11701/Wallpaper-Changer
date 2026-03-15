"""Main window for Wallpaper Changer using Flet framework."""
import os
import json
import threading
import keyboard
import flet as ft
from src.core import wallpaper
from src.config import DATA_FILE, HOTKEY_FILE
from src.gui.widgets.path_list_item import create_path_list_item
from src.gui.hotkey_dialog import show_hotkey_dialog


def main(page: ft.Page):
    """Main entry point for Flet app."""
    # State
    current_paths = []
    current_source = "No folder selected"
    timer_active = False
    timer_interval = 60  # Default 60 seconds
    active_timer = None
    hotkey_bindings = {"start": {}, "stop": [], "change": [], "show": []}

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

    # Status Cards Row (with refs for updates)
    source_card_value = ft.Ref[ft.Text]()
    timer_card_value = ft.Ref[ft.Text]()
    hotkeys_card_value = ft.Ref[ft.Text]()

    def create_updateable_status_card(icon: str, title: str, value: str, value_ref: ft.Ref):
        """Create status card with updateable value."""
        value_text = ft.Text(
            value,
            size=16,
            weight=ft.FontWeight.W_600,
            color="#2D3748",
            ref=value_ref,
        )
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(name=icon, size=32, color=ft.colors.PRIMARY),
                        ft.Text(
                            title,
                            size=12,
                            weight=ft.FontWeight.W_400,
                            color="#718096",
                        ),
                        value_text,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=24,
                alignment=ft.alignment.center,
            ),
            elevation=2,
        )

    status_cards = ft.ResponsiveRow(
        [
            ft.Container(
                content=create_updateable_status_card(
                    icon=ft.icons.FOLDER,
                    title="Current Source",
                    value=current_source,
                    value_ref=source_card_value,
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=create_updateable_status_card(
                    icon=ft.icons.TIMER,
                    title="Timer",
                    value="Stopped",
                    value_ref=timer_card_value,
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=create_updateable_status_card(
                    icon=ft.icons.KEYBOARD,
                    title="Hotkeys",
                    value="0 shortcuts active",
                    value_ref=hotkeys_card_value,
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
        ],
        spacing=16,
    )

    # Quick Actions Section
    def update_timer_ui(is_active: bool, countdown: str = "Stopped"):
        """Update timer button and status card."""
        nonlocal timer_button

        if is_active:
            timer_button.text = "Stop Timer"
            timer_button.icon = ft.icons.STOP
            timer_button.style.bgcolor = {"": "#FF6B6B"}  # Coral
            timer_card_value.current.value = countdown
        else:
            timer_button.text = "Start Timer"
            timer_button.icon = ft.icons.PLAY_ARROW
            timer_button.style.bgcolor = {"": "#718096"}  # Gray
            timer_card_value.current.value = "Stopped"

        page.update()

    def timer_loop():
        """Timer loop that runs in background."""
        nonlocal current_source

        if timer_active and current_paths:
            # Pick and change wallpaper
            selected_path = current_paths[0]
            try:
                if wallpaper.pick_and_change(selected_path):
                    current_source = os.path.basename(selected_path)
                    source_card_value.current.value = current_source
                    page.update()
            except Exception as e:
                print(f"Timer wallpaper change failed: {e}")

            # Schedule next iteration
            if timer_active:
                active_timer_ref = threading.Timer(timer_interval, timer_loop)
                active_timer_ref.start()

    def handle_timer_toggle(e):
        """Handle timer start/stop."""
        nonlocal timer_active, active_timer, timer_interval

        if not current_paths:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("No folders configured. Add a folder first."),
                bgcolor=ft.colors.ERROR,
            )
            page.snack_bar.open = True
            page.update()
            return

        timer_active = not timer_active

        if timer_active:
            # Calculate interval from inputs
            try:
                minutes = int(minutes_field.value) if minutes_field.value else 0
                seconds = int(seconds_field.value) if seconds_field.value else 0
                timer_interval = (minutes * 60) + seconds

                if timer_interval < 1:
                    timer_interval = 60
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Invalid interval, using default (60s)"),
                        bgcolor=ft.colors.ORANGE,
                    )
                    page.snack_bar.open = True
                elif timer_interval > (24 * 3600):
                    timer_interval = 60
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Interval too long, using default (60s)"),
                        bgcolor=ft.colors.ORANGE,
                    )
                    page.snack_bar.open = True
            except ValueError:
                timer_interval = 60
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Invalid input, using default (60s)"),
                    bgcolor=ft.colors.ORANGE,
                )
                page.snack_bar.open = True

            # Start timer
            update_timer_ui(is_active=True, countdown=f"{timer_interval}s")
            if not page.snack_bar or not page.snack_bar.open:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Auto-change started ({timer_interval}s interval)"),
                    bgcolor=ft.colors.BLUE,
                )
                page.snack_bar.open = True

            # Start timer loop
            active_timer = threading.Timer(timer_interval, timer_loop)
            active_timer.start()
        else:
            # Stop timer
            if active_timer:
                active_timer.cancel()
                active_timer = None

            update_timer_ui(is_active=False)
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Auto-change stopped"),
                bgcolor=ft.colors.BLUE,
            )
            page.snack_bar.open = True

        page.update()

    def load_paths():
        """Load paths from data.txt."""
        nonlocal current_paths
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                current_paths = [line.strip() for line in f if line.strip()]

    def load_hotkey_bindings():
        """Load hotkey bindings from file."""
        nonlocal hotkey_bindings
        default = {"start": {}, "stop": [], "change": [], "show": []}

        if os.path.exists(HOTKEY_FILE):
            try:
                with open(HOTKEY_FILE, "r") as f:
                    data = json.load(f)
                    for key in default:
                        if key not in data:
                            data[key] = default[key]
                    hotkey_bindings = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading hotkeys: {e}")
                hotkey_bindings = default
        else:
            hotkey_bindings = default

    def save_hotkey_bindings(bindings: dict):
        """Save hotkey bindings to file."""
        nonlocal hotkey_bindings
        hotkey_bindings = bindings

        try:
            with open(HOTKEY_FILE, "w") as f:
                json.dump(hotkey_bindings, f, indent=4)

            # Update hotkeys card
            count = len(hotkey_bindings.get("start", {})) + \
                    len(hotkey_bindings.get("stop", [])) + \
                    len(hotkey_bindings.get("change", [])) + \
                    len(hotkey_bindings.get("show", []))
            hotkeys_card_value.current.value = f"{count} shortcuts active"
            page.update()
        except IOError as e:
            print(f"Error saving hotkeys: {e}")

    def switch_path_by_hotkey(key_combo: str):
        """Handle start hotkey press."""
        nonlocal current_source
        path = hotkey_bindings["start"].get(key_combo)
        if path and os.path.isdir(path):
            if not timer_active:
                # Start timer for this path
                current_paths.insert(0, path)  # Prioritize this path
                handle_timer_toggle(None)

    def stop_auto_change_hotkey():
        """Handle stop hotkey press."""
        if timer_active:
            handle_timer_toggle(None)

    def change_wallpaper_hotkey():
        """Handle change wallpaper hotkey press."""
        if current_paths:
            handle_change_wallpaper(None)

    def show_ui_hotkey():
        """Handle show UI hotkey press."""
        page.window_to_front = True
        page.update()

    hotkey_actions = {
        "start": switch_path_by_hotkey,
        "stop": stop_auto_change_hotkey,
        "change": change_wallpaper_hotkey,
        "show": show_ui_hotkey,
    }

    def handle_change_wallpaper(e):
        """Handle manual wallpaper change."""
        nonlocal current_source

        if not current_paths:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("No folders configured. Add a folder first."),
                bgcolor=ft.colors.ERROR,
            )
            page.snack_bar.open = True
            page.update()
            return

        # Use first path for now (later: let user select)
        selected_path = current_paths[0]

        # Disable button, show loading
        change_now_button.disabled = True
        change_now_button.text = "Changing..."
        page.update()

        try:
            if wallpaper.pick_and_change(selected_path):
                current_source = os.path.basename(selected_path)
                source_card_value.current.value = current_source
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Wallpaper changed successfully"),
                    bgcolor=ft.colors.GREEN,
                )
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to change wallpaper"),
                    bgcolor=ft.colors.ERROR,
                )
        except ValueError as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(str(e)),
                bgcolor=ft.colors.ERROR,
            )
        finally:
            change_now_button.disabled = False
            change_now_button.text = "Change Wallpaper Now"
            page.snack_bar.open = True
            page.update()

    # Load paths on startup
    load_paths()

    # Load and register hotkeys
    load_hotkey_bindings()

    # Register hotkeys
    for combo_str, path in hotkey_bindings.get("start", {}).items():
        try:
            keyboard.add_hotkey(
                combo_str,
                lambda c=combo_str: switch_path_by_hotkey(c)
            )
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    for combo_str in hotkey_bindings.get("stop", []):
        try:
            keyboard.add_hotkey(combo_str, stop_auto_change_hotkey)
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    for combo_str in hotkey_bindings.get("change", []):
        try:
            keyboard.add_hotkey(combo_str, change_wallpaper_hotkey)
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    for combo_str in hotkey_bindings.get("show", []):
        try:
            keyboard.add_hotkey(combo_str, show_ui_hotkey)
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    # Update hotkeys card
    count = len(hotkey_bindings.get("start", {})) + \
            len(hotkey_bindings.get("stop", [])) + \
            len(hotkey_bindings.get("change", [])) + \
            len(hotkey_bindings.get("show", []))
    hotkeys_card_value.current.value = f"{count} shortcuts active"

    change_now_button = ft.FilledButton(
        text="Change Wallpaper Now",
        icon=ft.icons.WALLPAPER,
        style=ft.ButtonStyle(
            bgcolor=ft.colors.PRIMARY,
            color=ft.colors.ON_PRIMARY,
        ),
        height=50,
        on_click=handle_change_wallpaper,
    )

    timer_button = ft.FilledButton(
        text="Start Timer",
        icon=ft.icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            bgcolor={"": "#718096"},  # Gray when stopped
            color=ft.colors.WHITE,
        ),
        height=50,
        on_click=handle_timer_toggle,
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

    # Timer Configuration
    minutes_field = ft.TextField(
        label="Minutes",
        value="1",
        width=80,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    seconds_field = ft.TextField(
        label="Seconds",
        value="0",
        width=80,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    timer_config = ft.Container(
        content=ft.Column(
            [
                ft.Text("Timer Interval", size=14, weight=ft.FontWeight.W_600),
                ft.Row(
                    [
                        minutes_field,
                        ft.Text("minutes"),
                        seconds_field,
                        ft.Text("seconds"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
            ],
            spacing=8,
        ),
        padding=16,
        border=ft.border.all(1, "#E2E8F0"),
        border_radius=8,
    )

    # Paths Configuration
    paths_list = ft.Column(spacing=0)

    def refresh_paths_list():
        """Refresh the paths list display."""
        paths_list.controls.clear()
        for path in current_paths:
            paths_list.controls.append(
                create_path_list_item(path=path, on_delete=handle_remove_path)
            )
        page.update()

    def handle_remove_path(path: str):
        """Remove a path from the list."""
        nonlocal current_paths
        if path in current_paths:
            current_paths.remove(path)

            # Save to file
            with open(DATA_FILE, "w") as f:
                f.writelines(line + '\n' for line in current_paths)

            refresh_paths_list()

            page.snack_bar = ft.SnackBar(
                content=ft.Text("Folder removed"),
                bgcolor=ft.colors.BLUE,
            )
            page.snack_bar.open = True
            page.update()

    def on_folder_selected(e: ft.FilePickerResultEvent):
        """Handle folder selection from file picker."""
        nonlocal current_paths
        if e.path:
            selected_path = e.path

            # Validate directory
            if not os.path.isdir(selected_path):
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Invalid directory path"),
                    bgcolor=ft.colors.ERROR,
                )
                page.snack_bar.open = True
                page.update()
                return

            # Check for duplicates
            if selected_path in current_paths:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Folder already in list"),
                    bgcolor=ft.colors.ORANGE,
                )
                page.snack_bar.open = True
                page.update()
                return

            # Add to list
            current_paths.append(selected_path)

            # Save to file
            with open(DATA_FILE, "w") as f:
                f.writelines(line + '\n' for line in current_paths)

            refresh_paths_list()

            page.snack_bar = ft.SnackBar(
                content=ft.Text("Folder added"),
                bgcolor=ft.colors.GREEN,
            )
            page.snack_bar.open = True
            page.update()

    def handle_add_path(e):
        """Show file picker to add folder."""
        folder_picker.get_directory_path()

    # File picker
    folder_picker = ft.FilePicker(on_result=on_folder_selected)
    page.overlay.append(folder_picker)

    paths_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Wallpaper Folders",
                            size=14,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.IconButton(
                            icon=ft.icons.ADD_CIRCLE_OUTLINE,
                            icon_color=ft.colors.PRIMARY,
                            tooltip="Add folder",
                            on_click=handle_add_path,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                paths_list,
            ],
            spacing=8,
        ),
        padding=16,
        border=ft.border.all(1, "#E2E8F0"),
        border_radius=8,
    )

    # Initialize paths list
    refresh_paths_list()

    # Hotkeys Section
    def open_hotkey_dialog(e):
        """Open hotkey management dialog."""
        show_hotkey_dialog(
            page=page,
            paths=current_paths,
            hotkey_bindings=hotkey_bindings,
            hotkey_actions=hotkey_actions,
            on_save=save_hotkey_bindings,
        )

    hotkeys_section = ft.Container(
        content=ft.ListTile(
            leading=ft.Icon(ft.icons.KEYBOARD, color=ft.colors.PRIMARY),
            title=ft.Text("Manage Hotkeys", size=14, weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Configure global keyboard shortcuts"),
            trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
            on_click=open_hotkey_dialog,
        ),
        border=ft.border.all(1, "#E2E8F0"),
        border_radius=8,
    )

    # Main layout
    page.add(
        ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            status_cards,
                            quick_actions,
                            timer_config,
                            paths_section,
                            hotkeys_section,
                        ],
                        spacing=24,
                    ),
                    padding=24,
                )
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
