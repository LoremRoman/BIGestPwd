import tkinter as tk
import os
import json

SETTINGS_FILE = os.path.join(os.getcwd(), "data", "settings.json")


class ClipboardManager:
    def __init__(self, root):
        self.root = root
        self.security_timer = None
        self.timeout_seconds = 60

        self.root.bind_all("<Control-c>", self._on_manual_copy, add="+")
        self.root.bind_all("<Control-Insert>", self._on_manual_copy, add="+")

    def _should_auto_clear(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    settings = json.load(f)
                    return settings.get("clean_clipboard", True)
        except:
            pass
        return True

    def copy_to_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

            if self._should_auto_clear():
                self._start_timer()

            return True
        except Exception as e:
            print(f"Error copiando al portapapeles: {e}")
            return False

    def _on_manual_copy(self, event):
        if self._should_auto_clear():
            self.root.after(100, self._start_timer)

    def _start_timer(self):
        if self.security_timer:
            self.root.after_cancel(self.security_timer)

        self.security_timer = self.root.after(
            self.timeout_seconds * 1000, self._clear_clipboard_action
        )

    def _clear_clipboard_action(self):
        try:
            if not self._should_auto_clear():
                return

            self.root.clipboard_clear()
            self.root.clipboard_append("")
            self.root.update()
        except Exception as e:
            print(f"Error al limpiar clipboard: {e}")
