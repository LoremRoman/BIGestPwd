import tkinter as tk
import sys
import os
import ctypes
from datetime import datetime
import re

try:
    import win32api
    import win32con
except ImportError:
    pass

from modules.components.widgets import ModernWidgets


class WindowHelper:
    @staticmethod
    def center_window(window, width, height):
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        if y < 0:
            y = 50
        window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def show_custom_message(parent, title, message, is_error=False):
        widgets = ModernWidgets()
        msg_window = tk.Toplevel(parent)
        msg_window.title(title)
        msg_window.configure(bg=widgets.bg_color)
        msg_window.minsize(380, 200)
        msg_window.resizable(False, False)

        if parent:
            msg_window.transient(parent)
            msg_window.grab_set()
        else:
            msg_window.attributes("-topmost", True)

        main_frame = tk.Frame(msg_window, bg=widgets.bg_color, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        icon = "❌" if is_error else "✅"
        icon_color = widgets.danger_color if is_error else widgets.success_color
        btn_color = widgets.danger_color if is_error else widgets.accent_color

        tk.Label(
            main_frame,
            text=icon,
            font=("Segoe UI", 32),
            bg=widgets.bg_color,
            fg=icon_color,
        ).pack(pady=(10, 15))
        tk.Label(
            main_frame,
            text=message,
            font=("Segoe UI", 11),
            bg=widgets.bg_color,
            fg="white",
            wraplength=340,
            justify="center",
        ).pack(pady=(0, 20))

        widgets.create_modern_button(
            main_frame, "Aceptar", msg_window.destroy, btn_color, width=15
        ).pack(pady=10)

        msg_window.update_idletasks()
        width = msg_window.winfo_reqwidth()
        height = msg_window.winfo_reqheight()
        WindowHelper.center_window(msg_window, width, height)
        msg_window.focus_force()
        return msg_window

    @staticmethod
    def manage_windows_startup(enable=True):
        app_name = "BIGestPwd"
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                win32con.KEY_ALL_ACCESS,
            )

            if enable:
                if getattr(sys, "frozen", False):
                    app_path = f'"{sys.executable}"'
                else:
                    python_exe = sys.executable.replace("python.exe", "pythonw.exe")
                    script_path = os.path.abspath(sys.argv[0])
                    app_path = f'"{python_exe}" "{script_path}"'

                win32api.RegSetValueEx(key, app_name, 0, win32con.REG_SZ, app_path)
            else:
                try:
                    win32api.RegDeleteValue(key, app_name)
                except FileNotFoundError:
                    pass

            win32api.RegCloseKey(key)
            return True
        except Exception as e:
            print(f"Error gestionando inicio de Windows: {e}")
            return False

    @staticmethod
    def set_display_affinity(window, enable=True):
        try:
            WDA_NONE = 0x00000000
            WDA_MONITOR = 0x00000001
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            if not hwnd:
                hwnd = window.winfo_id()

            value = WDA_MONITOR if enable else WDA_NONE
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, value)
            return True
        except Exception as e:
            print(f"Error estableciendo afinidad de pantalla: {e}")
            return False


class PasswordHealth:
    @staticmethod
    def assess_strength(password):
        if not password:
            return 0, "Vacía", "#6b7280", "⚪"

        length = len(password)
        score = 0

        if length >= 20:
            score += 3
        elif length >= 16:
            score += 2
        elif length >= 12:
            score += 1

        has_lower = bool(re.search(r"[a-z]", password))
        has_upper = bool(re.search(r"[A-Z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

        complexity_count = sum([has_lower, has_upper, has_digit, has_special])
        score += complexity_count

        if score >= 6:
            return score, "Excelente", "#3b82f6", "🔵"
        elif score >= 5:
            return score, "Segura", "#10b981", "🟢"
        elif score >= 3:
            return score, "Moderada", "#f59e0b", "🟡"
        else:
            return score, "Débil", "#ef4444", "🔴"

    @staticmethod
    def calculate_status(password, date_str):
        msgs = []
        score, strength_text, strength_color, strength_emoji = (
            PasswordHealth.assess_strength(password)
        )

        try:
            if not date_str:
                date_obj = datetime.now()
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

            diff = datetime.now() - date_obj
            months = diff.days // 30
        except:
            months = 0

        msgs.append(f"{strength_emoji} Fortaleza: {strength_text}")

        if score < 3:
            msgs.append("• Contraseña débil o muy corta.")
            msgs.append("• Se recomienda mejorarla usando el generador.")

        if months > 0:
            msgs.append(f"• Antigüedad: {months} mes(es).")

        if months >= 6:
            return (
                "#ef4444",
                "Riesgo: Muy Antigua",
                ["• Esta contraseña tiene más de 6 meses.", "• Cámbiala urgentemente."]
                + msgs,
            )

        if score < 3:
            return (
                "#ef4444",
                "Riesgo: Insegura",
                ["• La contraseña es fácil de vulnerar."] + msgs,
            )

        if months >= 3:
            return (
                "#f59e0b",
                "Advertencia: Antigua",
                ["• Tiene más de 3 meses.", "• Considera renovarla."] + msgs,
            )

        if score < 5:
            return "#f59e0b", "Seguridad Moderada", ["• Podría ser más robusta."] + msgs

        return "#10b981", "Estado Óptimo", ["• Contraseña segura y reciente."]


class Tooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def show_tip(self, text_title, text_lines, x, y):
        self.hide_tip()
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x + 15, y + 10))

        widgets = ModernWidgets()
        main = tk.Frame(tw, bg=widgets.card_bg, relief="solid", bd=1)
        main.pack()

        tk.Label(
            main,
            text=text_title,
            font=("Segoe UI", 10, "bold"),
            bg=widgets.card_bg,
            fg=widgets.accent_color,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(5, 0))

        for line in text_lines:
            tk.Label(
                main,
                text=line,
                font=("Segoe UI", 9),
                bg=widgets.card_bg,
                fg="white",
                justify="left",
            ).pack(anchor="w", padx=10, pady=(0, 2))

        tk.Frame(main, bg=widgets.card_bg, height=5).pack()

    def hide_tip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
