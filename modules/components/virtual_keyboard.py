import tkinter as tk
import subprocess
import os
from modules.utils.helpers import WindowHelper
from modules.components.widgets import ModernWidgets  # ✅ Importamos los estilos

class VirtualKeyboard:
    def __init__(self, parent):
        self.parent = parent
        self.widgets = ModernWidgets()  # ✅ Iniciamos los estilos
    
    def create_keyboard(self, target_entry):
        """Abre el teclado virtual nativo de Windows de forma segura"""
        try:
            if os.name == 'nt':
                # Intenta varios métodos para abrir el teclado en Windows
                try:
                    # Método 1: Ruta directa (funciona en la mayoría de 64bits)
                    if os.path.exists('C:\\Windows\\System32\\osk.exe'):
                        subprocess.Popen('C:\\Windows\\System32\\osk.exe', shell=True)
                    else:
                        # Método 2: Comando directo
                        os.system('start osk')
                except:
                    # Método 3: Fallback básico
                    os.system('start osk')
            else:
                self.show_custom_message("Sistema no compatible", 
                                      "El teclado virtual automático solo está disponible en Windows.\n\n"
                                      "Por favor, ábrelo manualmente en tu sistema.")
        except Exception as e:
            # Fallback manual con instrucciones claras
            self.show_custom_message("No se pudo abrir automáticamente", 
                                  "Para abrir el Teclado en Pantalla manualmente:\n\n"
                                  "1. Presiona la tecla Windows + R\n"
                                  "2. Escribe 'osk' y presiona Enter\n" 
                                  "3. O busca 'Teclado en pantalla' en el menú Inicio")
    
    def show_custom_message(self, title, message):
        """Muestra un mensaje estilizado con ModernWidgets"""
        msg_window = tk.Toplevel(self.parent)
        msg_window.title(title)
        msg_window.configure(bg=self.widgets.bg_color) # ✅ Color consistente
        
        # Tamaño dinámico pero contenido
        msg_window.minsize(400, 250)
        msg_window.transient(self.parent)
        
        # Frame con padding
        main_frame = tk.Frame(msg_window, bg=self.widgets.bg_color, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        WindowHelper.center_window(msg_window, 400, 250)
        
        # Icono
        tk.Label(
            main_frame,
            text="⌨️",
            font=('Segoe UI', 32),
            bg=self.widgets.bg_color,
            fg=self.widgets.accent_color
        ).pack(pady=(10, 15))
        
        # Mensaje
        tk.Label(
            main_frame,
            text=message,
            font=('Segoe UI', 10),
            bg=self.widgets.bg_color,
            fg='white',
            wraplength=350,
            justify='center'
        ).pack(pady=10)
        
        # Botón con estilo moderno
        self.widgets.create_modern_button(
            main_frame,
            "Entendido",
            msg_window.destroy,
            self.widgets.accent_color,
            width=15
        ).pack(pady=15)