import tkinter as tk
from tkinter import ttk, messagebox
from modules.encryption import db_manager, encryption_system
from modules.components.virtual_keyboard import VirtualKeyboard
from modules.utils.helpers import WindowHelper
from modules.auth.multi_factor import MultiFactorAuth
from modules.auth.totp_offline import TOTPOffline
from modules.auth.usb_bypass import USBBypass
from modules.components.widgets import ModernWidgets
from PIL import Image, ImageTk
import io
import sqlite3

class PasswordChangeModal:
    def __init__(self, parent, master_password, on_success_callback=None):
        self.parent = parent
        self.current_master_password = master_password
        self.on_success_callback = on_success_callback
        self.widgets = ModernWidgets()
        self.virtual_kb = VirtualKeyboard(parent)
        self.totp = TOTPOffline()
        self.create_modal()

    def create_modal(self):
        self.modal = tk.Toplevel(self.parent)
        self.modal.title("🔑 Cambiar Llave Maestra")
        self.modal.configure(bg=self.widgets.bg_color)
        
        try: self.modal.iconbitmap("icon.ico")
        except: pass
        
        self.modal.minsize(500, 600)
        self.modal.resizable(True, True)
        self.modal.transient(self.parent)
        self.modal.grab_set()
        
        main_frame = tk.Frame(self.modal, bg=self.widgets.bg_color, padx=30, pady=30)
        main_frame.pack(fill='both', expand=True)
        tk.Label(main_frame, text="🔑 Cambiar Llave Maestra", font=('Segoe UI', 18, 'bold'), bg=self.widgets.bg_color, fg='white').pack(pady=(0, 10))
        tk.Label(main_frame, text="Esta acción re-encriptará todas tus contraseñas.", font=('Segoe UI', 10), bg=self.widgets.bg_color, fg=self.widgets.text_secondary).pack(pady=(0, 20))
        
        form_frame = tk.Frame(main_frame, bg=self.widgets.bg_color)
        form_frame.pack(fill='both', expand=True)
        form_frame.grid_columnconfigure(1, weight=1)
        lbl_style = {'font': ('Segoe UI', 10, 'bold'), 'bg': self.widgets.bg_color, 'fg': 'white', 'anchor': 'w'}
        
        tk.Label(form_frame, text="Actual:", **lbl_style).grid(row=0, column=0, pady=10, sticky='w')
        self.current_password_var = tk.StringVar()
        curr_entry = self.widgets.create_styled_entry(form_frame, var=self.current_password_var, show='•')
        curr_entry.grid(row=0, column=1, sticky='ew', ipady=5, padx=(10, 5))
        curr_entry.focus()
        self.widgets.create_modern_button(form_frame, "⌨️", lambda: self.virtual_kb.create_keyboard(curr_entry), self.widgets.accent_color, width=4).grid(row=0, column=2)

        tk.Frame(form_frame, bg='#333', height=1).grid(row=1, column=0, columnspan=3, sticky='ew', pady=15)

        tk.Label(form_frame, text="Nueva:", **lbl_style).grid(row=2, column=0, pady=10, sticky='w')
        self.new_password_var = tk.StringVar()
        new_entry = self.widgets.create_styled_entry(form_frame, var=self.new_password_var, show='•')
        new_entry.grid(row=2, column=1, sticky='ew', ipady=5, padx=(10, 5))
        self.widgets.create_modern_button(form_frame, "⌨️", lambda: self.virtual_kb.create_keyboard(new_entry), self.widgets.accent_color, width=4).grid(row=2, column=2)

        tk.Label(form_frame, text="Confirmar:", **lbl_style).grid(row=3, column=0, pady=10, sticky='w')
        self.confirm_password_var = tk.StringVar()
        conf_entry = self.widgets.create_styled_entry(form_frame, var=self.confirm_password_var, show='•')
        conf_entry.grid(row=3, column=1, sticky='ew', ipady=5, padx=(10, 5))

        self.strength_label = tk.Label(main_frame, text="Fortaleza: --", font=('Segoe UI', 9), bg=self.widgets.bg_color, fg=self.widgets.text_secondary)
        self.strength_label.pack(anchor='w', pady=(5, 20))
        
        self.current_password_var.trace('w', lambda *args: self.validate_form())
        self.new_password_var.trace('w', self.validate_password_strength)
        self.confirm_password_var.trace('w', self.validate_password_match)

        btn_frame = tk.Frame(main_frame, bg=self.widgets.bg_color)
        btn_frame.pack(fill='x', side='bottom', pady=10)
        self.change_btn = self.widgets.create_modern_button(btn_frame, "🔄 Re-encriptar Todo", self.change_master_password, self.widgets.success_color, width=20)
        self.change_btn.pack(side='right', padx=5)
        self.change_btn.config(state='disabled', bg='#4b5563')
        self.widgets.create_modern_button(btn_frame, "Cancelar", self.modal.destroy, self.widgets.text_secondary).pack(side='right', padx=5)

        self.modal.update_idletasks()
        WindowHelper.center_window(self.modal, self.modal.winfo_reqwidth(), self.modal.winfo_reqheight())

    def validate_password_strength(self, *args):
        password = self.new_password_var.get()
        if not password:
            self.strength_label.config(text="Fortaleza: --", fg=self.widgets.text_secondary)
            return
        strength = 0
        if len(password) >= 8: strength += 1
        if any(c.islower() for c in password): strength += 1
        if any(c.isupper() for c in password): strength += 1
        if any(c.isdigit() for c in password): strength += 1
        if any(not c.isalnum() for c in password): strength += 1
        if strength <= 2: self.strength_label.config(text="Fortaleza: Débil", fg=self.widgets.danger_color)
        elif strength <= 4: self.strength_label.config(text="Fortaleza: Media", fg=self.widgets.warning_color)
        else: self.strength_label.config(text="Fortaleza: Fuerte", fg=self.widgets.success_color)
        self.validate_form()

    def validate_password_match(self, *args):
        new_p = self.new_password_var.get()
        conf_p = self.confirm_password_var.get()
        if new_p and conf_p:
            if new_p == conf_p: self.strength_label.config(text="✅ Contraseñas coinciden", fg=self.widgets.success_color)
            else: self.strength_label.config(text="❌ No coinciden", fg=self.widgets.danger_color)
        self.validate_form()

    def validate_form(self):
        curr = self.current_password_var.get()
        new_p = self.new_password_var.get()
        conf_p = self.confirm_password_var.get()
        valid = bool(curr.strip()) and len(new_p) >= 8 and new_p == conf_p and new_p != curr
        if valid: self.change_btn.config(state='normal', bg=self.widgets.success_color)
        else: self.change_btn.config(state='disabled', bg='#4b5563')

    def change_master_password(self):
        current_password = self.current_password_var.get()
        new_password = self.new_password_var.get()
        if not db_manager.verify_master_password(current_password):
            WindowHelper.show_custom_message(self.modal, "Error", "Contraseña actual incorrecta", is_error=True)
            return
        if current_password == new_password:
            WindowHelper.show_custom_message(self.modal, "Error", "La nueva contraseña debe ser diferente", is_error=True)
            return
        if messagebox.askyesno("Confirmar Re-encriptación", "Esto re-encriptará TODAS tus contraseñas.\n¿Estás seguro?", parent=self.modal):
            self.execute_password_change(current_password, new_password)

    def execute_password_change(self, current_password, new_password):
        self.change_btn.config(text="⏳ Procesando...", state='disabled')
        self.modal.update()
        success = self.update_master_password_and_data(current_password, new_password)
        if success:
            WindowHelper.show_custom_message(self.parent, "Éxito", "Llave maestra actualizada.\nUsa la nueva contraseña la próxima vez.")
            if self.on_success_callback: self.on_success_callback(new_password)
            self.modal.destroy()
        else:
            WindowHelper.show_custom_message(self.modal, "Error", "Error crítico al cambiar la llave", is_error=True)
            self.change_btn.config(text="🔄 Re-encriptar Todo", state='normal')

    def update_master_password_and_data(self, old_password, new_password):
        try:
            # 1. Verificar contraseña actual
            if not db_manager.verify_master_password(old_password): 
                print("❌ Contraseña antigua inválida")
                return False
            
            # 2. Obtener datos
            entries = db_manager.get_password_entries(old_password)
            
            # 3. TOTP
            if self.totp.is_configured(): 
                self.totp.reencrypt_secret(old_password, new_password)
            
            # 4. Generar nuevo hash maestro
            new_master_hash, new_master_salt = encryption_system.hash_master_password(new_password)
            
            # ✅ CORRECCIÓN: Usar la ruta dinámica desde db_manager
            with sqlite3.connect(db_manager.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                
                # Actualizar config maestra
                cursor.execute("UPDATE master_config SET master_hash = ?, master_salt = ?", (new_master_hash, new_master_salt))
                
                # Re-encriptar entradas
                for entry in entries:
                    enc_pwd, pwd_salt = encryption_system.encrypt_data(entry['password'], new_password)
                    enc_notes, notes_salt = (None, None)
                    if entry['notes']: 
                        enc_notes, notes_salt = encryption_system.encrypt_data(entry['notes'], new_password)
                    
                    cursor.execute('''
                        UPDATE password_entries 
                        SET encrypted_password = ?, password_salt = ?, notes = ?, notes_salt = ? 
                        WHERE id = ?
                    ''', (enc_pwd, pwd_salt, enc_notes, notes_salt, entry['id']))
                
                conn.commit()
            
            return True
        except Exception as e:
            print(f"❌ Error crítico actualizando DB: {e}")
            import traceback
            traceback.print_exc()
            return False

class USBManagementModal:
    def __init__(self, parent, master_password, on_success_callback=None):
        self.parent = parent
        self.master_password = master_password
        self.on_success_callback = on_success_callback
        self.widgets = ModernWidgets()
        self.usb = USBBypass()
        self.create_modal()
    
    def create_modal(self):
        self.modal = tk.Toplevel(self.parent)
        self.modal.title("💾 Gestión USB")
        self.modal.configure(bg=self.widgets.bg_color)
        try: self.modal.iconbitmap("icon.ico")
        except: pass
        self.modal.geometry("600x650")
        self.modal.transient(self.parent)
        self.modal.grab_set()
        main_frame = tk.Frame(self.modal, bg=self.widgets.bg_color, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        tk.Label(main_frame, text="💾 Llaves USB", font=('Segoe UI', 18, 'bold'), bg=self.widgets.bg_color, fg='white').pack(pady=(0, 10))
        list_frame = tk.Frame(main_frame, bg=self.widgets.card_bg)
        list_frame.pack(fill='both', expand=True, pady=10)
        canvas = tk.Canvas(list_frame, bg=self.widgets.card_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.usb_list_container = tk.Frame(canvas, bg=self.widgets.card_bg)
        self.usb_list_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.usb_list_container, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        btn_frame = tk.Frame(main_frame, bg=self.widgets.bg_color)
        btn_frame.pack(fill='x', pady=10)
        self.add_btn = self.widgets.create_modern_button(btn_frame, "➕ Añadir USB", self.add_new_usb, self.widgets.success_color)
        self.add_btn.pack(side='right')
        self.widgets.create_modern_button(btn_frame, "Cerrar", self.modal.destroy, self.widgets.text_secondary).pack(side='right', padx=10)
        self.load_usb_list()
        WindowHelper.center_window(self.modal, 600, 650)

    def load_usb_list(self):
        for widget in self.usb_list_container.winfo_children(): widget.destroy()
        devices = self.usb.get_authorized_devices()
        if not devices:
            tk.Label(self.usb_list_container, text="No hay llaves configuradas", bg=self.widgets.card_bg, fg=self.widgets.text_secondary, font=('Segoe UI', 11)).pack(pady=20)
        else:
            for device in devices: self.create_usb_card(device)
        if len(devices) >= 2: self.add_btn.config(state='disabled', bg='#4b5563')
        else: self.add_btn.config(state='normal', bg=self.widgets.success_color)

    def create_usb_card(self, device):
        card = tk.Frame(self.usb_list_container, bg='#2d2d2d', pady=10, padx=10)
        card.pack(fill='x', pady=5, padx=5)
        tk.Label(card, text=f"💾 {device['name']}", font=('Segoe UI', 11, 'bold'), bg='#2d2d2d', fg='white').pack(side='left')
        tk.Label(card, text=f"({device['created_at'][:10]})", font=('Segoe UI', 9), bg='#2d2d2d', fg='#9ca3af').pack(side='left', padx=10)
        self.widgets.create_modern_button(card, "🗑️", lambda d=device: self.delete_usb_device(d), self.widgets.danger_color, width=4).pack(side='right')

    def delete_usb_device(self, device):
        if messagebox.askyesno("Eliminar USB", f"¿Revocar acceso a '{device['name']}'?", parent=self.modal):
            success, msg = self.usb.remove_usb_device(device['uuid'], device['name'])
            if success:
                self.load_usb_list()
                if self.on_success_callback: self.on_success_callback()
            else:
                WindowHelper.show_custom_message(self.modal, "Error", msg, is_error=True)

    def add_new_usb(self):
        USBSetupModal(self.modal, self.master_password, on_success_callback=self.on_usb_added)

    def on_usb_added(self):
        self.load_usb_list()
        if self.on_success_callback: self.on_success_callback()

class TOTPManagementModal:
    def __init__(self, parent, master_password, on_success_callback=None):
        self.parent = parent
        self.master_password = master_password
        self.on_success_callback = on_success_callback
        self.widgets = ModernWidgets()
        self.totp = TOTPOffline()
        self.create_modal()

    def create_modal(self):
        self.modal = tk.Toplevel(self.parent)
        self.modal.title("📱 Autenticación Móvil")
        self.modal.configure(bg=self.widgets.bg_color)
        try: self.modal.iconbitmap("icon.ico")
        except: pass
        self.modal.geometry("450x400")
        self.modal.transient(self.parent)
        self.modal.grab_set()
        main_frame = tk.Frame(self.modal, bg=self.widgets.bg_color, padx=30, pady=30)
        main_frame.pack(fill='both', expand=True)
        tk.Label(main_frame, text="📱 Authenticator", font=('Segoe UI', 18, 'bold'), bg=self.widgets.bg_color, fg='white').pack(pady=(0, 20))
        is_conf = self.totp.is_configured()
        status_txt = "✅ Activado" if is_conf else "❌ Desactivado"
        status_col = self.widgets.success_color if is_conf else self.widgets.danger_color
        tk.Label(main_frame, text=status_txt, font=('Segoe UI', 14), bg=self.widgets.bg_color, fg=status_col).pack(pady=20)
        if is_conf:
            self.widgets.create_modern_button(main_frame, "🔄 Mostrar Código QR", self.regenerate_qr, self.widgets.accent_color, width=20).pack(pady=10)
        else:
            self.widgets.create_modern_button(main_frame, "➕ Configurar Ahora", self.setup_totp, self.widgets.success_color, width=20).pack(pady=10)
        self.widgets.create_modern_button(main_frame, "Cerrar", self.modal.destroy, self.widgets.text_secondary).pack(side='bottom', pady=10)
        WindowHelper.center_window(self.modal, 450, 400)

    def regenerate_qr(self):
        try:
            secret = self.totp.get_secret(self.master_password)
            if not secret: raise Exception("No se pudo desencriptar el secreto")
            mfa = MultiFactorAuth()
            user = mfa.get_user_profile().get('display_name', "Usuario")
            qr_img, _ = self.totp.generate_qr_code(secret, user)
            if qr_img: TOTPQRModal(self.modal, qr_img)
        except Exception as e:
            WindowHelper.show_custom_message(self.modal, "Error", str(e), is_error=True)

    def setup_totp(self):
        from modules.components.mfa_setup import MFASetupWizard
        def on_done():
            self.modal.destroy()
            if self.on_success_callback: self.on_success_callback()
        w = MFASetupWizard(self.modal, self.master_password, on_complete_callback=on_done)
        w.show_step(2)

class TOTPQRModal:
    def __init__(self, parent, qr_image, title="Escanea este código"):
        self.widgets = ModernWidgets()
        self.modal = tk.Toplevel(parent)
        self.modal.title(title)
        self.modal.configure(bg=self.widgets.bg_color)
        try: self.modal.iconbitmap("icon.ico")
        except: pass
        
        main = tk.Frame(self.modal, bg=self.widgets.bg_color, padx=20, pady=20)
        main.pack(fill='both', expand=True)
        
        try:
            img = Image.open(io.BytesIO(qr_image))
            img = img.resize((300, 300))
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(main, image=photo, bg=self.widgets.bg_color)
            lbl.image = photo
            lbl.pack(pady=10)
        except:
            tk.Label(main, text="Error imagen", bg=self.widgets.bg_color, fg='red').pack()
            
        tk.Label(main, text="Escanea con Google Authenticator", bg=self.widgets.bg_color, fg='white').pack(pady=10)
        self.widgets.create_modern_button(main, "Listo", self.modal.destroy, self.widgets.success_color).pack()
        WindowHelper.center_window(self.modal, 400, 500)

class USBSetupModal:
    def __init__(self, parent, master_password, on_success_callback=None):
        self.parent = parent
        self.master_password = master_password
        self.on_success_callback = on_success_callback
        self.widgets = ModernWidgets()
        self.usb = USBBypass()
        self.modal = tk.Toplevel(parent)
        self.modal.title("🔍 Escáner USB")
        self.modal.configure(bg=self.widgets.bg_color)
        try: self.modal.iconbitmap("icon.ico")
        except: pass
        self.modal.geometry("500x500")
        self.modal.transient(parent)
        self.modal.grab_set()
        main = tk.Frame(self.modal, bg=self.widgets.bg_color, padx=20, pady=20)
        main.pack(fill='both', expand=True)
        tk.Label(main, text="Conecta tu USB", font=('Segoe UI', 16, 'bold'), bg=self.widgets.bg_color, fg='white').pack(pady=10)
        self.list_frame = tk.Frame(main, bg=self.widgets.card_bg)
        self.list_frame.pack(fill='both', expand=True, pady=10)
        btn_frame = tk.Frame(main, bg=self.widgets.bg_color)
        btn_frame.pack(fill='x')
        self.scan_btn = self.widgets.create_modern_button(btn_frame, "🔄 Escanear", self.scan, self.widgets.accent_color)
        self.scan_btn.pack(side='left', expand=True, fill='x', padx=5)
        self.widgets.create_modern_button(btn_frame, "Cancelar", self.modal.destroy, self.widgets.text_secondary).pack(side='left', padx=5)
        WindowHelper.center_window(self.modal, 500, 500)

    def scan(self):
        self.scan_btn.config(text="Buscando...", state='disabled')
        self.modal.update()
        for w in self.list_frame.winfo_children(): w.destroy()
        try:
            connected = self.usb.detect_real_usb_devices()
            authorized = [d['uuid'] for d in self.usb.get_authorized_devices()]
            available = [d for d in connected if self.usb.get_usb_uuid(d['path']) not in authorized]
            if not available:
                tk.Label(self.list_frame, text="No se encontraron USBs nuevos", bg=self.widgets.card_bg, fg=self.widgets.text_secondary).pack(pady=20)
            else:
                for dev in available:
                    f = tk.Frame(self.list_frame, bg='#2d2d2d', pady=5, padx=5)
                    f.pack(fill='x', pady=2)
                    tk.Label(f, text=f"{dev['name']} ({dev['size_gb']}GB)", bg='#2d2d2d', fg='white').pack(side='left')
                    self.widgets.create_modern_button(f, "Seleccionar", lambda d=dev: self.configure(d), self.widgets.success_color, width=10).pack(side='right')
        except Exception as e:
            tk.Label(self.list_frame, text=f"Error: {e}", fg='red', bg=self.widgets.card_bg).pack()
        self.scan_btn.config(text="🔄 Escanear", state='normal')

    def configure(self, device):
        res, msg = self.usb.register_usb_device(device['name'], device['path'], self.master_password)
        if res:
            if self.on_success_callback: self.on_success_callback()
            self.modal.destroy()
        else:
            WindowHelper.show_custom_message(self.modal, "Error", msg, is_error=True)

class SecurityVerificationModal:
    def __init__(self, parent, operation_name, master_password):
        self.parent = parent
        self.operation_name = operation_name
        self.master_password = master_password
        self.verified = False
        self.widgets = ModernWidgets()
        self.create_modal()
    
    def create_modal(self):
        self.modal = tk.Toplevel(self.parent)
        self.modal.title("🔒 Verificación de Seguridad")
        self.modal.configure(bg=self.widgets.bg_color)
        try: self.modal.iconbitmap("icon.ico")
        except: pass
        self.modal.geometry("450x350")
        self.modal.resizable(False, False)
        self.modal.transient(self.parent)
        self.modal.grab_set()
        main_frame = tk.Frame(self.modal, bg=self.widgets.bg_color, padx=30, pady=30)
        main_frame.pack(fill='both', expand=True)
        tk.Label(main_frame, text="🔒", font=('Segoe UI', 32), bg=self.widgets.bg_color, fg=self.widgets.accent_color).pack(pady=(0, 10))
        tk.Label(main_frame, text="Verificación Requerida", font=('Segoe UI', 16, 'bold'), bg=self.widgets.bg_color, fg='white').pack(pady=(0, 10))
        tk.Label(main_frame, text=f"Estás a punto de: {self.operation_name}", font=('Segoe UI', 11), bg=self.widgets.bg_color, fg=self.widgets.text_secondary, wraplength=350).pack(pady=(0, 20))
        btn_frame = tk.Frame(main_frame, bg=self.widgets.bg_color)
        btn_frame.pack(fill='x', pady=10)
        self.widgets.create_modern_button(btn_frame, "Cancelar", self.cancel_operation, self.widgets.text_secondary).pack(side='left', padx=10)
        self.widgets.create_modern_button(btn_frame, "✅ Confirmar", self.verify_identity, self.widgets.success_color).pack(side='right', padx=10)
        WindowHelper.center_window(self.modal, 450, 350)

    def cancel_operation(self):
        self.verified = False
        self.modal.destroy()
    
    def verify_identity(self):
        self.verified = True
        self.modal.destroy()