import tkinter as tk
from tkinter import ttk
from .virtual_keyboard import VirtualKeyboard
import string
import secrets
import random
from modules.utils.helpers import (
    WindowHelper,
    PasswordHealth,
)
from modules.components.widgets import ModernWidgets
from modules.encryption import db_manager
from modules.utils.clipboard_security import ClipboardManager


class PasswordGeneratorModal:
    def __init__(self, parent, on_generate_callback):
        self.parent = parent
        self.on_generate_callback = on_generate_callback
        self.widgets = ModernWidgets()
        self.symbols = "!@#$%&*()_+-=[]{}|;:,.<>?/~"
        self.create_modal()

    def create_modal(self):
        self.modal = tk.Toplevel(self.parent)
        self.modal.title("Generador de Contraseñas")
        self.modal.configure(bg="#0a0a0a")
        self.modal.minsize(450, 500)
        self.modal.resizable(True, True)
        self.modal.transient(self.parent)
        self.modal.grab_set()

        main_container = tk.Frame(self.modal, bg="#0a0a0a")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = tk.Frame(main_container, bg="#0a0a0a")
        header_frame.pack(fill="x", pady=(0, 20))

        tk.Label(
            header_frame,
            text="🎲 Generar Contraseña",
            font=("Segoe UI", 16, "bold"),
            bg="#0a0a0a",
            fg="white",
        ).pack(side="left")

        self.security_indicator = tk.Label(
            header_frame, text="🔴", font=("Segoe UI", 14), bg="#0a0a0a"
        )
        self.security_indicator.pack(side="right", padx=(10, 0))

        self.security_label = tk.Label(
            header_frame,
            text="Débil",
            font=("Segoe UI", 10, "bold"),
            bg="#0a0a0a",
            fg="#ef4444",
        )
        self.security_label.pack(side="right")

        result_frame = tk.Frame(
            main_container, bg="#1a1a1a", padx=15, pady=15, relief="flat"
        )
        result_frame.pack(fill="x", pady=(0, 20))

        self.password_var = tk.StringVar()
        self.password_display = tk.Entry(
            result_frame,
            textvariable=self.password_var,
            font=("Consolas", 14, "bold"),
            justify="center",
            bg="#1a1a1a",
            fg="#10b981",
            relief="flat",
            bd=0,
            state="readonly",
        )
        self.password_display.pack(fill="x")

        actions_frame = tk.Frame(result_frame, bg="#1a1a1a")
        actions_frame.pack(fill="x", pady=(10, 0))
        actions_frame.pack_configure(anchor="center")

        tk.Button(
            actions_frame,
            text="🔄 Regenerar",
            command=self.generate_password,
            bg="#3b82f6",
            fg="white",
            relief="flat",
            font=("Segoe UI", 9),
            cursor="hand2",
        ).pack(side="left", padx=5)
        tk.Button(
            actions_frame,
            text="📋 Copiar",
            command=self.copy_password,
            bg="#8b5cf6",
            fg="white",
            relief="flat",
            font=("Segoe UI", 9),
            cursor="hand2",
        ).pack(side="left", padx=5)

        controls_frame = tk.LabelFrame(
            main_container,
            text="Personalización",
            bg="#0a0a0a",
            fg="gray",
            font=("Segoe UI", 9),
        )
        controls_frame.pack(fill="both", expand=True, pady=10, ipadx=10, ipady=10)

        len_frame = tk.Frame(controls_frame, bg="#0a0a0a")
        len_frame.pack(fill="x", pady=5)

        tk.Label(
            len_frame, text="Longitud:", bg="#0a0a0a", fg="white", font=("Segoe UI", 10)
        ).pack(side="left")
        self.length_label = tk.Label(
            len_frame,
            text="16",
            bg="#0a0a0a",
            fg="#3b82f6",
            font=("Segoe UI", 10, "bold"),
        )
        self.length_label.pack(side="right")

        self.length_var = tk.IntVar(value=16)
        tk.Scale(
            controls_frame,
            from_=8,
            to=64,
            orient="horizontal",
            variable=self.length_var,
            command=self.update_length_label,
            bg="#0a0a0a",
            fg="white",
            troughcolor="#333",
            highlightthickness=0,
            showvalue=0,
        ).pack(fill="x", pady=5)

        opts_grid = tk.Frame(controls_frame, bg="#0a0a0a")
        opts_grid.pack(fill="x", pady=10)

        self.lower_var = tk.BooleanVar(value=True)
        self.upper_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)

        checks = [
            ("abc", "Minúsculas", self.lower_var),
            ("ABC", "Mayúsculas", self.upper_var),
            ("123", "Números", self.digits_var),
            ("#$%", "Símbolos", self.symbols_var),
        ]

        for i, (icon, text, var) in enumerate(checks):
            r, c = divmod(i, 2)
            f = tk.Frame(opts_grid, bg="#0a0a0a")
            f.grid(row=r, column=c, sticky="w", padx=10, pady=5)
            tk.Checkbutton(
                f,
                text=f"{text} ({icon})",
                variable=var,
                command=self.on_options_change,
                bg="#0a0a0a",
                fg="white",
                selectcolor="#2563eb",
                activebackground="#0a0a0a",
                activeforeground="white",
                font=("Segoe UI", 10),
            ).pack(anchor="w")

        btn_frame = tk.Frame(main_container, bg="#0a0a0a")
        btn_frame.pack(fill="x", pady=20, side="bottom")

        self.widgets.create_modern_button(
            btn_frame, "✅ Usar Contraseña", self.use_password, "#10b981"
        ).pack(side="right", padx=5)
        self.widgets.create_modern_button(
            btn_frame, "Cancelar", self.modal.destroy, "#6b7280"
        ).pack(side="right", padx=5)

        self.generate_password()
        self.update_security_indicator()

        self.modal.update_idletasks()
        w = self.modal.winfo_reqwidth()
        h = self.modal.winfo_reqheight()
        WindowHelper.center_window(self.modal, w, h)

    def update_length_label(self, value):
        length = int(float(value))
        self.length_label.config(text=str(length))
        self.generate_password()

    def on_options_change(self):
        self.generate_password()

    def update_security_indicator(self):
        current_password = self.password_var.get()
        score, text, color, emoji = PasswordHealth.assess_strength(current_password)

        self.security_indicator.config(text=emoji, fg=color)
        self.security_label.config(text=text, fg=color)

    def generate_balanced_password(self, length, characters):
        if not characters:
            return "Selecciona opciones"
        password = []
        char_sets = []
        if self.lower_var.get():
            char_sets.append(string.ascii_lowercase)
        if self.upper_var.get():
            char_sets.append(string.ascii_uppercase)
        if self.digits_var.get():
            char_sets.append(string.digits)
        if self.symbols_var.get():
            char_sets.append(self.symbols)

        min_per_type = (
            max(1, length // (len(char_sets) * 2)) if len(char_sets) > 0 else 0
        )
        for char_set in char_sets:
            for _ in range(min_per_type):
                password.append(secrets.choice(char_set))

        remaining_length = length - len(password)
        for _ in range(remaining_length):
            char_set = secrets.choice(char_sets)
            password.append(secrets.choice(char_set))

        secrets.SystemRandom().shuffle(password)
        return "".join(password)

    def generate_password(self):
        length = self.length_var.get()
        characters = ""
        if self.lower_var.get():
            characters += string.ascii_lowercase
        if self.upper_var.get():
            characters += string.ascii_uppercase
        if self.digits_var.get():
            characters += string.digits
        if self.symbols_var.get():
            characters += self.symbols

        if not characters:
            self.password_var.set("Seleccione opciones")
            self.security_indicator.config(text="⚪", fg="#6b7280")
            self.security_label.config(text="Vacía", fg="#6b7280")
            return

        password = self.generate_balanced_password(length, characters)
        self.password_var.set(password)
        self.update_security_indicator()

    def copy_password(self):
        password = self.password_var.get()
        if password and " " not in password:
            self.modal.clipboard_clear()
            self.modal.clipboard_append(password)
            self.password_display.config(bg="#064e3b", fg="white")
            self.modal.after(
                500, lambda: self.password_display.config(bg="#1a1a1a", fg="#10b981")
            )

    def use_password(self):
        password = self.password_var.get()
        if password and " " not in password:
            self.on_generate_callback(password)
            self.modal.destroy()


class PasswordEditModal:
    def __init__(self, parent, password_data, master_password, on_save_callback):
        self.parent = parent
        self.password_data = password_data
        self.master_password = master_password
        self.on_save_callback = on_save_callback
        self.widgets = ModernWidgets()
        self.password_visible = False
        self.create_modal()

    def create_modal(self):
        self.modal = tk.Toplevel(self.parent)
        self.modal.title(f"Editar - {self.password_data['title']}")
        self.modal.configure(bg="#0a0a0a")
        self.modal.minsize(550, 600)
        self.modal.resizable(True, True)
        self.modal.transient(self.parent)
        self.modal.grab_set()
        self.clipboard_manager = ClipboardManager(self.parent)
        main_frame = tk.Frame(self.modal, bg="#0a0a0a", padx=30, pady=25)
        main_frame.pack(fill="both", expand=True)

        tk.Label(
            main_frame,
            text="✏️ Editar Contraseña",
            font=("Segoe UI", 18, "bold"),
            bg="#0a0a0a",
            fg="white",
        ).pack(fill="x", pady=(0, 20))

        form_frame = tk.Frame(main_frame, bg="#0a0a0a")
        form_frame.pack(fill="both", expand=True)
        form_frame.grid_columnconfigure(1, weight=1)

        self.form_entries = {}
        lbl_style = {"font": ("Segoe UI", 10, "bold"), "bg": "#0a0a0a", "fg": "#9ca3af"}
        entry_style = {
            "font": ("Segoe UI", 10),
            "bg": "#2d2d2d",
            "fg": "white",
            "insertbackground": "white",
            "relief": "flat",
            "bd": 1,
        }

        tk.Label(form_frame, text="Categoría:", **lbl_style).grid(
            row=0, column=0, padx=(0, 15), pady=10, sticky="e"
        )
        categories = db_manager.get_categories()
        cat_names = [cat["name"] for cat in categories]
        self.category_var = tk.StringVar(value=self.password_data["category"])
        cat_combo = ttk.Combobox(
            form_frame,
            textvariable=self.category_var,
            values=cat_names,
            state="readonly",
        )
        cat_combo.grid(row=0, column=1, sticky="ew", pady=10)

        tk.Label(form_frame, text="Título:", **lbl_style).grid(
            row=1, column=0, padx=(0, 15), pady=10, sticky="e"
        )
        title_var = tk.StringVar(value=self.password_data["title"])
        title_entry = tk.Entry(form_frame, textvariable=title_var, **entry_style)
        title_entry.grid(row=1, column=1, sticky="ew", ipady=5, pady=10)
        self.form_entries["title"] = title_entry

        tk.Label(form_frame, text="Usuario:", **lbl_style).grid(
            row=2, column=0, padx=(0, 15), pady=10, sticky="e"
        )
        self.username_var = tk.StringVar(value=self.password_data["username"] or "")
        user_entry = tk.Entry(form_frame, textvariable=self.username_var, **entry_style)
        user_entry.grid(row=2, column=1, sticky="ew", ipady=5, pady=10)
        self.form_entries["username"] = user_entry

        tk.Label(form_frame, text="Contraseña:", **lbl_style).grid(
            row=3, column=0, padx=(0, 15), pady=10, sticky="e"
        )
        pwd_container = tk.Frame(form_frame, bg="#0a0a0a")
        pwd_container.grid(row=3, column=1, sticky="ew", pady=10)
        pwd_container.grid_columnconfigure(0, weight=1)

        self.password_var = tk.StringVar(value=self.password_data["password"])
        self.password_entry = tk.Entry(
            pwd_container, textvariable=self.password_var, show="•", **entry_style
        )
        self.password_entry.grid(row=0, column=0, sticky="ew", ipady=5)
        self.form_entries["password"] = self.password_entry

        tools_frame = tk.Frame(pwd_container, bg="#0a0a0a")
        tools_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        self.copy_btn = self.widgets.create_modern_button(
            tools_frame, "📋", self.copy_password_securely, "#8b5cf6", width=3
        )
        self.copy_btn.pack(side="left", padx=(0, 2))

        self.widgets.create_modern_button(
            tools_frame, "👁️", self.toggle_password_visibility, "#f59e0b", width=3
        ).pack(side="left", padx=2)
        self.widgets.create_modern_button(
            tools_frame, "🎲", self.generate_new_password, "#10b981", width=3
        ).pack(side="left", padx=2)
        self.widgets.create_modern_button(
            tools_frame,
            "⌨️",
            lambda: VirtualKeyboard(self.modal).create_keyboard(self.password_entry),
            "#3b82f6",
            width=3,
        ).pack(side="left", padx=2)

        tk.Label(form_frame, text="URL:", **lbl_style).grid(
            row=4, column=0, padx=(0, 15), pady=10, sticky="e"
        )
        url_var = tk.StringVar(value=self.password_data["url"] or "")
        url_entry = tk.Entry(form_frame, textvariable=url_var, **entry_style)
        url_entry.grid(row=4, column=1, sticky="ew", ipady=5, pady=10)
        self.form_entries["url"] = url_entry

        tk.Label(form_frame, text="Notas:", **lbl_style).grid(
            row=5, column=0, padx=(0, 15), pady=10, sticky="ne"
        )
        notes_text = tk.Text(form_frame, height=4, **entry_style)
        notes_text.grid(row=5, column=1, sticky="ew", pady=10)
        notes_text.insert("1.0", self.password_data["notes"] or "")
        self.form_entries["notes"] = notes_text

        footer_frame = tk.Frame(main_frame, bg="#0a0a0a")
        footer_frame.pack(fill="x", side="bottom", pady=10)
        self.widgets.create_modern_button(
            footer_frame, "💾 Guardar Cambios", self.save_changes, "#10b981", width=20
        ).pack(side="right", padx=5)
        self.widgets.create_modern_button(
            footer_frame, "Cancelar", self.modal.destroy, "#6b7280", width=10
        ).pack(side="right", padx=5)

        self.modal.update_idletasks()
        w = self.modal.winfo_reqwidth()
        h = self.modal.winfo_reqheight()
        screen_w = self.modal.winfo_screenwidth()
        screen_h = self.modal.winfo_screenheight()
        final_w = min(w + 20, screen_w - 100)
        final_h = min(h + 20, screen_h - 100)
        WindowHelper.center_window(self.modal, final_w, final_h)

    def copy_password_securely(self):
        pwd = self.password_var.get()
        if pwd:
            if self.clipboard_manager.copy_to_clipboard(pwd):
                original_text = self.copy_btn.cget("text")
                original_bg = self.copy_btn.cget("bg")
                self.copy_btn.config(text="✅", bg="#10b981")
                self.modal.after(
                    1500,
                    lambda: self.copy_btn.config(text=original_text, bg=original_bg),
                )

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible
        self.password_entry.config(show="" if self.password_visible else "•")

    def generate_new_password(self):
        def on_generate(password):
            self.password_var.set(password)

        PasswordGeneratorModal(self.modal, on_generate)

    def save_changes(self):
        cat_name = self.category_var.get()
        title = self.form_entries["title"].get()
        user = self.username_var.get()
        pwd = self.password_var.get()
        url = self.form_entries["url"].get()
        notes = self.form_entries["notes"].get("1.0", tk.END).strip()

        if not all([cat_name, title, pwd]):
            WindowHelper.show_custom_message(
                self.modal, "Error", "Faltan campos obligatorios", is_error=True
            )
            return

        cats = db_manager.get_categories()
        cat_id = next((c["id"] for c in cats if c["name"] == cat_name), None)
        if not cat_id:
            WindowHelper.show_custom_message(
                self.modal, "Error", "Categoría inválida", is_error=True
            )
            return

        success = db_manager.update_password_entry(
            self.password_data["id"],
            cat_id,
            title,
            user,
            pwd,
            url,
            notes,
            self.master_password,
        )
        if success:
            self.on_save_callback()
            self.modal.destroy()
        else:
            WindowHelper.show_custom_message(
                self.modal, "Error", "No se pudo guardar", is_error=True
            )
