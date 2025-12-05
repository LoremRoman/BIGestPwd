import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os


class ModernWidgets:
    def __init__(self):
        self.bg_color = "#0a0a0a"
        self.card_bg = "#1a1a1a"
        self.input_bg = "#2d2d2d"
        self.accent_color = "#3b82f6"
        self.success_color = "#10b981"
        self.danger_color = "#ef4444"
        self.warning_color = "#f59e0b"
        self.text_primary = "#ffffff"
        self.text_secondary = "#94a3b8"
        self.image_cache = {}

    def get_icon_image(self, size=(32, 32)):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            icon_path = os.path.join(base_path, "icon.ico")

            if not os.path.exists(icon_path):
                icon_path = "icon.ico"

            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                return photo
            return None
        except Exception as e:
            print(f"No se pudo cargar la imagen del icono: {e}")
            return None

    def create_modern_button(self, parent, text, command, color, width=None, height=1):
        btn_config = {
            "text": text,
            "command": command,
            "bg": color,
            "fg": "white",
            "activebackground": self.adjust_brightness(color, 0.8),
            "activeforeground": "white",
            "font": ("Segoe UI", 9, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 15,
            "pady": 6,
            "cursor": "hand2",
            "height": height,
        }
        if width:
            btn_config["width"] = width

        btn = tk.Button(parent, **btn_config)

        def on_enter(e):
            if btn["state"] == "normal":
                btn["bg"] = self.adjust_brightness(color, 1.2)

        def on_leave(e):
            if btn["state"] == "normal":
                btn["bg"] = color

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def create_card(self, parent):
        return tk.Frame(parent, bg=self.card_bg)

    def create_styled_entry(self, parent, var=None, show=None):
        return tk.Entry(
            parent,
            textvariable=var,
            font=("Segoe UI", 10),
            bg=self.input_bg,
            fg=self.text_primary,
            insertbackground=self.text_primary,
            relief="flat",
            bd=1,
            show=show,
        )

    def adjust_brightness(self, hex_color, factor):
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=self.card_bg,
            foreground=self.text_primary,
            fieldbackground=self.card_bg,
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=35,
        )
        style.configure(
            "Treeview.Heading",
            background="#2d2d2d",
            foreground=self.text_primary,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padding=[5, 10],
        )
        style.map("Treeview.Heading", background=[("active", "#374151")])
        style.map(
            "Treeview",
            background=[("selected", self.accent_color)],
            foreground=[("selected", "white")],
        )

        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background="#2d2d2d",
            darkcolor="#1a1a1a",
            lightcolor="#1a1a1a",
            troughcolor="#0a0a0a",
            bordercolor="#1a1a1a",
            arrowcolor="white",
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", "#404040"), ("disabled", "#1a1a1a")],
        )
        return style
