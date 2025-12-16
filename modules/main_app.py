import tkinter as tk
from tkinter import ttk, messagebox, Menu
import webbrowser
import json
import os
import time
from modules.encryption import db_manager
from modules.components.virtual_keyboard import VirtualKeyboard
from modules.components.modals import PasswordGeneratorModal, PasswordEditModal
from modules.components.security_modals import (
    PasswordChangeModal,
    USBManagementModal,
    TOTPManagementModal,
)
from modules.components.widgets import ModernWidgets
from modules.utils.helpers import WindowHelper, PasswordHealth, Tooltip
from modules.utils.clipboard_security import ClipboardManager
from modules.auth.multi_factor import MultiFactorAuth
from modules.auth.totp_offline import TOTPOffline
from modules.auth.usb_bypass import USBBypass
from modules.utils.updater import AppUpdater

SETTINGS_FILE = os.path.join(os.getcwd(), "data", "settings.json")


class MainApplication:
    def __init__(self, root, master_password, on_logout_callback=None):
        self.root = root
        self.master_password = master_password
        self.on_logout_callback = on_logout_callback
        self.virtual_kb = VirtualKeyboard(root)
        self.widgets = ModernWidgets()
        self.mfa = MultiFactorAuth()
        self.totp = TOTPOffline()
        self.usb = USBBypass()
        self.clipboard_manager = ClipboardManager(root)
        self.tooltip = Tooltip(root)
        self.password_health_data = {}
        self.current_search = ""
        self.selected_item = None
        self.user_profile = self.mfa.get_user_profile()

        self.last_menu_close_time = 0
        self.btn_settings = None

        self.settings = {
            "start_with_windows": False,
            "minimize_to_tray": True,
            "afk_lock": True,
            "clean_clipboard": True,
            "privacy_mode": False,
        }
        self.load_settings()

        self.root.title("BIGestPwd 2.8.1 - Gestor Principal")
        self.root.configure(bg=self.widgets.bg_color)

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.apply_initial_settings()
        self.setup_styles()
        self.create_interface()
        self.load_categories()
        self.load_passwords()

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                    self.settings.update(saved)
        except:
            pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f)
        except:
            pass

    def apply_initial_settings(self):
        if self.settings["privacy_mode"]:
            WindowHelper.set_display_affinity(self.root, True)

    def setup_styles(self):
        self.style = self.widgets.setup_treeview_style()

        self.style.configure(
            "TNotebook", background=self.widgets.bg_color, borderwidth=0
        )
        self.style.configure(
            "TNotebook.Tab",
            background=self.widgets.bg_color,
            foreground=self.widgets.text_secondary,
            padding=[15, 8],
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", self.widgets.card_bg)],
            foreground=[("selected", self.widgets.accent_color)],
        )

    def create_interface(self):
        self.create_header()

        main_container = tk.Frame(self.root, bg=self.widgets.bg_color)
        main_container.pack(fill="both", expand=True, padx=15, pady=10)

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True)
        self.create_passwords_tab()
        self.create_add_tab()
        self.create_security_tab()
        self.create_about_tab()
        self.create_status_bar()

    def create_header(self):
        header = tk.Frame(self.root, bg=self.widgets.bg_color, height=60)
        header.pack(fill="x", padx=20, pady=10)

        icon_img = self.widgets.get_icon_image(size=(40, 40))
        if icon_img:
            self.widgets.image_cache["header_icon"] = icon_img
            tk.Label(header, image=icon_img, bg=self.widgets.bg_color).pack(side="left")
        else:
            tk.Label(
                header,
                text="🔐",
                font=("Segoe UI", 20),
                bg=self.widgets.bg_color,
                fg=self.widgets.accent_color,
            ).pack(side="left")

        tk.Label(
            header,
            text="BIGestPwd",
            font=("Segoe UI", 18, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(side="left", padx=10)

        if self.user_profile:
            p_text = self.user_profile["display_name"]
            if self.user_profile["is_anonymous"]:
                p_text += " 🕶️"
            tk.Label(
                header,
                text="👤",
                font=("Segoe UI", 14),
                bg=self.widgets.bg_color,
                fg=self.widgets.accent_color,
            ).pack(side="left", padx=(20, 5))
            tk.Label(
                header,
                text=p_text,
                font=("Segoe UI", 10, "bold"),
                bg=self.widgets.bg_color,
                fg=self.widgets.text_secondary,
            ).pack(side="left")

        btn_frame = tk.Frame(header, bg=self.widgets.bg_color)
        btn_frame.pack(side="right")

        self.btn_settings = self.widgets.create_modern_button(
            btn_frame, "⚙️", self.show_settings_menu, self.widgets.card_bg, width=4
        )
        self.btn_settings.pack(side="left", padx=(0, 5))

        self.btn_update = self.widgets.create_modern_button(
            btn_frame, "🔄 Actualizar", self.check_update, self.widgets.accent_color
        )
        self.btn_update.pack(side="left", padx=5)
        self.widgets.create_modern_button(
            btn_frame, "🔒 Cerrar Sesión", self.logout, self.widgets.danger_color
        ).pack(side="left", padx=5)

    def show_settings_menu(self):
        current_time = time.time() * 1000
        if current_time - self.last_menu_close_time < 300:
            return

        menu = Menu(
            self.root,
            tearoff=0,
            bg=self.widgets.card_bg,
            fg="white",
            activebackground=self.widgets.accent_color,
            activeforeground="white",
            font=("Segoe UI", 10),
        )

        def get_lbl(text, key):
            state = "🟢 ON" if self.settings[key] else "⚪ OFF"
            return f"{text}   [{state}]"

        menu.add_command(
            label=get_lbl("🚀 Iniciar con Windows", "start_with_windows"),
            command=lambda: self.toggle_setting("start_with_windows"),
        )

        menu.add_command(
            label=get_lbl("❌ Minimizar al Cerrar", "minimize_to_tray"),
            command=lambda: self.toggle_setting("minimize_to_tray"),
        )

        menu.add_command(
            label=get_lbl("⏱️ Bloqueo Auto (AFK)", "afk_lock"),
            command=lambda: self.toggle_setting("afk_lock"),
        )

        menu.add_command(
            label=get_lbl("🧹 Limpiar Portapapeles", "clean_clipboard"),
            command=lambda: self.toggle_setting("clean_clipboard"),
        )

        menu.add_separator()

        menu.add_command(
            label=get_lbl("👁️ Modo Confidencial", "privacy_mode"),
            command=lambda: self.toggle_setting("privacy_mode"),
        )

        try:
            x = self.btn_settings.winfo_rootx()
            y = self.btn_settings.winfo_rooty() + self.btn_settings.winfo_height()

            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
            self.last_menu_close_time = time.time() * 1000

    def toggle_setting(self, key):
        new_val = not self.settings[key]
        self.settings[key] = new_val
        self.save_settings()

        if key == "start_with_windows":
            WindowHelper.manage_windows_startup(new_val)
        elif key == "privacy_mode":
            WindowHelper.set_display_affinity(self.root, new_val)

        self.root.after(50, self.show_settings_menu)

    def create_passwords_tab(self):
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="📁 Contraseñas")

        card = self.widgets.create_card(tab)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        top_frame = tk.Frame(card, bg=self.widgets.card_bg)
        top_frame.pack(fill="x", padx=15, pady=15)
        top_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            top_frame,
            text="🔍 Buscar:",
            font=("Segoe UI", 10, "bold"),
            bg=self.widgets.card_bg,
            fg="white",
        ).grid(row=0, column=0, padx=(0, 10))
        self.search_var = tk.StringVar()
        search_entry = self.widgets.create_styled_entry(top_frame, self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", ipady=5)
        search_entry.bind("<KeyRelease>", self.on_search_change)

        tk.Label(
            top_frame,
            text="📂 Categoría:",
            font=("Segoe UI", 10, "bold"),
            bg=self.widgets.card_bg,
            fg="white",
        ).grid(row=0, column=2, padx=(20, 10))
        self.category_var = tk.StringVar(value="Todas")
        self.category_combo = ttk.Combobox(
            top_frame, textvariable=self.category_var, state="readonly", width=15
        )
        self.category_combo.grid(row=0, column=3, sticky="e", ipady=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        action_frame = tk.Frame(card, bg=self.widgets.card_bg)
        action_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.edit_btn = self.widgets.create_modern_button(
            action_frame, "✏️ Editar/Ver", self.edit_show_selected_password, "#6b7280"
        )
        self.edit_btn.pack(side="left", padx=5)
        self.edit_btn.config(state="disabled")

        self.del_btn = self.widgets.create_modern_button(
            action_frame, "🗑️ Eliminar", self.delete_selected_password, "#6b7280"
        )
        self.del_btn.pack(side="left", padx=5)
        self.del_btn.config(state="disabled")

        tree_frame = tk.Frame(card, bg=self.widgets.card_bg)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        cols = ("Status", "Categoría", "Título", "Notas")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)

        self.tree.heading("Status", text="Status")
        self.tree.heading("Categoría", text="Categoría")
        self.tree.heading("Título", text="Título")
        self.tree.heading("Notas", text="Notas")
        self.tree.column("Status", width=60, anchor="center")
        self.tree.column("Categoría", width=150, anchor="center")
        self.tree.column("Título", width=250, anchor="center")
        self.tree.column("Notas", width=300, anchor="center")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Motion>", self.on_tree_hover)

    def on_tree_hover(self, event):
        region = self.tree.identify_region(event.x, event.y)

        if region == "cell":
            col = self.tree.identify_column(event.x)
            row_id = self.tree.identify_row(event.y)

            if col == "#1" and row_id:
                item_tags = self.tree.item(row_id, "tags")
                if item_tags:
                    db_id = int(item_tags[0])

                    if db_id in self.password_health_data:
                        data = self.password_health_data[db_id]
                        self.tooltip.show_tip(
                            data["title"], data["messages"], event.x_root, event.y_root
                        )
                        return

        self.tooltip.hide_tip()

    def create_add_tab(self):
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="➕ Añadir")

        card = self.widgets.create_card(tab)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            card,
            text="Nueva Contraseña",
            font=("Segoe UI", 16, "bold"),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack(pady=20)

        form = tk.Frame(card, bg=self.widgets.card_bg)
        form.pack(fill="both", expand=True, padx=40)
        form.grid_columnconfigure(1, weight=1)

        self.form_entries = {}
        lbl_style = {
            "font": ("Segoe UI", 10, "bold"),
            "bg": self.widgets.card_bg,
            "fg": self.widgets.text_secondary,
            "anchor": "w",
        }

        tk.Label(form, text="Categoría:", **lbl_style).grid(
            row=0, column=0, pady=10, sticky="w"
        )
        cat_combo = ttk.Combobox(form, state="readonly")
        cat_combo.grid(row=0, column=1, sticky="ew", ipady=5)
        self.form_entries["category"] = cat_combo

        tk.Label(form, text="Título:", **lbl_style).grid(
            row=1, column=0, pady=10, sticky="w"
        )
        title_ent = self.widgets.create_styled_entry(form)
        title_ent.grid(row=1, column=1, sticky="ew", ipady=5)
        self.form_entries["title"] = title_ent

        tk.Label(form, text="Usuario/Email:", **lbl_style).grid(
            row=2, column=0, pady=10, sticky="w"
        )
        user_ent = self.widgets.create_styled_entry(form)
        user_ent.grid(row=2, column=1, sticky="ew", ipady=5)
        self.form_entries["username"] = user_ent

        tk.Label(form, text="Contraseña:", **lbl_style).grid(
            row=3, column=0, pady=10, sticky="w"
        )
        pwd_frame = tk.Frame(form, bg=self.widgets.card_bg)
        pwd_frame.grid(row=3, column=1, sticky="ew")
        pwd_frame.grid_columnconfigure(0, weight=1)

        pwd_ent = self.widgets.create_styled_entry(pwd_frame, show="•")
        pwd_ent.grid(row=0, column=0, sticky="ew", ipady=5)
        self.form_entries["password"] = pwd_ent

        tools = tk.Frame(pwd_frame, bg=self.widgets.card_bg)
        tools.grid(row=0, column=1, padx=(5, 0))
        self.widgets.create_modern_button(
            tools,
            "🎲",
            lambda: self.open_password_generator(pwd_ent),
            self.widgets.accent_color,
            width=4,
        ).pack(side="left", padx=2)
        self.widgets.create_modern_button(
            tools,
            "⌨️",
            lambda: self.virtual_kb.create_keyboard(pwd_ent),
            self.widgets.warning_color,
            width=4,
        ).pack(side="left", padx=2)

        tk.Label(form, text="URL:", **lbl_style).grid(
            row=4, column=0, pady=10, sticky="w"
        )
        url_ent = self.widgets.create_styled_entry(form)
        url_ent.grid(row=4, column=1, sticky="ew", ipady=5)
        self.form_entries["url"] = url_ent

        tk.Label(form, text="Notas:", **lbl_style).grid(
            row=5, column=0, pady=10, sticky="nw"
        )
        notes_ent = tk.Text(
            form,
            height=4,
            bg="#2d2d2d",
            fg="white",
            relief="flat",
            bd=1,
            font=("Segoe UI", 10),
        )
        notes_ent.grid(row=5, column=1, sticky="ew", pady=10)
        self.form_entries["notes"] = notes_ent

        self.widgets.create_modern_button(
            card,
            "💾 Guardar Contraseña",
            self.save_password,
            self.widgets.success_color,
            width=20,
        ).pack(pady=20)

    def create_security_tab(self):
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="🔒 Seguridad")
        center_frame = tk.Frame(tab, bg=self.widgets.bg_color)
        center_frame.pack(fill="both", expand=True, padx=40, pady=20)

        tk.Label(
            center_frame,
            text="Gestión de Seguridad",
            font=("Segoe UI", 20, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        ).pack(pady=(0, 20))
        self.create_sec_option(
            center_frame,
            "🔑 Llave Maestra",
            "Cambia tu contraseña principal",
            "Cambiar Contraseña",
            self.open_change_master_password,
        )
        self.create_sec_option(
            center_frame,
            "💾 Bypass USB",
            f"Gestiona tus llaves físicas ({len(self.usb.get_authorized_devices())}/2)",
            "Gestionar USBs",
            self.open_usb_management,
        )
        self.create_sec_option(
            center_frame,
            "📱 Autenticación TOTP",
            "Configura Google Authenticator",
            "Gestionar 2FA",
            self.open_totp_management,
        )

    def create_about_tab(self):
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="ℹ️ Acerca de")
        card = self.widgets.create_card(tab)
        card.pack(expand=True, fill="both", padx=60, pady=40)
        center = tk.Frame(card, bg=self.widgets.card_bg)
        center.pack(expand=True)

        icon_img = self.widgets.get_icon_image(size=(100, 100))
        if icon_img:
            self.widgets.image_cache["about_icon"] = icon_img
            tk.Label(center, image=icon_img, bg=self.widgets.card_bg).pack(pady=(0, 15))
        else:
            tk.Label(
                center,
                text="🛡️",
                font=("Segoe UI", 64),
                bg=self.widgets.card_bg,
                fg=self.widgets.accent_color,
            ).pack(pady=(0, 15))

        tk.Label(
            center,
            text="BIGestPwd 2.8.1",
            font=("Segoe UI", 24, "bold"),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack()
        tk.Label(
            center,
            text="Gestor de Contraseñas Seguro",
            font=("Segoe UI", 12),
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
        ).pack(pady=(5, 20))
        tk.Frame(center, bg=self.widgets.text_secondary, height=2, width=200).pack(
            pady=10
        )
        tk.Label(
            center,
            text="Created by LoremRoman",
            font=("Segoe UI", 11),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack(pady=(10, 5))

        tagline = "Secure. Open Source. Free. Always."
        tk.Label(
            center,
            text=tagline,
            font=("Consolas", 11, "italic"),
            bg=self.widgets.card_bg,
            fg=self.widgets.accent_color,
        ).pack(pady=10)

        repo_url = "https://github.com/LoremRoman/BIGestPwd"

        def open_repo():
            webbrowser.open(repo_url)

        self.widgets.create_modern_button(
            center,
            "🌐 Visitar Repositorio",
            open_repo,
            self.widgets.accent_color,
            width=20,
        ).pack(pady=20)
        tk.Label(
            center,
            text="© 2025 LoremRoman. MIT License.",
            font=("Segoe UI", 9),
            bg=self.widgets.card_bg,
            fg="#666",
        ).pack(side="bottom", pady=20)

    def create_sec_option(self, parent, title, desc, btn_text, command):
        card = self.widgets.create_card(parent)
        card.pack(fill="x", pady=10)
        inner = tk.Frame(card, bg=self.widgets.card_bg, padx=20, pady=15)
        inner.pack(fill="both", expand=True)
        info = tk.Frame(inner, bg=self.widgets.card_bg)
        info.pack(side="left", fill="both", expand=True)
        tk.Label(
            info,
            text=title,
            font=("Segoe UI", 14, "bold"),
            bg=self.widgets.card_bg,
            fg="white",
        ).pack(anchor="w")
        tk.Label(
            info,
            text=desc,
            font=("Segoe UI", 10),
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
        ).pack(anchor="w")
        self.widgets.create_modern_button(
            inner, btn_text, command, self.widgets.accent_color, width=18
        ).pack(side="right")

    def create_status_bar(self):
        status = tk.Frame(self.root, bg=self.widgets.card_bg, height=25)
        status.pack(side="bottom", fill="x")
        txt = "Listo • Modo Seguro"
        if self.user_profile:
            txt = f"Conectado como: {self.user_profile['display_name']} • {txt}"
        self.status_label = tk.Label(
            status,
            text=txt,
            font=("Segoe UI", 9),
            bg=self.widgets.card_bg,
            fg=self.widgets.text_secondary,
        )
        self.status_label.pack(side="left", padx=10)

    def check_update(self):
        updater = AppUpdater(
            self.root,
            on_start_check=lambda: self.btn_update.config(
                state="disabled", text="🔄 Buscando..."
            ),
            on_finish_check=lambda: self.btn_update.config(
                state="normal", text="🔄 Actualizar"
            ),
        )
        updater.check_for_updates()

    def load_categories(self):
        cats = db_manager.get_categories()
        names = ["Todas"] + [c["name"] for c in cats]
        self.category_combo["values"] = names
        if "category" in self.form_entries:
            self.form_entries["category"]["values"] = [c["name"] for c in cats]
            if cats:
                self.form_entries["category"].set(cats[0]["name"])

    def load_passwords(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        self.password_health_data.clear()

        entries = db_manager.get_password_entries(self.master_password)
        search = self.current_search.lower()
        cat = self.category_var.get()

        count = 0
        for e in entries:
            if search and (
                search not in e["title"].lower() and search not in str(e["url"]).lower()
            ):
                continue
            if cat != "Todas" and e["category"] != cat:
                continue

            color_code, status_title, messages = PasswordHealth.calculate_status(
                e["password"], e["date_for_check"]
            )

            note_preview = e["notes"].replace("\n", " ") if e["notes"] else ""
            if len(note_preview) > 30:
                note_preview = note_preview[:30] + "..."

            self.password_health_data[e["id"]] = {
                "title": status_title,
                "messages": messages,
            }

            item_id = self.tree.insert(
                "",
                "end",
                values=("●", e["category"], e["title"], note_preview),
                tags=(str(e["id"]),),
            )

            tag_name = f"status_{e['id']}"
            self.tree.item(item_id, tags=(str(e["id"]), tag_name))
            self.tree.tag_configure(tag_name, foreground=color_code)

            count += 1

        self.update_status(f"Mostrando {count} contraseñas")
        self.disable_context_buttons()

    def on_search_change(self, e):
        self.current_search = self.search_var.get()
        self.load_passwords()

    def on_category_change(self, e):
        self.load_passwords()

    def on_tree_select(self, e):
        sel = self.tree.selection()
        if sel:
            self.selected_item = sel[0]
            self.enable_context_buttons()
        else:
            self.disable_context_buttons()

    def enable_context_buttons(self):
        self.edit_btn.config(state="normal", bg=self.widgets.accent_color)
        self.del_btn.config(state="normal", bg=self.widgets.danger_color)

    def disable_context_buttons(self):
        self.edit_btn.config(state="disabled", bg="#6b7280")
        self.del_btn.config(state="disabled", bg="#6b7280")

    def save_password(self):
        cat = self.form_entries["category"].get()
        title = self.form_entries["title"].get()
        user = self.form_entries["username"].get()
        pwd = self.form_entries["password"].get()
        url = self.form_entries["url"].get()
        notes = self.form_entries["notes"].get("1.0", tk.END).strip()

        if not all([cat, title, pwd]):
            WindowHelper.show_custom_message(
                self.root,
                "Faltan Datos",
                "Categoría, Título y Contraseña son obligatorios",
                is_error=True,
            )
            return

        cats = db_manager.get_categories()
        cat_id = next((c["id"] for c in cats if c["name"] == cat), None)

        if db_manager.add_password_entry(
            cat_id, title, user, pwd, url, notes, self.master_password
        ):
            WindowHelper.show_custom_message(
                self.root, "Guardado", "Contraseña guardada correctamente"
            )
            self.clear_form()
            self.load_passwords()
            self.notebook.select(0)
        else:
            WindowHelper.show_custom_message(
                self.root, "Error", "No se pudo guardar", is_error=True
            )

    def clear_form(self):
        self.form_entries["title"].delete(0, tk.END)
        self.form_entries["username"].delete(0, tk.END)
        self.form_entries["password"].delete(0, tk.END)
        self.form_entries["url"].delete(0, tk.END)
        self.form_entries["notes"].delete("1.0", tk.END)

    def open_password_generator(self, entry):
        def set_pwd(p):
            entry.delete(0, tk.END)
            entry.insert(0, p)

        PasswordGeneratorModal(self.root, set_pwd)

    def edit_show_selected_password(self):
        if not self.selected_item:
            return
        id_ = self.tree.item(self.selected_item, "tags")[0]
        entries = db_manager.get_password_entries(self.master_password)
        data = next((e for e in entries if e["id"] == int(id_)), None)
        if data:
            PasswordEditModal(
                self.root, data, self.master_password, self.load_passwords
            )

    def delete_selected_password(self):
        if not self.selected_item:
            return

        id_str = self.tree.item(self.selected_item, "tags")[0]
        id_ = int(id_str)
        entries = db_manager.get_password_entries(self.master_password)
        entry_data = next((e for e in entries if e["id"] == id_), None)

        title_to_show = entry_data["title"] if entry_data else "esta contraseña"

        if messagebox.askyesno(
            "Eliminar",
            f"¿Estás seguro de eliminar '{title_to_show}'?",
            parent=self.root,
        ):
            if db_manager.delete_password_entry(id_):
                self.load_passwords()
                WindowHelper.show_custom_message(
                    self.root, "Eliminado", "Contraseña eliminada correctamente"
                )
            else:
                WindowHelper.show_custom_message(
                    self.root, "Error", "No se pudo eliminar", is_error=True
                )

    def open_change_master_password(self):
        PasswordChangeModal(self.root, self.master_password, self.on_master_changed)

    def on_master_changed(self, new_pwd):
        self.master_password = new_pwd
        self.load_passwords()

    def open_usb_management(self):
        def refresh_app():
            for widget in self.root.winfo_children():
                widget.destroy()
            self.create_interface()
            self.load_categories()
            self.load_passwords()

        USBManagementModal(self.root, self.master_password, refresh_app)

    def open_totp_management(self):
        TOTPManagementModal(self.root, self.master_password)

    def update_status(self, msg):
        if hasattr(self, "status_label") and self.status_label:
            self.status_label.config(text=f"Estado: {msg}")

    def logout(self):
        self.master_password = ""
        if self.on_logout_callback:
            self.on_logout_callback()
        else:
            self.root.quit()
