import tkinter as tk
import win32event
import win32api
import winerror
import sys
import os
import json
from tkinter import ttk

from modules.auth_system_new import LoginSystemNew as LoginSystem
from modules.encryption import db_manager
from modules.main_app import MainApplication
from modules.components.virtual_keyboard import VirtualKeyboard
from modules.utils.helpers import WindowHelper
from modules.auth.multi_factor import MultiFactorAuth
from modules.components.widgets import ModernWidgets
from modules.config import APP_VERSION as CURRENT_VERSION
from modules.release_notes import RELEASE_NOTES

from modules.utils.afk_monitor import AFKMonitor
from modules.utils.system_tray import AppTrayIcon
from modules.utils.animator import WindowAnimator

MUTEX_NAME = "BIGestPwd_SingleInstanceMutex"
SETTINGS_FILE = os.path.join(os.getcwd(), "data", "settings.json")


class BIGestPwdApp:
    def __init__(self):
        self.root = tk.Tk()
        self.master_password = ""
        self.widgets = ModernWidgets()
        self.virtual_kb = VirtualKeyboard(self.root)
        self.mfa = MultiFactorAuth()

        self.settings = {
            "start_with_windows": False,
            "minimize_to_tray": True,
            "afk_lock": True,
            "clean_clipboard": True,
            "privacy_mode": False,
        }
        self.load_settings()

        self.afk_monitor = None
        if self.settings["afk_lock"]:
            self.afk_monitor = AFKMonitor(
                timeout_minutes=15, on_afk_callback=self.on_afk_detected
            )
            self.afk_monitor.start()

        self.tray_icon = None
        self.is_closing = False

        self.setup_system_tray()
        self.setup_app_window()

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                    self.settings.update(saved)
        except:
            pass

    def setup_system_tray(self):
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            self.tray_icon = AppTrayIcon(
                f"BIGestPwd {CURRENT_VERSION}",
                icon_path,
                on_show_callback=self.show_window_from_tray,
                on_exit_callback=self.quit_app_completely,
            )
            self.tray_icon.run()
        except Exception as e:
            print(f"Error iniciando Tray: {e}")

    def setup_app_window(self):
        self.root.title(f"BIGestPwd {CURRENT_VERSION}")
        self.root.configure(bg=self.widgets.bg_color)
        self.root.geometry("550x700")
        self.root.minsize(500, 600)

        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            pass

        if self.settings["minimize_to_tray"]:
            self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        else:
            self.root.protocol("WM_DELETE_WINDOW", self.quit_app_completely)

        if self.settings["privacy_mode"]:
            WindowHelper.set_display_affinity(self.root, True)

        if not db_manager.is_master_configured():
            self.root.deiconify()
            WindowHelper.center_window(self.root, 550, 700)
            self.show_first_time_setup()
        else:
            self.start_in_background()

    def start_in_background(self):
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.show_notification(
                "BIGestPwd está activo",
                "La aplicación se está ejecutando en segundo plano. Haz doble clic en el icono para abrir.",
            )

    def show_window_from_tray(self):
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        if self.root.state() == "normal":
            self.root.focus_force()
            return

        WindowAnimator.fade_in(self.root)
        self.root.focus_force()

        if not self.master_password:
            self.check_login_status()

    def minimize_to_tray(self):
        self.load_settings()
        if self.settings["minimize_to_tray"]:
            WindowHelper.set_display_affinity(self.root, False)
            WindowAnimator.fade_out(self.root)
        else:
            self.quit_app_completely()

    def quit_app_completely(self):
        self.is_closing = True
        if self.afk_monitor:
            self.afk_monitor.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        try:
            self.root.destroy()
        except:
            pass
        os._exit(0)

    def check_login_status(self):
        mfa_status = self.mfa.get_mfa_status()
        configured_methods = sum(
            [1 for m in mfa_status.values() if m.get("configured", False)]
        )

        if configured_methods < 2:
            self.show_mfa_setup()
        else:
            self.show_login()

    def on_afk_detected(self):
        self.load_settings()
        if not self.settings["afk_lock"]:
            return

        if self.master_password and not self.is_closing:
            self.master_password = ""
            self.root.after(0, self._force_logout_afk)

    def _force_logout_afk(self):
        self.clear_window()
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.show_notification(
                "Sesión Cerrada", "Se cerró la sesión por inactividad (15 min)."
            )

    def show_first_time_setup(self):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg=self.widgets.bg_color)
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        center_container = tk.Frame(main_frame, bg=self.widgets.bg_color)
        center_container.pack(expand=True, fill="both")

        icon_img = self.widgets.get_icon_image(size=(100, 100))
        if icon_img:
            self.widgets.image_cache["welcome_icon"] = icon_img
            tk.Label(center_container, image=icon_img, bg=self.widgets.bg_color).pack(
                pady=(0, 10)
            )
        else:
            tk.Label(
                center_container,
                text="🔐",
                font=("Segoe UI", 48),
                bg=self.widgets.bg_color,
                fg=self.widgets.accent_color,
            ).pack(pady=(0, 10))

        tk.Label(
            center_container,
            text="Bienvenido a BIGestPwd",
            font=("Segoe UI", 24, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack()
        tk.Label(
            center_container,
            text="Tu fortaleza digital personal",
            font=("Segoe UI", 12),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
        ).pack(pady=(5, 30))

        card = tk.Frame(center_container, bg=self.widgets.card_bg, padx=30, pady=30)
        card.pack(fill="x")
        tk.Label(
            card,
            text="Configurar Llave Maestra",
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack(pady=(0, 20))

        tk.Label(
            card,
            text="Nueva Contraseña Maestra:",
            font=("Segoe UI", 10, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
            anchor="w",
        ).pack(fill="x", pady=(0, 5))
        self.master_entry = self.widgets.create_styled_entry(card, show="•")
        self.master_entry.pack(fill="x", ipady=6, pady=(0, 15))
        self.master_entry.focus()

        tk.Label(
            card,
            text="Confirmar Contraseña:",
            font=("Segoe UI", 10, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
            anchor="w",
        ).pack(fill="x", pady=(0, 5))
        self.confirm_entry = self.widgets.create_styled_entry(card, show="•")
        self.confirm_entry.pack(fill="x", ipady=6, pady=(0, 20))

        def setup_master():
            master_pwd = self.master_entry.get()
            confirm_pwd = self.confirm_entry.get()

            if len(master_pwd) < 8:
                WindowHelper.show_custom_message(
                    self.root,
                    "Seguridad Débil",
                    "Mínimo 8 caracteres requeridos",
                    is_error=True,
                )
                return
            if master_pwd != confirm_pwd:
                WindowHelper.show_custom_message(
                    self.root, "Error", "Las contraseñas no coinciden", is_error=True
                )
                return

            if db_manager.configure_master_password(master_pwd):
                self.master_password = master_pwd
                self.show_mfa_setup()
            else:
                WindowHelper.show_custom_message(
                    self.root,
                    "Error fatal",
                    "No se pudo guardar la configuración",
                    is_error=True,
                )

        self.widgets.create_modern_button(
            card,
            "🚀 Comenzar Configuración",
            setup_master,
            self.widgets.success_color,
            width=25,
        ).pack(fill="x", pady=5)
        self.widgets.create_modern_button(
            card,
            "⌨️ Teclado Virtual",
            lambda: self.virtual_kb.create_keyboard(self.master_entry),
            self.widgets.accent_color,
        ).pack(fill="x", pady=5)
        self.master_entry.bind("<Return>", lambda e: setup_master())
        self.confirm_entry.bind("<Return>", lambda e: setup_master())

    def show_mfa_setup(self):
        self.clear_window()
        from modules.components.mfa_setup import MFASetupWizard

        self.root.geometry("900x700")
        WindowHelper.center_window(self.root, 900, 700)
        self.mfa_wizard = MFASetupWizard(
            self.root,
            self.master_password,
            on_complete_callback=self.on_mfa_setup_complete,
        )

    def on_mfa_setup_complete(self):
        if self.master_password:
            self.show_main_interface()
        else:
            self.show_login()

    def show_login(self):
        self.clear_window()
        self.root.geometry("500x650")
        WindowHelper.center_window(self.root, 500, 650)
        self.login_system = LoginSystem(self.root)
        self.login_system.create_login_interface(self.on_login_success)

    def on_login_success(self, master_password):
        self.master_password = master_password
        self.show_main_interface()

    def on_logout(self):
        self.master_password = ""
        self.show_login()

    def show_main_interface(self):
        self.clear_window()
        width = 1100
        height = 750
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2 - 30
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.state("normal")
        if self.settings["privacy_mode"]:
            WindowHelper.set_display_affinity(self.root, True)

        self.main_app = MainApplication(
            self.root, self.master_password, on_logout_callback=self.on_logout
        )
        self.check_version_and_show_news()

    def check_version_and_show_news(self):
        version_file = os.path.join(os.getcwd(), "data", "version.json")
        show_modal = False

        try:
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    data = json.load(f)
                    last_version = data.get("version", "0.0")
                    if last_version != CURRENT_VERSION:
                        show_modal = True
            else:
                show_modal = True
        except:
            show_modal = True

        if show_modal:
            self.root.after(500, self.show_whats_new_modal)
            try:
                with open(version_file, "w") as f:
                    json.dump({"version": CURRENT_VERSION}, f)
            except:
                pass

    def show_whats_new_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title(f"¡Novedades v{CURRENT_VERSION}!")
        modal.configure(bg=self.widgets.bg_color)
        modal.geometry("500x620")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        WindowHelper.center_window(modal, 500, 620)

        header = tk.Frame(modal, bg=self.widgets.accent_color, height=80)
        header.pack(fill="x")
        tk.Label(
            header,
            text="✨ Novedades",
            font=("Segoe UI", 20, "bold"),
            bg=self.widgets.accent_color,
            fg="white",
        ).place(x=20, y=10)
        tk.Label(
            header,
            text=f"Versión {CURRENT_VERSION} - BIGestPwd",
            font=("Segoe UI", 10),
            bg=self.widgets.accent_color,
            fg="#e5e7eb",
        ).place(x=20, y=50)

        content = tk.Frame(modal, bg=self.widgets.bg_color, padx=30, pady=20)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text="¡Hemos mejorado tu seguridad!",
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(anchor="w", pady=(0, 15))

        notes = RELEASE_NOTES.get(CURRENT_VERSION, [])

        if not notes:
            tk.Label(
                content,
                text="No hay notas disponibles para esta versión.",
                font=("Segoe UI", 10),
                bg=self.widgets.bg_color,
                fg="white",
            ).pack()
        else:
            for item in notes:
                f = tk.Frame(content, bg=self.widgets.bg_color)
                f.pack(fill="x", pady=10)

                icon_frame = tk.Frame(f, bg=self.widgets.bg_color, width=70)
                icon_frame.pack(side="left", anchor="n", fill="y")
                icon_frame.pack_propagate(False)

                tk.Label(
                    icon_frame,
                    text=item["emoji"],
                    font=("Segoe UI", 24),
                    bg=self.widgets.bg_color,
                    fg="white",
                ).pack(expand=True)

                text_f = tk.Frame(f, bg=self.widgets.bg_color)
                text_f.pack(side="left", fill="x", expand=True)

                tk.Label(
                    text_f,
                    text=item["title"],
                    font=("Segoe UI", 11, "bold"),
                    bg=self.widgets.bg_color,
                    fg=self.widgets.success_color,
                ).pack(anchor="w")
                tk.Label(
                    text_f,
                    text=item["desc"],
                    font=("Segoe UI", 9),
                    bg=self.widgets.bg_color,
                    fg=self.widgets.text_secondary,
                    wraplength=330,
                    justify="left",
                ).pack(anchor="w")

        footer_text_frame = tk.Frame(modal, bg=self.widgets.bg_color, pady=10)
        footer_text_frame.pack(fill="x", side="bottom")

        tk.Label(
            footer_text_frame,
            text='Si deseas saber los cambios previos de cada versión,\nve a la pestaña "Acerca de" y visita nuestro repositorio!',
            font=("Segoe UI", 9, "italic"),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
            justify="center",
        ).pack(side="bottom", pady=(0, 15))

        self.widgets.create_modern_button(
            footer_text_frame,
            "¡Excelente, Entendido!",
            modal.destroy,
            self.widgets.accent_color,
            width=20,
        ).pack(side="bottom", pady=(5, 5))

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


def check_single_instance():
    try:
        mutex = win32event.CreateMutex(None, 1, MUTEX_NAME)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            return True
        return False
    except:
        return False


if __name__ == "__main__":
    if check_single_instance():
        WindowHelper.show_custom_message(
            None,
            "BIGestPwd Abierto",
            "La aplicación ya se está ejecutando en segundo plano. Por favor, revisa la bandeja del sistema.",
            is_error=False,
        )
        sys.exit(0)

    app = BIGestPwdApp()
    app.root.mainloop()
