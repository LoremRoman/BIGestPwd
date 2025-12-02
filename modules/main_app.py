import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser  # ✅ NUEVO: Para abrir links
from modules.encryption import db_manager
from modules.components.virtual_keyboard import VirtualKeyboard
from modules.components.modals import PasswordGeneratorModal, PasswordEditModal
from modules.components.security_modals import PasswordChangeModal, USBManagementModal, TOTPManagementModal
from modules.components.widgets import ModernWidgets
from modules.utils.helpers import WindowHelper
from modules.auth.multi_factor import MultiFactorAuth
from modules.auth.totp_offline import TOTPOffline
from modules.auth.usb_bypass import USBBypass

class MainApplication:
    def __init__(self, root, master_password):
        self.root = root
        self.master_password = master_password
        self.virtual_kb = VirtualKeyboard(root)
        self.widgets = ModernWidgets()
        self.mfa = MultiFactorAuth()
        self.totp = TOTPOffline()
        self.usb = USBBypass()
        
        # DEBUG
        print(f"🔐 [MAIN_APP DEBUG] Contraseña recibida. Longitud: {len(master_password)}")
        
        self.current_search = ""
        self.selected_item = None
        
        self.user_profile = self.mfa.get_user_profile()
        
        # Configurar ventana
        self.root.title("BIGestPwd 2.3 - Gestor Principal")
        self.root.configure(bg=self.widgets.bg_color)
        
        # Cargar icono ventana principal si existe
        try: self.root.iconbitmap("icon.ico")
        except: pass
        
        # Setup inicial
        self.setup_styles()
        self.create_interface()
        self.load_categories()
        self.load_passwords()
    
    def setup_styles(self):
        """Configura estilos modernos"""
        self.style = self.widgets.setup_treeview_style()
        
        # Estilo para Notebook (Pestañas)
        self.style.configure('TNotebook', background=self.widgets.bg_color, borderwidth=0)
        self.style.configure('TNotebook.Tab', 
                           background=self.widgets.bg_color,
                           foreground=self.widgets.text_secondary,
                           padding=[15, 8],
                           font=('Segoe UI', 10, 'bold'))
        self.style.map('TNotebook.Tab', 
                      background=[('selected', self.widgets.card_bg)], # Color activo
                      foreground=[('selected', self.widgets.accent_color)])
    
    def create_interface(self):
        """Crea la interfaz principal"""
        # 1. Header
        self.create_header()
        
        # 2. Notebook Container
        main_container = tk.Frame(self.root, bg=self.widgets.bg_color)
        main_container.pack(fill='both', expand=True, padx=15, pady=10)
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # 3. Pestañas
        self.create_passwords_tab()
        self.create_add_tab()
        self.create_security_tab()
        self.create_about_tab()  # ✅ NUEVA PESTAÑA
        
        # 4. Status Bar
        self.create_status_bar()
    
    def create_header(self):
        """Encabezado superior"""
        header = tk.Frame(self.root, bg=self.widgets.bg_color, height=60)
        header.pack(fill='x', padx=20, pady=10)
        
        # Logo (Imagen o Emoji)
        icon_img = self.widgets.get_icon_image(size=(40, 40))
        if icon_img:
            self.widgets.image_cache['header_icon'] = icon_img
            tk.Label(header, image=icon_img, bg=self.widgets.bg_color).pack(side='left')
        else:
            tk.Label(header, text="🔐", font=('Segoe UI', 20), bg=self.widgets.bg_color, fg=self.widgets.accent_color).pack(side='left')
            
        tk.Label(header, text="BIGestPwd 2.3", font=('Segoe UI', 18, 'bold'), bg=self.widgets.bg_color, fg='white').pack(side='left', padx=10)
        
        # Perfil
        if self.user_profile:
            p_text = self.user_profile['display_name']
            if self.user_profile['is_anonymous']: p_text += " 🕶️"
            
            tk.Label(header, text="👤", font=('Segoe UI', 14), bg=self.widgets.bg_color, fg=self.widgets.accent_color).pack(side='left', padx=(20, 5))
            tk.Label(header, text=p_text, font=('Segoe UI', 10, 'bold'), bg=self.widgets.bg_color, fg=self.widgets.text_secondary).pack(side='left')

        # Botones Header
        btn_frame = tk.Frame(header, bg=self.widgets.bg_color)
        btn_frame.pack(side='right')
        
        self.widgets.create_modern_button(btn_frame, "🔄 Actualizar", self.load_passwords, self.widgets.accent_color).pack(side='left', padx=5)
        self.widgets.create_modern_button(btn_frame, "🔒 Cerrar Sesión", self.logout, self.widgets.danger_color).pack(side='left', padx=5)

    def create_passwords_tab(self):
        """Pestaña de lista de contraseñas"""
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="📁 Contraseñas")
        
        card = self.widgets.create_card(tab)
        card.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Filtros
        top_frame = tk.Frame(card, bg=self.widgets.card_bg)
        top_frame.pack(fill='x', padx=15, pady=15)
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Buscar
        tk.Label(top_frame, text="🔍 Buscar:", font=('Segoe UI', 10, 'bold'), bg=self.widgets.card_bg, fg='white').grid(row=0, column=0, padx=(0, 10))
        self.search_var = tk.StringVar()
        search_entry = self.widgets.create_styled_entry(top_frame, self.search_var)
        search_entry.grid(row=0, column=1, sticky='ew', ipady=5)
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Categoría
        tk.Label(top_frame, text="📂 Categoría:", font=('Segoe UI', 10, 'bold'), bg=self.widgets.card_bg, fg='white').grid(row=0, column=2, padx=(20, 10))
        self.category_var = tk.StringVar(value="Todas")
        self.category_combo = ttk.Combobox(top_frame, textvariable=self.category_var, state='readonly', width=15)
        self.category_combo.grid(row=0, column=3, sticky='e', ipady=5)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        # Botones Acción
        action_frame = tk.Frame(card, bg=self.widgets.card_bg)
        action_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        self.edit_btn = self.widgets.create_modern_button(action_frame, "✏️ Editar/Ver", self.edit_show_selected_password, '#6b7280')
        self.edit_btn.pack(side='left', padx=5)
        self.edit_btn.config(state='disabled')
        
        self.del_btn = self.widgets.create_modern_button(action_frame, "🗑️ Eliminar", self.delete_selected_password, '#6b7280')
        self.del_btn.pack(side='left', padx=5)
        self.del_btn.config(state='disabled')
        
        # Treeview
        tree_frame = tk.Frame(card, bg=self.widgets.card_bg)
        tree_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        cols = ('Categoría', 'Título', 'URL')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10)
        
        self.tree.heading('Categoría', text='Categoría')
        self.tree.heading('Título', text='Título')
        self.tree.heading('URL', text='URL')
        
        self.tree.column('Categoría', width=150, anchor='center')
        self.tree.column('Título', width=300, anchor='w')
        self.tree.column('URL', width=250, anchor='w')
        
        sb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def create_add_tab(self):
        """Pestaña añadir contraseña"""
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="➕ Añadir")
        
        card = self.widgets.create_card(tab)
        card.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(card, text="Nueva Contraseña", font=('Segoe UI', 16, 'bold'), 
                 bg=self.widgets.card_bg, fg='white').pack(pady=20)
        
        form = tk.Frame(card, bg=self.widgets.card_bg)
        form.pack(fill='both', expand=True, padx=40)
        form.grid_columnconfigure(1, weight=1)
        
        self.form_entries = {}
        
        lbl_style = {'font': ('Segoe UI', 10, 'bold'), 'bg': self.widgets.card_bg, 'fg': self.widgets.text_secondary, 'anchor': 'w'}
        
        tk.Label(form, text="Categoría:", **lbl_style).grid(row=0, column=0, pady=10, sticky='w')
        cat_combo = ttk.Combobox(form, state='readonly')
        cat_combo.grid(row=0, column=1, sticky='ew', ipady=5)
        self.form_entries['category'] = cat_combo
        
        tk.Label(form, text="Título:", **lbl_style).grid(row=1, column=0, pady=10, sticky='w')
        title_ent = self.widgets.create_styled_entry(form)
        title_ent.grid(row=1, column=1, sticky='ew', ipady=5)
        self.form_entries['title'] = title_ent
        
        tk.Label(form, text="Usuario/Email:", **lbl_style).grid(row=2, column=0, pady=10, sticky='w')
        user_ent = self.widgets.create_styled_entry(form)
        user_ent.grid(row=2, column=1, sticky='ew', ipady=5)
        self.form_entries['username'] = user_ent
        
        tk.Label(form, text="Contraseña:", **lbl_style).grid(row=3, column=0, pady=10, sticky='w')
        pwd_frame = tk.Frame(form, bg=self.widgets.card_bg)
        pwd_frame.grid(row=3, column=1, sticky='ew')
        pwd_frame.grid_columnconfigure(0, weight=1)
        
        pwd_ent = self.widgets.create_styled_entry(pwd_frame, show='•')
        pwd_ent.grid(row=0, column=0, sticky='ew', ipady=5)
        self.form_entries['password'] = pwd_ent
        
        tools = tk.Frame(pwd_frame, bg=self.widgets.card_bg)
        tools.grid(row=0, column=1, padx=(5, 0))
        self.widgets.create_modern_button(tools, "🎲", lambda: self.open_password_generator(pwd_ent), self.widgets.accent_color, width=4).pack(side='left', padx=2)
        self.widgets.create_modern_button(tools, "⌨️", lambda: self.virtual_kb.create_keyboard(pwd_ent), self.widgets.warning_color, width=4).pack(side='left', padx=2)
        
        tk.Label(form, text="URL:", **lbl_style).grid(row=4, column=0, pady=10, sticky='w')
        url_ent = self.widgets.create_styled_entry(form)
        url_ent.grid(row=4, column=1, sticky='ew', ipady=5)
        self.form_entries['url'] = url_ent
        
        tk.Label(form, text="Notas:", **lbl_style).grid(row=5, column=0, pady=10, sticky='nw')
        notes_ent = tk.Text(form, height=4, bg='#2d2d2d', fg='white', relief='flat', bd=1, font=('Segoe UI', 10))
        notes_ent.grid(row=5, column=1, sticky='ew', pady=10)
        self.form_entries['notes'] = notes_ent
        
        self.widgets.create_modern_button(
            card, "💾 Guardar Contraseña", self.save_password, self.widgets.success_color, width=20
        ).pack(pady=20)

    def create_security_tab(self):
        """Pestaña de seguridad"""
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="🔒 Seguridad")
        
        center_frame = tk.Frame(tab, bg=self.widgets.bg_color)
        center_frame.pack(fill='both', expand=True, padx=40, pady=20)
        
        tk.Label(center_frame, text="Gestión de Seguridad", font=('Segoe UI', 20, 'bold'), 
                 bg=self.widgets.bg_color, fg='white').pack(pady=(0, 20))
        
        self.create_sec_option(center_frame, "🔑 Llave Maestra", "Cambia tu contraseña principal", 
                             "Cambiar Contraseña", self.open_change_master_password)
        
        self.create_sec_option(center_frame, "💾 Bypass USB", f"Gestiona tus llaves físicas ({len(self.usb.get_authorized_devices())}/2)", 
                             "Gestionar USBs", self.open_usb_management)
        
        self.create_sec_option(center_frame, "📱 Autenticación TOTP", "Configura Google Authenticator", 
                             "Gestionar 2FA", self.open_totp_management)

    def create_about_tab(self):
        """Pestaña Acerca De (NUEVA)"""
        tab = tk.Frame(self.notebook, bg=self.widgets.bg_color)
        self.notebook.add(tab, text="ℹ️ Acerca de")
        
        # Tarjeta Central
        card = self.widgets.create_card(tab)
        card.pack(expand=True, fill='both', padx=60, pady=40)
        
        # Contenido centrado
        center = tk.Frame(card, bg=self.widgets.card_bg)
        center.pack(expand=True)
        
        # Logo Grande
        icon_img = self.widgets.get_icon_image(size=(100, 100))
        if icon_img:
            self.widgets.image_cache['about_icon'] = icon_img
            tk.Label(center, image=icon_img, bg=self.widgets.card_bg).pack(pady=(0, 15))
        else:
            tk.Label(center, text="🛡️", font=('Segoe UI', 64), bg=self.widgets.card_bg, fg=self.widgets.accent_color).pack(pady=(0, 15))
            
        tk.Label(center, text="BIGestPwd 2.3", font=('Segoe UI', 24, 'bold'), bg=self.widgets.card_bg, fg='white').pack()
        tk.Label(center, text="Gestor de Contraseñas Seguro", font=('Segoe UI', 12), bg=self.widgets.card_bg, fg=self.widgets.text_secondary).pack(pady=(5, 20))
        
        # Separador
        tk.Frame(center, bg=self.widgets.text_secondary, height=2, width=200).pack(pady=10)
        
        # Créditos y Eslogan
        tk.Label(center, text="Created by LoremRoman", font=('Segoe UI', 11), bg=self.widgets.card_bg, fg='white').pack(pady=(10, 5))
        
        # Eslogan con estilo
        tagline = "Secure. Open Source. Free. Always."
        tk.Label(center, text=tagline, font=('Consolas', 11, 'italic'), bg=self.widgets.card_bg, fg=self.widgets.accent_color).pack(pady=10)
        
        # Botón Repositorio
        repo_url = "https://github.com/LoremRoman/BIGestPwd" # Puedes poner tu URL real aquí
        def open_repo():
            webbrowser.open(repo_url)
            
        self.widgets.create_modern_button(
            center, "🌐 Visitar Repositorio", open_repo, self.widgets.accent_color, width=20
        ).pack(pady=20)
        
        # Copyright
        tk.Label(center, text="© 2025 LoremRoman. MIT License.", font=('Segoe UI', 9), bg=self.widgets.card_bg, fg='#666').pack(side='bottom', pady=20)

    def create_sec_option(self, parent, title, desc, btn_text, command):
        card = self.widgets.create_card(parent)
        card.pack(fill='x', pady=10)
        
        inner = tk.Frame(card, bg=self.widgets.card_bg, padx=20, pady=15)
        inner.pack(fill='both', expand=True)
        
        info = tk.Frame(inner, bg=self.widgets.card_bg)
        info.pack(side='left', fill='both', expand=True)
        
        tk.Label(info, text=title, font=('Segoe UI', 14, 'bold'), bg=self.widgets.card_bg, fg='white').pack(anchor='w')
        tk.Label(info, text=desc, font=('Segoe UI', 10), bg=self.widgets.card_bg, fg=self.widgets.text_secondary).pack(anchor='w')
        
        self.widgets.create_modern_button(inner, btn_text, command, self.widgets.accent_color, width=18).pack(side='right')

    def create_status_bar(self):
        status = tk.Frame(self.root, bg=self.widgets.card_bg, height=25)
        status.pack(side='bottom', fill='x')
        
        txt = "Listo • Modo Seguro"
        if self.user_profile: txt = f"Conectado como: {self.user_profile['display_name']} • {txt}"
        
        self.status_label = tk.Label(status, text=txt, font=('Segoe UI', 9), bg=self.widgets.card_bg, fg=self.widgets.text_secondary)
        self.status_label.pack(side='left', padx=10)

    # --- Lógica de negocio ---
    
    def load_categories(self):
        cats = db_manager.get_categories()
        names = ['Todas'] + [c['name'] for c in cats]
        self.category_combo['values'] = names
        if 'category' in self.form_entries:
            self.form_entries['category']['values'] = [c['name'] for c in cats]
            if cats: self.form_entries['category'].set(cats[0]['name'])

    def load_passwords(self):
        # Limpiar
        for i in self.tree.get_children(): self.tree.delete(i)
        
        entries = db_manager.get_password_entries(self.master_password)
        search = self.current_search.lower()
        cat = self.category_var.get()
        
        count = 0
        for e in entries:
            if search and (search not in e['title'].lower() and search not in str(e['url']).lower()):
                continue
            if cat != "Todas" and e['category'] != cat:
                continue
                
            self.tree.insert('', 'end', values=(e['category'], e['title'], e['url'] or ''), tags=(e['id'],))
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
        self.edit_btn.config(state='normal', bg=self.widgets.accent_color)
        self.del_btn.config(state='normal', bg=self.widgets.danger_color)

    def disable_context_buttons(self):
        self.edit_btn.config(state='disabled', bg='#6b7280')
        self.del_btn.config(state='disabled', bg='#6b7280')

    def save_password(self):
        # Obtener datos
        cat = self.form_entries['category'].get()
        title = self.form_entries['title'].get()
        user = self.form_entries['username'].get()
        pwd = self.form_entries['password'].get()
        url = self.form_entries['url'].get()
        notes = self.form_entries['notes'].get("1.0", tk.END).strip()
        
        if not all([cat, title, pwd]):
            WindowHelper.show_custom_message(self.root, "Faltan Datos", "Categoría, Título y Contraseña son obligatorios", is_error=True)
            return
            
        # Obtener ID categoría
        cats = db_manager.get_categories()
        cat_id = next((c['id'] for c in cats if c['name'] == cat), None)
        
        if db_manager.add_password_entry(cat_id, title, user, pwd, url, notes, self.master_password):
            WindowHelper.show_custom_message(self.root, "Guardado", "Contraseña guardada correctamente")
            self.clear_form()
            self.load_passwords()
            self.notebook.select(0) # Ir a lista
        else:
            WindowHelper.show_custom_message(self.root, "Error", "No se pudo guardar", is_error=True)

    def clear_form(self):
        self.form_entries['title'].delete(0, tk.END)
        self.form_entries['username'].delete(0, tk.END)
        self.form_entries['password'].delete(0, tk.END)
        self.form_entries['url'].delete(0, tk.END)
        self.form_entries['notes'].delete("1.0", tk.END)

    def open_password_generator(self, entry):
        def set_pwd(p):
            entry.delete(0, tk.END)
            entry.insert(0, p)
        PasswordGeneratorModal(self.root, set_pwd)

    def edit_show_selected_password(self):
        if not self.selected_item: return
        id_ = self.tree.item(self.selected_item, 'tags')[0]
        entries = db_manager.get_password_entries(self.master_password)
        data = next((e for e in entries if e['id'] == int(id_)), None)
        
        if data:
            PasswordEditModal(self.root, data, self.master_password, self.load_passwords)

    def delete_selected_password(self):
        if not self.selected_item: return
        id_ = int(self.tree.item(self.selected_item, 'tags')[0])
        title = self.tree.item(self.selected_item, 'values')[1]
        
        # Usar messagebox importado correctamente
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{title}'?", parent=self.root):
            if db_manager.delete_password_entry(id_):
                self.load_passwords()
                WindowHelper.show_custom_message(self.root, "Eliminado", "Contraseña eliminada")
            else:
                WindowHelper.show_custom_message(self.root, "Error", "No se pudo eliminar", is_error=True)

    def open_change_master_password(self):
        PasswordChangeModal(self.root, self.master_password, self.on_master_changed)

    def on_master_changed(self, new_pwd):
        self.master_password = new_pwd
        self.load_passwords() # Recargar con nueva clave

    def open_usb_management(self):
        USBManagementModal(self.root, self.master_password, lambda: self.create_interface()) 

    def open_totp_management(self):
        TOTPManagementModal(self.root, self.master_password)

    def update_status(self, msg):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"Estado: {msg}")

    def logout(self):
        self.master_password = ""
        for w in self.root.winfo_children(): w.destroy()
        self.root.quit()