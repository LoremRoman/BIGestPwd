import tkinter as tk
from modules.components.widgets import ModernWidgets

class WindowHelper:
    @staticmethod
    def center_window(window, width, height):
        """Centra una ventana en la pantalla de forma inteligente"""
        window.update_idletasks()
        
        # Obtener dimensiones de pantalla
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calcular posición x, y
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Asegurar que no quede fuera de pantalla (por barras de tareas)
        if y < 0: y = 50
        
        window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def show_custom_message(parent, title, message, is_error=False):
        """Muestra un mensaje modal personalizado con estilo moderno"""
        widgets = ModernWidgets() # Instanciar estilos
        
        msg_window = tk.Toplevel(parent)
        msg_window.title(title)
        msg_window.configure(bg=widgets.bg_color)
        
        # No definimos geometría fija, usamos minsize y dejamos que se adapte
        msg_window.minsize(380, 200)
        msg_window.resizable(False, False)
        msg_window.transient(parent)
        msg_window.grab_set() # Hacer modal (bloquea la ventana padre)
        
        # Frame principal con padding
        main_frame = tk.Frame(msg_window, bg=widgets.bg_color, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Configurar colores e icono
        icon = "❌" if is_error else "✅"
        icon_color = widgets.danger_color if is_error else widgets.success_color
        btn_color = widgets.danger_color if is_error else widgets.accent_color
        
        # Icono grande
        tk.Label(
            main_frame,
            text=icon,
            font=('Segoe UI', 32),
            bg=widgets.bg_color,
            fg=icon_color
        ).pack(pady=(10, 15))
        
        # Mensaje
        tk.Label(
            main_frame,
            text=message,
            font=('Segoe UI', 11),
            bg=widgets.bg_color,
            fg='white',
            wraplength=340,
            justify='center'
        ).pack(pady=(0, 20))
        
        # Botón Aceptar usando el estilo moderno
        widgets.create_modern_button(
            main_frame,
            "Aceptar",
            msg_window.destroy,
            btn_color,
            width=15
        ).pack(pady=10)
        
        # Centrar después de renderizar para calcular tamaño real
        msg_window.update_idletasks()
        width = msg_window.winfo_reqwidth()
        height = msg_window.winfo_reqheight()
        WindowHelper.center_window(msg_window, width, height)
        
        # Enfocar y esperar
        msg_window.focus_force()
        return msg_window