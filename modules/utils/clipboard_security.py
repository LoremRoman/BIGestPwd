import tkinter as tk
import threading


class ClipboardManager:
    def __init__(self, root):
        self.root = root
        self.security_timer = None
        self.timeout_seconds = 60

    def copy_to_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            if self.security_timer:
                self.root.after_cancel(self.security_timer)
            self.security_timer = self.root.after(
                self.timeout_seconds * 1000, self._clear_clipboard_action
            )

            return True
        except Exception as e:
            print(f"Error copiando al portapapeles: {e}")
            return False

    def _clear_clipboard_action(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("¡Ups!")
            self.root.update()
            print("🔒 [SEGURIDAD] Portapapeles limpiado automáticamente (Sobrescrito).")
        except Exception as e:
            print(f"Error al limpiar clipboard: {e}")
