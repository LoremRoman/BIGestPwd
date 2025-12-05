import os
import uuid
import sqlite3
import time
import threading
from modules.security.file_encryption import FileEncryption

try:
    import psutil
except ImportError:
    psutil = None

DATA_DIR = os.path.join(os.getcwd(), "data")
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "bigestpwd_secure.db")


class USBBypass:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else DEFAULT_DB_PATH
        self.file_encryption = FileEncryption()
        self.db_lock = threading.Lock()
        self.setup_usb_tables()

    def setup_usb_tables(self):
        with self.db_lock:
            with sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=30.0
            ) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS usb_devices (id INTEGER PRIMARY KEY, device_name TEXT NOT NULL, device_uuid TEXT UNIQUE NOT NULL, device_path TEXT DEFAULT '', created_at DATETIME DEFAULT CURRENT_TIMESTAMP, last_seen DATETIME DEFAULT CURRENT_TIMESTAMP, is_active BOOLEAN DEFAULT 1)"""
                )
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS usb_security_files (id INTEGER PRIMARY KEY, device_uuid TEXT NOT NULL, file_name TEXT NOT NULL, encrypted_data BLOB NOT NULL, file_salt BLOB NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (device_uuid) REFERENCES usb_devices(device_uuid))"""
                )
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS usb_blacklist (id INTEGER PRIMARY KEY, device_uuid TEXT UNIQUE NOT NULL, device_name TEXT NOT NULL, revoked_at DATETIME DEFAULT CURRENT_TIMESTAMP, cleaned BOOLEAN DEFAULT 0, reason TEXT DEFAULT 'Usuario eliminó dispositivo')"""
                )
                conn.commit()

    def detect_real_usb_devices(self):
        if not psutil:
            return self._detect_usb_devices_simulated()
        try:
            usb_devices = []
            for partition in psutil.disk_partitions():
                if "removable" in partition.opts or partition.fstype.lower() in [
                    "fat",
                    "fat32",
                    "exfat",
                    "ntfs",
                    "vfat",
                ]:
                    if self.is_system_drive(partition.mountpoint):
                        continue
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        if round(usage.total / (1024**3), 1) < 4000:
                            usb_devices.append(
                                {
                                    "name": self.get_device_display_name(partition),
                                    "uuid": self.get_usb_uuid(partition.device),
                                    "path": partition.mountpoint,
                                    "size_gb": round(usage.total / (1024**3), 1),
                                    "fstype": partition.fstype,
                                    "device": partition.device,
                                    "drive_letter": self.get_drive_letter(
                                        partition.device
                                    ),
                                }
                            )
                    except:
                        continue
            return usb_devices
        except:
            return []

    def _detect_usb_devices_simulated(self):
        return [
            {
                "name": "USB_Simulado_DEV",
                "uuid": "simulated-uuid-1234",
                "path": "C:\\USB_SIMULADO" if os.name == "nt" else "/tmp/usb_sim",
                "size_gb": 16.0,
                "fstype": "FAT32",
                "device": "SIM",
                "drive_letter": "S:",
            }
        ]

    def register_usb_device(self, device_name, device_path, master_password):
        device_uuid = self.get_usb_uuid(device_path)
        with self.db_lock:
            try:
                with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) FROM usb_devices WHERE device_uuid = ? AND is_active = 1",
                        (device_uuid,),
                    )
                    if cursor.fetchone()[0] > 0:
                        return False, "Este dispositivo ya está registrado"
                    cursor.execute(
                        "SELECT COUNT(*) FROM usb_devices WHERE is_active = 1"
                    )
                    if cursor.fetchone()[0] >= 3:
                        return False, "Límite de 3 dispositivos alcanzado"
                    try:
                        cursor.execute(
                            "INSERT INTO usb_devices (device_name, device_uuid, device_path, is_active) VALUES (?, ?, ?, 1)",
                            (device_name, device_uuid, device_path),
                        )
                    except:
                        cursor.execute(
                            "INSERT INTO usb_devices (device_name, device_uuid, is_active) VALUES (?, ?, 1)",
                            (device_name, device_uuid),
                        )

                    if self.create_security_files_with_connection(
                        conn, device_path, device_uuid, master_password
                    ):
                        conn.commit()
                        self._update_mfa_status()
                        return True, "Dispositivo registrado exitosamente"
                    else:
                        conn.rollback()
                        return False, "Error escribiendo archivos en USB"
            except Exception as e:
                return False, f"Error: {e}"

    def create_security_files_with_connection(
        self, conn, device_path, device_uuid, master_password
    ):
        try:
            folder_path = os.path.join(device_path, "BIGestPwd_Security")
            os.makedirs(folder_path, exist_ok=True)
            timestamp = int(time.time())
            security_files = [
                {
                    "name": "validator.bypass",
                    "content": f"BIGestPwd_Validator_{device_uuid}_{timestamp}",
                },
                {
                    "name": "master_key.enc",
                    "content": f"encrypted_master_key_{device_uuid}_{timestamp}",
                },
                {
                    "name": "backup_codes.enc",
                    "content": f"encrypted_backup_codes_{device_uuid}_{timestamp}",
                },
                {
                    "name": "README.txt",
                    "content": f"⚠️ ARCHIVOS DE SEGURIDAD BIGestPwd.\nUUID: {device_uuid}\nNO BORRAR.",
                },
            ]
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM usb_security_files WHERE device_uuid = ?", (device_uuid,)
            )
            for f_info in security_files:
                full_path = os.path.join(folder_path, f_info["name"])
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(f_info["content"])
                if os.name == "nt":
                    try:
                        import ctypes

                        ctypes.windll.kernel32.SetFileAttributesW(full_path, 2)
                    except:
                        pass
                if f_info["name"] != "README.txt":
                    enc_data, salt = self.file_encryption.encrypt_file(
                        f_info["content"], master_password
                    )
                    cursor.execute(
                        "INSERT INTO usb_security_files (device_uuid, file_name, encrypted_data, file_salt) VALUES (?, ?, ?, ?)",
                        (device_uuid, f_info["name"], enc_data, salt),
                    )
            return True
        except:
            return False

    def verify_device(self):
        devices = self.detect_real_usb_devices()
        if not devices:
            return False
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                for dev in devices:
                    uuid_val = self.get_usb_uuid(dev["path"])
                    cursor.execute(
                        "SELECT cleaned FROM usb_blacklist WHERE device_uuid = ?",
                        (uuid_val,),
                    )
                    blacklisted = cursor.fetchone()
                    if blacklisted:
                        if not blacklisted[0]:
                            threading.Thread(
                                target=self.clean_usb_files, args=(dev["path"],)
                            ).start()
                        continue
                    cursor.execute(
                        "SELECT device_name FROM usb_devices WHERE device_uuid = ? AND is_active = 1",
                        (uuid_val,),
                    )
                    if cursor.fetchone():
                        return True
            return False
        except:
            return False

    def remove_usb_device(self, device_uuid, device_name):
        with self.db_lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO usb_blacklist (device_uuid, device_name, reason) VALUES (?, ?, 'Usuario revocó acceso')",
                        (device_uuid, device_name),
                    )
                    conn.execute(
                        "UPDATE usb_devices SET is_active = 0 WHERE device_uuid = ?",
                        (device_uuid,),
                    )
                    conn.execute(
                        "DELETE FROM usb_security_files WHERE device_uuid = ?",
                        (device_uuid,),
                    )
                    conn.commit()
                self.try_immediate_cleanup(device_uuid)
                if not self.get_authorized_devices():
                    self._update_mfa_status_removal()
                return True, "Dispositivo eliminado"
            except Exception as e:
                return False, f"Error: {e}"

    def clean_usb_files(self, device_path):
        folder = os.path.join(device_path, "BIGestPwd_Security")
        try:
            if os.path.exists(folder):
                import shutil

                shutil.rmtree(folder)
                uuid_val = self.get_usb_uuid(device_path)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE usb_blacklist SET cleaned = 1 WHERE device_uuid = ?",
                        (uuid_val,),
                    )
                    conn.commit()
                return True
        except:
            pass
        return False

    def try_immediate_cleanup(self, target_uuid):
        for dev in self.detect_real_usb_devices():
            if self.get_usb_uuid(dev["path"]) == target_uuid:
                self.clean_usb_files(dev["path"])
                return

    def get_authorized_devices(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM usb_devices WHERE is_active = 1"
                ).fetchall()
                return [
                    {
                        "name": r["device_name"],
                        "uuid": r["device_uuid"],
                        "path": r["device_path"] if "device_path" in r.keys() else "",
                        "created_at": r["created_at"],
                        "last_seen": r["last_seen"],
                    }
                    for r in rows
                ]
        except:
            return []

    def get_usb_uuid(self, path):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, path))

    def get_device_display_name(self, partition):
        name = os.path.basename(partition.mountpoint)
        if not name and os.name == "nt":
            try:
                import win32api

                name = win32api.GetVolumeInformation(partition.mountpoint)[0]
            except:
                pass
        return f"{name or 'USB Drive'} ({partition.device})"

    def get_drive_letter(self, device):
        return device.split(":")[0] if os.name == "nt" and ":" in device else ""

    def is_system_drive(self, path):
        return any(
            path.upper().startswith(p.upper())
            for p in ["C:\\", "C:/", "/", "/boot", "/System", "/Windows"]
        )

    def _update_mfa_status(self):
        try:
            from modules.auth.multi_factor import MultiFactorAuth

            MultiFactorAuth(self.db_path).update_mfa_method(
                "usb_bypass", enabled=True, configured=True
            )
        except:
            pass

    def _update_mfa_status_removal(self):
        try:
            from modules.auth.multi_factor import MultiFactorAuth

            MultiFactorAuth(self.db_path).update_mfa_method(
                "usb_bypass", enabled=False, configured=False
            )
        except:
            pass

    def is_configured(self):
        return len(self.get_authorized_devices()) > 0
