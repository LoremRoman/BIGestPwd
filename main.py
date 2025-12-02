import tkinter as tk
from tkinter import ttk
import os
from modules.auth_system_new import LoginSystemNew as LoginSystem
from modules.encryption import db_manager
from modules.main_app import MainApplication
from modules.components.virtual_keyboard import VirtualKeyboard
from modules.utils.helpers import WindowHelper
from modules.auth.multi_factor import MultiFactorAuth
from modules.components.widgets import ModernWidgets

class BIGestPwdApp:
    def __init__(self):
        self.root = tk.Tk()
        self.master_password = ""
        self.widgets = ModernWidgets()
        self.virtual_kb = VirtualKeyboard(self.root)
        self.mfa = MultiFactorAuth()
        self.setup_app()
    
    def setup_app(self):
        """Configura la aplicación principal"""
        self.root.title("BIGestPwd 2.3")
        self.root.configure(bg=self.widgets.bg_color)
        
        self.root.geometry("550x700")
        self.root.minsize(500, 600)
        WindowHelper.center_window(self.root, 550, 700)
        
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"No se pudo cargar el icono: {e}")
            pass
            
        self.check_first_run()
    
    def check_first_run(self):
        if not db_manager.is_master_configured():
            self.show_first_time_setup()
        else:
            mfa_status = self.mfa.get_mfa_status()
            configured_methods = sum([1 for m in mfa_status.values() if m.get('configured', False)])
            if configured_methods < 2:
                self.show_mfa_setup()
            else:
                self.show_login()
    
    def show_first_time_setup(self):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg=self.widgets.bg_color)
        main_frame.pack(fill='both', expand=True, padx=40, pady=40)
        center_container = tk.Frame(main_frame, bg=self.widgets.bg_color)
        center_container.pack(expand=True, fill='both')
        
        # --- ICONO GRANDE ---
        icon_img = self.widgets.get_icon_image(size=(100, 100)) # Tamaño más grande para bienvenida
        if icon_img:
            self.widgets.image_cache['welcome_icon'] = icon_img
            tk.Label(center_container, image=icon_img, bg=self.widgets.bg_color).pack(pady=(0, 10))
        else:
            tk.Label(center_container, text="🔐", font=('Segoe UI', 48), bg=self.widgets.bg_color, fg=self.widgets.accent_color).pack(pady=(0, 10))
            
        tk.Label(center_container, text="Bienvenido a BIGestPwd", font=('Segoe UI', 24, 'bold'), bg=self.widgets.bg_color, fg='white').pack()
        tk.Label(center_container, text="Tu fortaleza digital personal", font=('Segoe UI', 12), bg=self.widgets.bg_color, fg=self.widgets.text_secondary).pack(pady=(5, 30))
        
        card = tk.Frame(center_container, bg=self.widgets.card_bg, padx=30, pady=30)
        card.pack(fill='x')
        tk.Label(card, text="Configurar Llave Maestra", font=('Segoe UI', 14, 'bold'), bg=self.widgets.card_bg, fg='white').pack(pady=(0, 20))
        
        tk.Label(card, text="Nueva Contraseña Maestra:", font=('Segoe UI', 10, 'bold'), bg=self.widgets.card_bg, fg=self.widgets.text_secondary, anchor='w').pack(fill='x', pady=(0, 5))
        self.master_entry = self.widgets.create_styled_entry(card, show='•')
        self.master_entry.pack(fill='x', ipady=6, pady=(0, 15))
        self.master_entry.focus()
        
        tk.Label(card, text="Confirmar Contraseña:", font=('Segoe UI', 10, 'bold'), bg=self.widgets.card_bg, fg=self.widgets.text_secondary, anchor='w').pack(fill='x', pady=(0, 5))
        self.confirm_entry = self.widgets.create_styled_entry(card, show='•')
        self.confirm_entry.pack(fill='x', ipady=6, pady=(0, 20))
        
        def setup_master():
            master_pwd = self.master_entry.get()
            confirm_pwd = self.confirm_entry.get()
            
            if len(master_pwd) < 8:
                WindowHelper.show_custom_message(self.root, "Seguridad Débil", "Mínimo 8 caracteres requeridos", is_error=True)
                return
            if master_pwd != confirm_pwd:
                WindowHelper.show_custom_message(self.root, "Error", "Las contraseñas no coinciden", is_error=True)
                return
            
            if db_manager.configure_master_password(master_pwd):
                self.master_password = master_pwd
                self.show_mfa_setup()
            else:
                WindowHelper.show_custom_message(self.root, "Error fatal", "No se pudo guardar la configuración", is_error=True)

        self.widgets.create_modern_button(card, "🚀 Comenzar Configuración", setup_master, self.widgets.success_color, width=25).pack(fill='x', pady=5)
        self.widgets.create_modern_button(card, "⌨️ Teclado Virtual", lambda: self.virtual_kb.create_keyboard(self.master_entry), self.widgets.accent_color).pack(fill='x', pady=5)
        self.master_entry.bind('<Return>', lambda e: setup_master())
        self.confirm_entry.bind('<Return>', lambda e: setup_master())

    def show_mfa_setup(self):
        self.clear_window()
        from modules.components.mfa_setup import MFASetupWizard
        self.root.geometry("900x700")
        WindowHelper.center_window(self.root, 900, 700)
        self.mfa_wizard = MFASetupWizard(self.root, self.master_password, on_complete_callback=self.on_mfa_setup_complete)
    
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
    
    def show_main_interface(self):
        self.clear_window()
        width = 1100
        height = 750
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2 - 30
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.state('normal')
        self.main_app = MainApplication(self.root, self.master_password)
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = BIGestPwdApp()
    app.root.mainloop()