import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image
import os
import sys


class AppTrayIcon:
    def __init__(self, app_name, icon_path, on_show_callback, on_exit_callback):
        self.app_name = app_name
        self.icon_path = icon_path
        self.on_show = on_show_callback
        self.on_exit = on_exit_callback
        self.icon = None
        self.thread = None

    def run(self):
        image = self._load_image()
        menu = Menu(
            MenuItem("Abrir BIGestPwd", self._action_show, default=True),
            MenuItem("Buscar Actualizaciones", self._action_update),
            MenuItem("Salir", self._action_exit),
        )
        self.icon = Icon(self.app_name, image, self.app_name, menu)
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()

    def show_notification(self, title, message):
        if self.icon:
            self.icon.notify(message, title)

    def _load_image(self):
        try:
            if os.path.exists(self.icon_path):
                return Image.open(self.icon_path)
            return Image.new("RGB", (64, 64), color=(79, 70, 229))
        except:
            return Image.new("RGB", (64, 64), color=(79, 70, 229))

    def _action_show(self, icon, item):
        if self.on_show:
            self.on_show()

    def _action_update(self, icon, item):
        if self.on_show:
            self.on_show()

    def _action_exit(self, icon, item):
        self.icon.stop()
        if self.on_exit:
            self.on_exit()
