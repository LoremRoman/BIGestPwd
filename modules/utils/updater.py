import requests
import os
import sys
import subprocess
import threading
import tempfile
from tkinter import messagebox
from packaging import version
import webbrowser
from modules.config import APP_VERSION as CURRENT_VERSION, REPO_OWNER, REPO_NAME


class AppUpdater:
    def __init__(self, root, on_start_check=None, on_finish_check=None):
        self.root = root
        self.api_url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        )
        self.on_start = on_start_check
        self.on_finish = on_finish_check

    def check_for_updates(self):
        if self.on_start:
            self.on_start()

        thread = threading.Thread(target=self._check_logic, daemon=True)
        thread.start()

    def _check_logic(self):
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code != 200:
                self.root.after(
                    0, lambda: self._show_error("No se pudo conectar con el servidor.")
                )
                return

            data = response.json()
            latest_tag = data.get("tag_name", "0.0").replace("v", "")
            html_url = data.get(
                "html_url", f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
            )

            if version.parse(latest_tag) > version.parse(CURRENT_VERSION):
                download_url = self._get_exe_url(data)
                if download_url:
                    self.root.after(
                        0,
                        lambda: self._confirm_update(
                            latest_tag, download_url, data.get("body", ""), html_url
                        ),
                    )
                else:
                    self.root.after(
                        0,
                        lambda: self._show_error(
                            "Nueva versión detectada, pero falta el .exe en GitHub."
                        ),
                    )
            else:
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Actualizado",
                        f"Ya tienes la última versión ({CURRENT_VERSION}).",
                    ),
                )

        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Error: {str(e)}"))

        finally:
            if self.on_finish:
                self.root.after(0, self.on_finish)

    def _get_exe_url(self, data):
        for asset in data.get("assets", []):
            if asset["name"].endswith(".exe"):
                return asset["browser_download_url"]
        return None

    def _confirm_update(self, ver, exe_url, notes, release_url):
        msg = f"¡Versión v{ver} disponible!\n\n{notes}\n\n¿Descargar e instalar ahora?"
        if messagebox.askyesno("Actualización", msg, parent=self.root):
            webbrowser.open(release_url)
            self._download_and_install(exe_url)

    def _download_and_install(self, url):
        try:
            messagebox.showinfo(
                "Actualizando",
                "1. Se descargará la actualización.\n"
                "2. El programa se cerrará automáticamente.\n"
                "3. Verás una ventana de instalación.\n\n"
                "¡El programa se volverá a abrir solo al terminar!",
            )

            response = requests.get(url, stream=True)
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, f"BIGestPwd_Update.exe")

            with open(installer_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            subprocess.Popen([installer_path, "/SILENT"])

            self.root.quit()
            sys.exit()

        except Exception as e:
            messagebox.showerror("Error", f"Fallo en descarga:\n{e}")

    def _show_error(self, msg):
        messagebox.showerror("Error", msg, parent=self.root)
