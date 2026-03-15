"""Hotkey management dialog for Flet UI."""
import flet as ft
import keyboard


def show_hotkey_dialog(
    page: ft.Page,
    paths: list[str],
    hotkey_bindings: dict,
    hotkey_actions: dict,
    on_save: callable,
) -> None:
    """
    Show dialog for managing hotkeys.

    Args:
        page: Flet page instance
        paths: List of available paths for binding
        hotkey_bindings: Current hotkey bindings dict
        hotkey_actions: Dict of action callbacks
        on_save: Callback to save bindings (receives updated hotkey_bindings)
    """

    # State for recording
    recording = False
    recorded_combo = ""

    # UI elements
    action_dropdown = ft.Dropdown(
        label="Action",
        options=[
            ft.dropdown.Option("start", "Start Auto-Change (Path)"),
            ft.dropdown.Option("stop", "Stop Auto-Change"),
            ft.dropdown.Option("change", "Change Wallpaper"),
            ft.dropdown.Option("show", "Show UI"),
        ],
        value="start",
        width=300,
    )

    path_dropdown = ft.Dropdown(
        label="Path (for Start action)",
        options=[ft.dropdown.Option(p, p) for p in paths],
        value=paths[0] if paths else None,
        width=300,
        visible=True,
    )

    hotkey_field = ft.TextField(
        label="Hotkey Combination",
        value="",
        read_only=True,
        width=300,
    )

    record_button = ft.ElevatedButton(
        content=ft.Text("Record Hotkey"),
        icon=ft.Icons.KEYBOARD_OUTLINED,
    )

    hotkeys_list = ft.ListView(
        controls=[],
        height=200,
        spacing=4,
    )

    def update_path_visibility(e):
        """Show/hide path dropdown based on action."""
        path_dropdown.visible = action_dropdown.value == "start"
        page.update()

    action_dropdown.on_change = update_path_visibility

    def refresh_hotkeys_list():
        """Refresh the list of configured hotkeys."""
        hotkeys_list.controls.clear()

        # Start hotkeys
        for combo, path in hotkey_bindings.get("start", {}).items():
            folder_name = path.split("/")[-1] or path.split("\\")[-1]
            hotkeys_list.controls.append(
                ft.ListTile(
                    title=ft.Text(f"[START: {folder_name}] → {combo}"),
                    trailing=ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.ERROR,
                        on_click=lambda e, c=combo: remove_hotkey("start", c),
                    ),
                )
            )

        # Other hotkeys
        for action_type in ["stop", "change", "show"]:
            for combo in hotkey_bindings.get(action_type, []):
                label = action_type.upper()
                hotkeys_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(f"[{label}] → {combo}"),
                        trailing=ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.ERROR,
                            on_click=lambda e, t=action_type, c=combo: remove_hotkey(t, c),
                        ),
                    )
                )

        page.update()

    def remove_hotkey(action_type: str, combo: str):
        """Remove a hotkey binding."""
        try:
            keyboard.remove_hotkey(combo)
        except:
            pass

        if action_type == "start":
            if combo in hotkey_bindings["start"]:
                del hotkey_bindings["start"][combo]
        else:
            if combo in hotkey_bindings.get(action_type, []):
                hotkey_bindings[action_type].remove(combo)

        on_save(hotkey_bindings)
        refresh_hotkeys_list()

        page.show_dialog(
            ft.SnackBar(
                ft.Text(f"Removed hotkey: {combo}"),
                bgcolor=ft.Colors.BLUE,
            )
        )

    def start_recording(e):
        """Start recording hotkey."""
        nonlocal recording, recorded_combo
        recording = True
        recorded_combo = ""
        hotkey_field.value = "Press keys..."
        record_button.disabled = True
        page.update()

        keys_pressed = set()

        def on_key_event(event):
            nonlocal recording, recorded_combo

            if not recording:
                return

            if event.event_type == 'down':
                keys_pressed.add(event.name)
            elif event.event_type == 'up':
                if keys_pressed:
                    # Format combo
                    ordered = sorted(
                        keys_pressed,
                        key=lambda k: (k not in ['ctrl', 'shift', 'alt'], k)
                    )
                    combo = '+'.join(ordered)

                    recorded_combo = combo
                    hotkey_field.value = combo
                    recording = False
                    record_button.disabled = False

                    keyboard.unhook_all()
                    page.update()

        keyboard.hook(on_key_event)

    record_button.on_click = start_recording

    def save_hotkey(e):
        """Save the recorded hotkey."""
        if not recorded_combo:
            page.show_dialog(
                ft.SnackBar(
                    ft.Text("Please record a hotkey first"),
                    bgcolor=ft.Colors.ERROR,
                )
            )
            return

        action_type = action_dropdown.value

        # Remove from all existing bindings
        for section in ["start", "stop", "change", "show"]:
            try:
                keyboard.remove_hotkey(recorded_combo)
            except:
                pass

            if section == "start":
                if recorded_combo in hotkey_bindings.get(section, {}):
                    del hotkey_bindings["start"][recorded_combo]
            else:
                if recorded_combo in hotkey_bindings.get(section, []):
                    hotkey_bindings[section].remove(recorded_combo)

        # Add new binding
        try:
            if action_type == "start":
                if not path_dropdown.value:
                    page.show_dialog(
                        ft.SnackBar(
                            ft.Text("Please select a path"),
                            bgcolor=ft.Colors.ERROR,
                        )
                    )
                    return

                keyboard.add_hotkey(
                    recorded_combo,
                    lambda c=recorded_combo: hotkey_actions["start"](c)
                )
                hotkey_bindings["start"][recorded_combo] = path_dropdown.value
            else:
                keyboard.add_hotkey(recorded_combo, hotkey_actions[action_type])
                if action_type not in hotkey_bindings:
                    hotkey_bindings[action_type] = []
                if recorded_combo not in hotkey_bindings[action_type]:
                    hotkey_bindings[action_type].append(recorded_combo)

            on_save(hotkey_bindings)
            refresh_hotkeys_list()

            # Clear inputs
            hotkey_field.value = ""

            page.show_dialog(
                ft.SnackBar(
                    ft.Text(f"Hotkey bound: {recorded_combo}"),
                    bgcolor=ft.Colors.GREEN,
                )
            )

        except Exception as ex:
            page.show_dialog(
                ft.SnackBar(
                    ft.Text(f"Failed to bind hotkey: {str(ex)}"),
                    bgcolor=ft.Colors.ERROR,
                )
            )

    # Dialog
    dialog = ft.AlertDialog(
        title=ft.Text("Manage Hotkeys"),
        content=ft.Container(
            content=ft.Column(
                [
                    action_dropdown,
                    path_dropdown,
                    hotkey_field,
                    record_button,
                    ft.ElevatedButton(
                        content=ft.Text("Save Hotkey"),
                        icon=ft.Icons.SAVE,
                        on_click=save_hotkey,
                    ),
                    ft.Divider(),
                    ft.Text("Current Hotkeys", size=14, weight=ft.FontWeight.W_600),
                    hotkeys_list,
                ],
                spacing=16,
                width=400,
            ),
            padding=20,
        ),
        actions=[
            ft.TextButton(content=ft.Text("Close"), on_click=lambda e: close_dialog()),
        ],
    )

    def close_dialog():
        dialog.open = False
        page.update()

    # Show dialog
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    refresh_hotkeys_list()
    dialog.open = True
    page.update()
