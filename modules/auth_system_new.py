import tkinter as tk
from tkinter import ttk
from modules.components.virtual_keyboard import VirtualKeyboard
from modules.utils.helpers import WindowHelper
from modules.encryption import db_manager
from modules.auth.multi_factor import MultiFactorAuth
from modules.auth.totp_offline import TOTPOffline
from modules.auth.usb_bypass import USBBypass
from modules.components.widgets import ModernWidgets


class LoginSystemNew:
    def __init__(self, root):
        self.root = root
        self.widgets = ModernWidgets()
        self.virtual_kb = VirtualKeyboard(root)
        self.mfa = MultiFactorAuth()
        self.totp = TOTPOffline()
        self.usb = USBBypass()
        self.master_password = ""

    def create_login_interface(self, on_success_callback):
        self.on_success_callback = on_success_callback

        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("BIGestPwd 2.8.1 - Login Seguro")
        self.root.configure(bg=self.widgets.bg_color)
        self.root.resizable(True, True)

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        user_profile = self.mfa.get_user_profile()
        usb_configured = self.usb.is_configured()
        force_totp = getattr(self, "force_totp_mode", False)

        if usb_configured and not force_totp:
            self.root.geometry("500x650")
            self.create_usb_login_interface(user_profile)
        else:
            self.root.geometry("500x700")
            self.create_totp_login_interface(user_profile)

        WindowHelper.center_window(self.root, 500, 700)

    def create_usb_login_interface(self, user_profile):
        main_frame = tk.Frame(self.root, bg=self.widgets.bg_color)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        center_box = tk.Frame(main_frame, bg=self.widgets.bg_color)
        center_box.pack(expand=True)

        if user_profile:
            tk.Label(
                center_box,
                text=f"👤 {user_profile['display_name']}",
                font=("Segoe UI", 12, "bold"),
                bg=self.widgets.bg_color,
                fg=self.widgets.accent_color,
            ).pack(pady=(0, 20))

        tk.Label(
            center_box,
            text="💾",
            font=("Segoe UI", 64),
            bg=self.widgets.bg_color,
            fg=self.widgets.accent_color,
        ).pack()
        tk.Label(
            center_box,
            text="Modo USB Bypass",
            font=("Segoe UI", 18, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(pady=(10, 5))

        status_card = tk.Frame(center_box, bg=self.widgets.card_bg, padx=20, pady=20)
        status_card.pack(fill="x", pady=30, ipadx=20)

        tk.Label(
            status_card,
            text="Conecta tu llave de seguridad",
            font=("Segoe UI", 11),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack()

        self.usb_status = tk.Label(
            status_card,
            text="🔍 Buscando...",
            font=("Segoe UI", 10),
            bg=self.widgets.card_bg,
            fg=self.widgets.warning_color,
        )
        self.usb_status.pack(pady=(10, 0))

        self.usb_login_btn = self.widgets.create_modern_button(
            center_box,
            "🔓 Entrar con USB",
            self.attempt_usb_login,
            self.widgets.success_color,
            width=25,
        )
        self.usb_login_btn.pack(pady=(0, 10))
        self.usb_login_btn.config(state="disabled", bg="#4b5563")

        self.widgets.create_modern_button(
            center_box,
            "🔄 Verificar de nuevo",
            self.verify_usb_status,
            self.widgets.accent_color,
            width=25,
        ).pack(pady=(0, 20))

        tk.Label(
            center_box,
            text="O usa otro método:",
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
        ).pack()

        self.widgets.create_modern_button(
            center_box,
            "📱 Usar Código / Contraseña",
            self.switch_to_totp_mode,
            "#8b5cf6",
            width=25,
        ).pack(pady=10)

        self.verify_usb_status()

    def create_totp_login_interface(self, user_profile):
        main_frame = tk.Frame(self.root, bg=self.widgets.bg_color)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        center_box = tk.Frame(main_frame, bg=self.widgets.bg_color)
        center_box.pack(expand=True)

        if user_profile:
            tk.Label(
                center_box,
                text=f"👤 {user_profile['display_name']}",
                font=("Segoe UI", 12, "bold"),
                bg=self.widgets.bg_color,
                fg=self.widgets.accent_color,
            ).pack(pady=(0, 15))

        tk.Label(
            center_box,
            text="🛡️",
            font=("Segoe UI", 64),
            bg=self.widgets.bg_color,
            fg=self.widgets.accent_color,
        ).pack()
        tk.Label(
            center_box,
            text="Inicio de Sesión",
            font=("Segoe UI", 22, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(pady=(5, 25))

        form_frame = tk.Frame(center_box, bg=self.widgets.bg_color)
        form_frame.pack(fill="x", ipadx=20)

        tk.Label(
            form_frame,
            text="Contraseña Maestra",
            font=("Segoe UI", 10, "bold"),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
            anchor="w",
        ).pack(fill="x")

        self.master_entry = self.widgets.create_styled_entry(form_frame, show="•")
        self.master_entry.pack(fill="x", ipady=8, pady=(5, 20))
        self.master_entry.bind("<Return>", lambda e: self.attempt_totp_login())
        self.master_entry.focus()

        tk.Label(
            form_frame,
            text="Código de Verificación (TOTP)",
            font=("Segoe UI", 10, "bold"),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
            anchor="center",
        ).pack(fill="x")

        self.totp_entry = self.widgets.create_styled_entry(form_frame)
        self.totp_entry.config(
            font=("Consolas", 16, "bold"), justify="center", width=10
        )
        self.totp_entry.pack(pady=(5, 20))
        self.widgets.create_modern_button(
            center_box,
            "🚀 Iniciar Sesión",
            self.attempt_totp_login,
            self.widgets.success_color,
            width=25,
        ).pack(pady=5)

        if self.usb.is_configured():
            self.widgets.create_modern_button(
                center_box,
                "💾 Usar Bypass USB",
                self.switch_to_usb_mode,
                self.widgets.accent_color,
                width=25,
            ).pack(pady=10)

        self.widgets.create_modern_button(
            center_box, "Salir", self.root.quit, self.widgets.text_secondary, width=15
        ).pack(pady=15)

    def verify_usb_status(self):
        try:
            if self.usb.verify_device():
                self.usb_status.config(
                    text="✅ USB Autorizado Detectado", fg=self.widgets.success_color
                )
                self.usb_login_btn.config(state="normal", bg=self.widgets.success_color)
            else:
                self.usb_status.config(
                    text="❌ USB no detectado", fg=self.widgets.danger_color
                )
                self.usb_login_btn.config(state="disabled", bg="#4b5563")
        except:
            pass

    def attempt_usb_login(self):
        if self.usb.verify_device():
            pwd = self.get_password_for_usb_login()
            if pwd:
                if db_manager.verify_master_password(pwd):
                    self.on_success_callback(pwd)
                else:
                    WindowHelper.show_custom_message(
                        self.root, "Error", "Contraseña incorrecta", is_error=True
                    )
        else:
            self.verify_usb_status()

    def get_password_for_usb_login(self):
        win = tk.Toplevel(self.root)
        win.title("Verificación")
        win.configure(bg=self.widgets.bg_color)
        WindowHelper.center_window(win, 450, 300)
        win.transient(self.root)
        win.grab_set()

        try:
            win.iconbitmap("icon.ico")
        except:
            pass

        main = tk.Frame(win, bg=self.widgets.bg_color, padx=30, pady=30)
        main.pack(fill="both", expand=True)

        tk.Label(
            main,
            text="🔐 Confirmar Identidad",
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(pady=(0, 15))
        tk.Label(
            main,
            text="Ingresa tu contraseña para desbloquear.",
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
        ).pack(pady=(0, 20))

        pwd_var = tk.StringVar()
        entry = self.widgets.create_styled_entry(main, pwd_var, show="•")
        entry.pack(fill="x", ipady=5)
        entry.focus()

        result = {"pwd": None}

        def submit():
            if pwd_var.get():
                result["pwd"] = pwd_var.get()
                win.destroy()

        entry.bind("<Return>", lambda e: submit())
        btn_f = tk.Frame(main, bg=self.widgets.bg_color)
        btn_f.pack(fill="x", pady=20)
        self.widgets.create_modern_button(
            btn_f, "Desbloquear", submit, self.widgets.success_color
        ).pack(side="right", padx=5)
        self.widgets.create_modern_button(
            btn_f, "Cancelar", win.destroy, self.widgets.text_secondary
        ).pack(side="right", padx=5)
        self.root.wait_window(win)
        return result["pwd"]

    def attempt_totp_login(self):
        pwd = self.master_entry.get()
        code = self.totp_entry.get().strip()
        if not pwd:
            WindowHelper.show_custom_message(
                self.root, "Error", "Falta contraseña", is_error=True
            )
            return

        try:
            methods = {"master_password": pwd}
            if code:
                methods["totp_offline"] = code
            if self.mfa.validate_authentication(methods, pwd):
                self.on_success_callback(pwd)
            else:
                WindowHelper.show_custom_message(
                    self.root, "Error", "Credenciales inválidas", is_error=True
                )
                self.totp_entry.delete(0, tk.END)
        except Exception as e:
            WindowHelper.show_custom_message(self.root, "Error", str(e), is_error=True)

    def switch_to_usb_mode(self):
        self.force_totp_mode = False
        self.create_login_interface(self.on_success_callback)

    def switch_to_totp_mode(self):
        self.force_totp_mode = True
        self.create_login_interface(self.on_success_callback)

    def show_usb_setup_info(self):
        WindowHelper.show_custom_message(
            self.root, "Información", "Configura un USB en las opciones."
        )
