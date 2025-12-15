import tkinter as tk
from tkinter import ttk
import requests
import os
import sys
import subprocess
import threading
import tempfile
from packaging import version
from modules.components.widgets import ModernWidgets
from modules.utils.helpers import WindowHelper
from modules.config import APP_VERSION as CURRENT_VERSION, REPO_OWNER, REPO_NAME


class AppUpdater:
    def __init__(self, root, on_start_check=None, on_finish_check=None):
        self.root = root
        self.widgets = ModernWidgets()
        self.api_url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        )
        self.on_start = on_start_check
        self.on_finish = on_finish_check
        self.modal = None
        self.progress_bar = None
        self.status_label = None
        self.info_label = None
        self.btn_frame = None

    def check_for_updates(self):
        if self.on_start:
            self.on_start()

        self._create_update_modal()
        threading.Thread(target=self._check_logic, daemon=True).start()

    def _create_update_modal(self):
        self.modal = tk.Toplevel(self.root)
        self.modal.title("Actualización del Sistema")
        self.modal.configure(bg=self.widgets.bg_color)
        self.modal.geometry("400x250")
        self.modal.resizable(False, False)
        self.modal.transient(self.root)
        self.modal.grab_set()
        WindowHelper.center_window(self.modal, 400, 250)

        self.modal.protocol("WM_DELETE_WINDOW", self._close_cleanly)

        tk.Label(
            self.modal,
            text="🚀",
            font=("Segoe UI", 40),
            bg=self.widgets.bg_color,
            fg=self.widgets.accent_color,
        ).pack(pady=(20, 10))

        self.status_label = tk.Label(
            self.modal,
            text="Buscando actualizaciones...",
            font=("Segoe UI", 12, "bold"),
            bg=self.widgets.bg_color,
            fg="white",
        )
        self.status_label.pack(pady=(0, 5))

        self.info_label = tk.Label(
            self.modal,
            text=f"Versión actual: {CURRENT_VERSION}",
            font=("Segoe UI", 9),
            bg=self.widgets.bg_color,
            fg=self.widgets.text_secondary,
        )
        self.info_label.pack(pady=(0, 15))

        style = ttk.Style()
        try:
            style.configure(
                "Green.Horizontal.TProgressbar",
                background=self.widgets.success_color,
                troughcolor=self.widgets.card_bg,
                borderwidth=0,
            )
        except:
            pass

        self.progress_bar = ttk.Progressbar(
            self.modal,
            orient="horizontal",
            length=300,
            mode="indeterminate",
            style="Green.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.start(10)

        self.btn_frame = tk.Frame(self.modal, bg=self.widgets.bg_color)
        self.btn_frame.pack(pady=10, fill="x")

    def _check_logic(self):
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code != 200:
                self.root.after(
                    0, lambda: self._update_ui_state("error", "Error de conexión")
                )
                return

            data = response.json()
            latest_tag = data.get("tag_name", "0.0").replace("v", "")

            if version.parse(latest_tag) > version.parse(CURRENT_VERSION):
                exe_url = self._get_exe_url(data)
                if exe_url:
                    self.root.after(
                        0,
                        lambda: self._update_ui_state(
                            "found", f"¡Nueva versión {latest_tag} disponible!", exe_url
                        ),
                    )
                else:
                    self.root.after(
                        0,
                        lambda: self._update_ui_state(
                            "error", "Actualización detectada sin ejecutable."
                        ),
                    )
            else:
                self.root.after(0, lambda: self._update_ui_state("uptodate"))

        except Exception as e:
            self.root.after(
                0, lambda: self._update_ui_state("error", f"Error: {str(e)}")
            )

        finally:
            if self.on_finish:
                self.root.after(0, self.on_finish)

    def _get_exe_url(self, data):
        for asset in data.get("assets", []):
            if asset["name"].endswith(".exe"):
                return asset["browser_download_url"]
        return None

    def _update_ui_state(self, state, message="", extra_data=None):
        if not self.modal or not self.modal.winfo_exists():
            return

        if state == "uptodate":
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(
                text="Todo está actualizado", fg=self.widgets.success_color
            )
            self.info_label.config(
                text=f"Ya tienes la versión más reciente ({CURRENT_VERSION})"
            )

            self.widgets.create_modern_button(
                self.btn_frame,
                "Aceptar",
                self._close_cleanly,
                self.widgets.accent_color,
                width=15,
            ).pack()

        elif state == "error":
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(
                text="Ups, algo salió mal", fg=self.widgets.danger_color
            )
            self.info_label.config(text=message)

            self.widgets.create_modern_button(
                self.btn_frame,
                "Cerrar",
                self._close_cleanly,
                self.widgets.card_bg,
                width=15,
            ).pack()

        elif state == "found":
            self.progress_bar.stop()
            self.progress_bar.config(mode="determinate", value=0)
            self.status_label.config(text=message, fg="white")
            self.info_label.config(
                text="Se recomienda actualizar para obtener las últimas mejoras."
            )

            self.widgets.create_modern_button(
                self.btn_frame,
                "⬇️ Instalar Ahora",
                lambda: self._start_download(extra_data),
                self.widgets.success_color,
                width=20,
            ).pack()

    def _close_cleanly(self):
        if self.modal:
            self.modal.grab_release()
            self.modal.destroy()
            self.modal = None

        self.root.focus_force()

    def _start_download(self, url):
        for widget in self.btn_frame.winfo_children():
            widget.destroy()

        self.status_label.config(text="Descargando actualización...")
        self.info_label.config(text="Por favor espera, no cierres el programa.")

        threading.Thread(target=self._download_logic, args=(url,), daemon=True).start()

    def _download_logic(self, url):
        try:
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, "BIGestPwd_Update.exe")

            response = requests.get(url, stream=True)
            total_size = int(response.headers.get("content-length", 0))
            block_size = 8192
            wrote = 0

            with open(installer_path, "wb") as f:
                for data in response.iter_content(block_size):
                    size = f.write(data)
                    wrote += size
                    if total_size > 0:
                        percent = (wrote / total_size) * 100
                        self.root.after(
                            0, lambda p=percent: self.progress_bar.configure(value=p)
                        )

            self.root.after(0, lambda: self._launch_installer(installer_path))

        except Exception as e:
            self.root.after(
                0, lambda: self._update_ui_state("error", f"Error de descarga: {e}")
            )

    def _launch_installer(self, path):
        self.status_label.config(text="Iniciando instalación...")
        self.progress_bar.configure(value=100)
        self.modal.update()

        subprocess.Popen([path, "/SILENT"])

        self.root.quit()
        sys.exit()
