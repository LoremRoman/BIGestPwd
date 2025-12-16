import tkinter as tk
from tkinter import ttk
import secrets
import pyotp
import webbrowser
from modules.auth.multi_factor import MultiFactorAuth
from modules.auth.totp_offline import TOTPOffline
from modules.utils.helpers import WindowHelper
from modules.components.widgets import ModernWidgets


class MFASetupWizard:
    def __init__(self, parent, master_password, on_complete_callback):
        self.parent = parent
        self.master_password = master_password
        self.on_complete_callback = on_complete_callback
        self.widgets = ModernWidgets()
        self.mfa = MultiFactorAuth()
        self.totp = TOTPOffline()
        self.current_step = 0
        self.user_profile = None
        self.totp_secret = None
        self.totp_verified = False

        self.setup_wizard()

    def setup_wizard(self):
        self.parent.title("Configuración de Seguridad - BIGestPwd 2.8.2")
        self.parent.configure(bg=self.widgets.bg_color)

        width = 750
        height = 800
        WindowHelper.center_window(self.parent, width, height)

        main_container = tk.Frame(self.parent, bg=self.widgets.bg_color)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = tk.Frame(main_container, bg=self.widgets.bg_color)
        header_frame.pack(fill="x", pady=(0, 20))

        tk.Label(
            header_frame,
            text="🛡️ Configuración de Seguridad",
            font=("Segoe UI", 20, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack()

        tk.Label(
            header_frame,
            text="Configura al menos 2 métodos para máxima protección",
            font=("Segoe UI", 10),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
        ).pack(pady=(5, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Horizontal.TProgressbar",
            background=self.widgets.accent_color,
            troughcolor=self.widgets.card_bg,
            bordercolor=self.widgets.bg_color,
            lightcolor=self.widgets.accent_color,
            darkcolor=self.widgets.accent_color,
        )

        self.progress_bar = ttk.Progressbar(
            header_frame,
            orient="horizontal",
            length=400,
            mode="determinate",
            style="Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", padx=40)

        canvas = tk.Canvas(
            main_container, bg=self.widgets.bg_color, highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            main_container, orient="vertical", command=canvas.yview
        )
        self.content_frame = tk.Frame(canvas, bg=self.widgets.bg_color)

        self.content_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw"
        )

        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", configure_canvas)

        canvas.configure(yscrollcommand=scrollbar.set)

        self.nav_frame = tk.Frame(main_container, bg=self.widgets.bg_color, pady=10)
        self.nav_frame.pack(side="bottom", fill="x")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except:
                pass

        canvas.bind(
            "<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_mousewheel)
        )
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        self.back_btn = self.widgets.create_modern_button(
            self.nav_frame,
            "⬅️ Anterior",
            self.previous_step,
            self.widgets.text_secondary,
            width=15,
        )
        self.back_btn.pack(side="left")

        self.next_btn = self.widgets.create_modern_button(
            self.nav_frame,
            "Siguiente ➡️",
            self.next_step,
            self.widgets.accent_color,
            width=15,
        )
        self.next_btn.pack(side="right")

        self.steps = [
            self.create_profile_step,
            self.create_welcome_step,
            self.create_totp_step,
            self.create_usb_bypass_step,
            self.create_summary_step,
        ]

        self.show_step(0)

    def show_step(self, step_index):
        self.current_step = step_index
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.steps[step_index]()

        progress = ((step_index + 1) / len(self.steps)) * 100
        self.progress_bar["value"] = progress

        self.back_btn["state"] = "normal" if step_index > 0 else "disabled"
        self.back_btn.config(
            bg=self.widgets.text_secondary if step_index > 0 else "#333"
        )

        if step_index == len(self.steps) - 1:
            self.next_btn.config(text="✅ Finalizar", bg=self.widgets.success_color)
        else:
            self.next_btn.config(text="Siguiente ➡️", bg=self.widgets.accent_color)

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            if self.current_step == 0 and not self.validate_profile_step():
                return
            if self.current_step == 2 and not self.validate_totp_step():
                return
            self.show_step(self.current_step + 1)
        else:
            self.complete_setup()

    def previous_step(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def create_profile_step(self):
        self._step_header(
            "👤 Configurar Perfil", "Elige cómo te identificarás en la aplicación"
        )

        self.profile_type = tk.StringVar(value="personal")

        card1 = tk.Frame(self.content_frame, bg=self.widgets.card_bg, padx=15, pady=15)
        card1.pack(fill="x", pady=10)

        rb1 = tk.Radiobutton(
            card1,
            text="📝 Usar nombre personal",
            variable=self.profile_type,
            value="personal",
            command=self.on_profile_type_change,
            bg=self.widgets.card_bg,
            fg="white",
            selectcolor=self.widgets.accent_color,
            font=("Segoe UI", 11, "bold"),
            activebackground=self.widgets.card_bg,
        )
        rb1.pack(anchor="w")

        self.personal_fields = tk.Frame(card1, bg=self.widgets.card_bg)
        self.personal_fields.pack(fill="x", pady=(10, 0), padx=20)

        tk.Label(
            self.personal_fields,
            text="Nombre:",
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
        ).pack(anchor="w")
        self.name_var = tk.StringVar()
        self.name_entry = self.widgets.create_styled_entry(
            self.personal_fields, self.name_var
        )
        self.name_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            self.personal_fields,
            text="Apellido:",
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
        ).pack(anchor="w")
        self.lastname_var = tk.StringVar()
        self.lastname_entry = self.widgets.create_styled_entry(
            self.personal_fields, self.lastname_var
        )
        self.lastname_entry.pack(fill="x")

        card2 = tk.Frame(self.content_frame, bg=self.widgets.card_bg, padx=15, pady=15)
        card2.pack(fill="x", pady=10)

        rb2 = tk.Radiobutton(
            card2,
            text="🕶️ Generar nombre anónimo",
            variable=self.profile_type,
            value="anonymous",
            command=self.on_profile_type_change,
            bg=self.widgets.card_bg,
            fg="white",
            selectcolor=self.widgets.accent_color,
            font=("Segoe UI", 11, "bold"),
            activebackground=self.widgets.card_bg,
        )
        rb2.pack(anchor="w")

        tk.Label(
            card2,
            text="Se generará un alias único (ej. Anon4287). No se puede cambiar después.",
            font=("Segoe UI", 9),
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
        ).pack(anchor="w", padx=20, pady=5)

        self.on_profile_type_change()

    def on_profile_type_change(self):
        state = "normal" if self.profile_type.get() == "personal" else "disabled"
        self.name_entry.config(state=state)
        self.lastname_entry.config(state=state)

    def validate_profile_step(self):
        ptype = self.profile_type.get()
        if ptype == "personal":
            if not self.name_var.get().strip():
                WindowHelper.show_custom_message(
                    self.parent, "Error", "Ingresa tu nombre", is_error=True
                )
                return False
            dname = f"{self.name_var.get()} {self.lastname_var.get()}".strip()
            anon = False
        else:
            dname = f"Anon{secrets.randbelow(10000):04d}"
            anon = True

        self.user_profile = {"display_name": dname, "is_anonymous": anon}
        return True

    def create_welcome_step(self):
        self._step_header(
            f"Hola, {self.user_profile['display_name']}",
            "Entendiendo la Autenticación Múltiple (MFA)",
        )

        info_card = tk.Frame(
            self.content_frame, bg=self.widgets.card_bg, padx=20, pady=20
        )
        info_card.pack(fill="x", pady=10)

        tk.Label(
            info_card,
            text="¿Qué es MFA?",
            font=("Segoe UI", 12, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.accent_color,
        ).pack(anchor="w")

        what_is_text = (
            "MFA (Autenticación Multifactor) es como tener dos cerraduras en tu puerta. "
            "No basta con tener la llave (tu contraseña maestra); también necesitas abrir "
            "el cerrojo de seguridad (tu teléfono o USB)."
        )
        tk.Label(
            info_card,
            text=what_is_text,
            bg=self.widgets.card_bg,
            fg="white",
            wraplength=550,
            justify="left",
        ).pack(pady=(5, 15))

        tk.Label(
            info_card,
            text="¿Por qué lo necesitamos?",
            font=("Segoe UI", 12, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.accent_color,
        ).pack(anchor="w")

        why_text = (
            "Si un hacker adivina tu contraseña, NO podrá robar tus datos porque le faltará "
            "tu dispositivo físico. BIGestPwd te protege incluso si cometes un error."
        )
        tk.Label(
            info_card,
            text=why_text,
            bg=self.widgets.card_bg,
            fg="white",
            wraplength=550,
            justify="left",
        ).pack(pady=(5, 0))

        tk.Label(
            self.content_frame,
            text="Estado Actual:",
            font=("Segoe UI", 11, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(anchor="w", pady=(20, 5))

        methods = self.mfa.get_mfa_status()
        for k, v in methods.items():
            icon = "✅" if v["configured"] else "❌"
            color = (
                self.widgets.success_color
                if v["configured"]
                else self.widgets.danger_color
            )
            lbl = {
                "master_password": "Llave Maestra",
                "totp_offline": "Código TOTP",
                "usb_bypass": "Bypass USB",
            }[k]

            f = tk.Frame(self.content_frame, bg=self.widgets.bg_color)
            f.pack(fill="x", pady=2)
            tk.Label(
                f, text=icon, bg=self.widgets.bg_color, fg=color, font=("Segoe UI", 12)
            ).pack(side="left")
            tk.Label(f, text=lbl, bg=self.widgets.bg_color, fg="white").pack(
                side="left", padx=10
            )

    def create_totp_step(self):
        self._step_header(
            "📱 Autenticación Móvil", "Usa tu celular como llave de acceso"
        )

        if self.totp.is_configured() or self.totp_verified:
            self._show_totp_success()
            return

        card = tk.Frame(self.content_frame, bg=self.widgets.card_bg, padx=20, pady=20)
        card.pack(fill="x", pady=10)

        tk.Label(
            card,
            text="¿Qué es el Código QR?",
            font=("Segoe UI", 11, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.accent_color,
        ).pack(anchor="w")
        qr_exp = (
            "Este código contiene una 'semilla' secreta única para ti. Necesitas escanearlo con una app "
            "especializada que genera códigos numéricos que cambian cada 30 segundos."
        )
        tk.Label(
            card,
            text=qr_exp,
            bg=self.widgets.card_bg,
            fg="white",
            justify="left",
            wraplength=550,
        ).pack(anchor="w", pady=(5, 10))

        tk.Label(
            card,
            text="Instrucciones:",
            font=("Segoe UI", 11, "bold"),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack(anchor="w")
        steps = (
            "1. Descarga 'Google Authenticator' o 'Authy' en tu celular (App Store / Play Store).\n"
            "2. Abre la app y selecciona 'Agregar cuenta' o el símbolo (+).\n"
            "3. Escanea el código QR que aparecerá abajo.\n"
            "4. La app te dará un código de 6 dígitos. Ingrésalo aquí."
        )
        tk.Label(
            card,
            text=steps,
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
            justify="left",
        ).pack(anchor="w", pady=5)

        if not self.totp_secret:
            self.totp_secret = self.totp.generate_secret()

        self.widgets.create_modern_button(
            card,
            "📷 Mostrar Código QR",
            self.show_qr_modal,
            self.widgets.accent_color,
            width=25,
        ).pack(pady=15)

        tk.Label(
            self.content_frame,
            text="Verificar Código:",
            font=("Segoe UI", 11, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(anchor="w", pady=(20, 5))

        verify_frame = tk.Frame(self.content_frame, bg=self.widgets.bg_color)
        verify_frame.pack(fill="x")

        self.verify_code_var = tk.StringVar()
        self.verify_entry = self.widgets.create_styled_entry(
            verify_frame, self.verify_code_var
        )
        self.verify_entry.config(font=("Consolas", 14), justify="center", width=10)
        self.verify_entry.pack(side="left")
        self.verify_entry.bind("<KeyRelease>", self.on_verify_code_input)

        self.verify_status = tk.Label(
            verify_frame,
            text="⏳ Esperando código...",
            bg=self.widgets.bg_color,
            fg=self.widgets.warning_color,
        )
        self.verify_status.pack(side="left", padx=15)

        if not self.totp_verified:
            self.parent.after(500, self.show_qr_modal)

    def _show_totp_success(self):
        card = tk.Frame(self.content_frame, bg=self.widgets.card_bg, padx=20, pady=20)
        card.pack(fill="x", pady=20)
        tk.Label(
            card,
            text="✅ TOTP Configurado",
            font=("Segoe UI", 16, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.success_color,
        ).pack()
        self.widgets.create_modern_button(
            card,
            "🔑 Ver Códigos de Respaldo",
            self.show_backup_codes_modal,
            self.widgets.warning_color,
        ).pack(pady=10)
        self.totp_verified = True

    def validate_totp_step(self):
        if not self.totp_verified and not self.totp.is_configured():
            WindowHelper.show_custom_message(
                self.parent,
                "Requerido",
                "Debes configurar TOTP para continuar.",
                is_error=True,
            )
            return False
        return True

    def show_qr_modal(self):
        if not self.totp_secret:
            return
        qr_win = tk.Toplevel(self.parent)
        qr_win.title("Escanear QR")
        qr_win.configure(bg=self.widgets.bg_color)
        WindowHelper.center_window(qr_win, 400, 550)

        pname = self.user_profile["display_name"] if self.user_profile else "Usuario"
        qr_img, _ = self.totp.generate_qr_code(self.totp_secret, pname)

        from PIL import Image, ImageTk
        import io

        img = Image.open(io.BytesIO(qr_img))
        img = img.resize((300, 300))
        photo = ImageTk.PhotoImage(img)

        tk.Label(
            qr_win,
            text="Escanear en App",
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(pady=20)
        lbl = tk.Label(qr_win, image=photo, bg=self.widgets.bg_color)
        lbl.image = photo
        lbl.pack(pady=10)

        tk.Label(
            qr_win,
            text=self.totp_secret,
            font=("Consolas", 10),
            bg=self.widgets.bg_color,
            fg=self.widgets.accent_color,
        ).pack(pady=5)
        self.widgets.create_modern_button(
            qr_win, "Cerrar", qr_win.destroy, self.widgets.success_color
        ).pack(pady=20)

    def on_verify_code_input(self, e):
        code = self.verify_code_var.get().strip()
        if len(code) == 6 and code.isdigit():
            totp = pyotp.TOTP(self.totp_secret)
            if totp.verify(code, valid_window=1):
                self.verify_status.config(
                    text="✅ Correcto", fg=self.widgets.success_color
                )
                self.totp_verified = True
                backups = self.totp.save_secret(self.totp_secret, self.master_password)
                self.mfa.update_mfa_method(
                    "totp_offline", enabled=True, configured=True
                )
                self.parent.after(500, lambda: self.show_backup_codes_modal(backups))
            else:
                self.verify_status.config(
                    text="❌ Incorrecto", fg=self.widgets.danger_color
                )

    def show_backup_codes_modal(self, codes=None):
        if not codes:
            return
        win = tk.Toplevel(self.parent)
        win.title("Códigos de Respaldo")
        win.configure(bg=self.widgets.bg_color)
        WindowHelper.center_window(win, 500, 600)

        tk.Label(
            win,
            text="⚠️ GUARDA ESTOS CÓDIGOS",
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.bg_color,
            fg=self.widgets.warning_color,
        ).pack(pady=20)
        tk.Label(
            win,
            text="Úsala si pierdes tu teléfono. Solo funcionan una vez.",
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(pady=5)

        frame = tk.Frame(win, bg=self.widgets.card_bg, padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        for i, code in enumerate(codes):
            tk.Label(
                frame,
                text=f"{i+1}. {code}",
                font=("Consolas", 12),
                bg=self.widgets.card_bg,
                fg=self.widgets.success_color,
            ).pack(anchor="w")

        self.widgets.create_modern_button(
            win, "He guardado los códigos", win.destroy, self.widgets.success_color
        ).pack(pady=20)

    def create_usb_bypass_step(self):
        self._step_header("💾 Bypass USB (Opcional)", "Máxima seguridad física")
        from modules.auth.usb_bypass import USBBypass

        usb = USBBypass()

        card = tk.Frame(self.content_frame, bg=self.widgets.card_bg, padx=20, pady=20)
        card.pack(fill="x", pady=10)

        tk.Label(
            card,
            text="Tu Llave Física Maestra",
            font=("Segoe UI", 12, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.accent_color,
        ).pack(anchor="w")

        sec_msg = (
            "Este método convierte cualquier memoria USB común en una 'Llave de Hardware' de alta seguridad. "
            "El sistema escribirá un archivo encriptado único en tu USB. \n\n"
            "✅ Ventaja: Si conectas el USB, no necesitas escribir códigos.\n"
            "🔒 Seguridad: Sin el USB físico, nadie puede usar este método de entrada."
        )
        tk.Label(
            card,
            text=sec_msg,
            bg=self.widgets.card_bg,
            fg="white",
            justify="left",
            wraplength=550,
        ).pack(anchor="w", pady=5)

        btn_text = (
            "⚙️ Gestionar USBs" if usb.is_configured() else "💾 Configurar Nuevo USB"
        )
        btn_col = (
            self.widgets.warning_color
            if usb.is_configured()
            else self.widgets.accent_color
        )

        self.widgets.create_modern_button(
            self.content_frame, btn_text, self.setup_usb_bypass, btn_col, width=25
        ).pack(pady=20)

        if usb.is_configured():
            tk.Label(
                self.content_frame,
                text="✅ Dispositivos configurados:",
                font=("Segoe UI", 11, "bold"),
                bg=self.widgets.bg_color,
                fg=self.widgets.success_color,
            ).pack(anchor="w")
            for dev in usb.get_authorized_devices():
                tk.Label(
                    self.content_frame,
                    text=f"• 💾 {dev['name']}",
                    bg=self.widgets.bg_color,
                    fg="white",
                ).pack(anchor="w", padx=20)

    def setup_usb_bypass(self):
        from modules.auth.usb_bypass import USBBypass

        usb = USBBypass()
        devs = usb.detect_real_usb_devices()

        if not devs:
            WindowHelper.show_custom_message(
                self.parent,
                "No detectado",
                "Conecta un USB y reintenta.",
                is_error=True,
            )
            return

        win = tk.Toplevel(self.parent)
        win.title("Seleccionar USB")
        win.configure(bg=self.widgets.bg_color)
        WindowHelper.center_window(win, 500, 500)

        tk.Label(
            win,
            text="Selecciona un dispositivo",
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(pady=20)

        list_f = tk.Frame(win, bg=self.widgets.bg_color)
        list_f.pack(fill="both", expand=True, padx=20)

        selected = tk.StringVar()
        for d in devs:
            f = tk.Frame(list_f, bg=self.widgets.card_bg, pady=10, padx=10)
            f.pack(fill="x", pady=5)
            tk.Radiobutton(
                f,
                text=f"{d['name']} ({d['size_gb']}GB)",
                variable=selected,
                value=d["uuid"],
                bg=self.widgets.card_bg,
                fg="white",
                selectcolor=self.widgets.accent_color,
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w")

        def save():
            if not selected.get():
                return
            sel_dev = next((d for d in devs if d["uuid"] == selected.get()), None)
            if sel_dev:
                res, msg = usb.register_usb_device(
                    sel_dev["name"], sel_dev["path"], self.master_password
                )
                if res:
                    WindowHelper.show_custom_message(win, "Éxito", "USB Configurado")
                    win.destroy()
                    self.show_step(3)
                else:
                    WindowHelper.show_custom_message(win, "Error", msg, is_error=True)

        self.widgets.create_modern_button(
            win, "Guardar Configuración", save, self.widgets.success_color
        ).pack(pady=20)

    def create_summary_step(self):
        self._step_header("✅ Todo Listo", "Tu bóveda está segura")

        card = tk.Frame(self.content_frame, bg=self.widgets.card_bg, padx=20, pady=20)
        card.pack(fill="both", expand=True, pady=10)

        tk.Label(
            card,
            text=f"Perfil: {self.user_profile['display_name']}",
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.card_bg,
            fg=self.widgets.accent_color,
        ).pack(pady=10)

        methods = self.mfa.get_mfa_status()
        active = sum(1 for m in methods.values() if m["configured"])

        tk.Label(
            card,
            text=f"Métodos Activos: {active}/3",
            font=("Segoe UI", 12),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack()
        tk.Label(
            card,
            text="Recuerda: Necesitas 2 métodos para entrar.",
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
        ).pack(pady=10)

        footer_frame = tk.Frame(self.content_frame, bg=self.widgets.bg_color)
        footer_frame.pack(side="bottom", pady=20)

        tk.Label(
            footer_frame,
            text="Desarrollado con ❤️ por LoremRoman",
            font=("Segoe UI", 9),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
        ).pack()

        def open_repo():
            webbrowser.open("https://github.com/LoremRoman/BIGestPwd")

        repo_link = tk.Label(
            footer_frame,
            text="Visitar Repositorio Oficial",
            font=("Segoe UI", 9, "underline"),
            bg=self.widgets.bg_color,
            fg=self.widgets.accent_color,
            cursor="hand2",
        )
        repo_link.pack(pady=2)
        repo_link.bind("<Button-1>", lambda e: open_repo())

    def _step_header(self, title, subtitle):
        tk.Label(
            self.content_frame,
            text=title,
            font=("Segoe UI", 16, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(anchor="w", pady=(0, 5))
        tk.Label(
            self.content_frame,
            text=subtitle,
            font=("Segoe UI", 10),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
        ).pack(anchor="w", pady=(0, 20))

    def complete_setup(self):
        if self.user_profile:
            self.mfa.save_user_profile(
                self.user_profile["display_name"], self.user_profile["is_anonymous"]
            )

        methods = self.mfa.get_mfa_status()
        active = sum(
            1 for k, v in methods.items() if k != "master_password" and v["configured"]
        )

        if active < 1:
            WindowHelper.show_custom_message(
                self.parent, "Inseguro", "Configura al menos TOTP o USB.", is_error=True
            )
            self.show_step(2)
        else:
            self.on_complete_callback()
