"""Shared bridge between the main window and the floating image panel."""
import os
import threading


class PanelBridge:
    """
    Thread-safe communication channel.

    Main window calls:  open(folder, monitor_id), close(), update_geometry(x, y, w, h)
    Panel window calls: register(page, grid, title_text)
    """

    def __init__(self):
        self._lock = threading.Lock()

        # Panel Flet controls (set by panel once initialised)
        self._page = None
        self._grid = None
        self._title = None
        self._ready = threading.Event()

        # State
        self.folder = None
        self.visible = False
        self.monitor_id = None

        # Main window geometry
        self.main_x = 100
        self.main_y = 100
        self.main_w = 800
        self.main_h = 640
        self.panel_w = 300

    # ── Called by panel window ─────────────────────────────────────────────

    def register(self, page, grid, title_text):
        with self._lock:
            self._page = page
            self._grid = grid
            self._title = title_text
        self._ready.set()

    # ── Called by main window (from event handler thread) ─────────────────

    def open(self, folder, monitor_id=None):
        """Open panel for folder. Run in a thread so the UI doesn't block."""
        threading.Thread(
            target=self._open_threaded,
            args=(folder, monitor_id),
            daemon=True,
        ).start()

    def close(self):
        self.visible = False
        self.folder = None
        if self._page:
            self._page.run_task(self._async_hide)

    def update_geometry(self, x, y, w, h):
        self.main_x = x
        self.main_y = y
        self.main_w = w
        self.main_h = h
        if self.visible and self._page:
            self._page.run_task(self._async_reposition)

    # ── Internal ───────────────────────────────────────────────────────────

    def _open_threaded(self, folder, monitor_id):
        # Toggle closed if same folder clicked again
        if self.visible and self.folder == folder:
            self.close()
            return

        if not self._ready.wait(timeout=8):
            print("Image panel not ready — open ignored")
            return

        self.folder = folder
        self.monitor_id = monitor_id
        self.visible = True

        self._refresh_content()
        self._page.run_task(self._async_show)

    async def _async_show(self):
        self._page.window.left = self.main_x + self.main_w
        self._page.window.top = self.main_y
        self._page.window.height = self.main_h
        self._page.window.visible = True
        self._page.update()

    async def _async_hide(self):
        self._page.window.visible = False
        self._page.update()

    async def _async_reposition(self):
        self._page.window.left = self.main_x + self.main_w
        self._page.window.top = self.main_y
        self._page.window.height = self.main_h
        self._page.update()

    def _refresh_content(self):
        from src.core import wallpaper
        import flet as ft

        self._title.value = os.path.basename(self.folder)
        self._grid.controls.clear()

        try:
            images = sorted(
                f for f in os.listdir(self.folder)
                if wallpaper.is_valid_image_file(f)
            )
            for img_name in images:
                abs_path = os.path.abspath(os.path.join(self.folder, img_name))
                monitor_id = self.monitor_id

                def on_tap(e, p=abs_path, mid=monitor_id):
                    wallpaper.change_wallpaper(p, monitor_id=mid)

                self._grid.controls.append(
                    ft.GestureDetector(
                        content=ft.Container(
                            content=ft.Image(
                                src=abs_path,
                                fit=ft.ImageFit.COVER,
                                expand=True,
                                gapless_playback=True,
                            ),
                            border_radius=6,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            tooltip=img_name,
                        ),
                        on_tap=on_tap,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    )
                )
        except Exception as e:
            print(f"Panel image load error: {e}")


# Module-level singleton shared by both windows
bridge = PanelBridge()
