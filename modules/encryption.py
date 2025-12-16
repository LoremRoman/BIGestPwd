import os
import sys
import base64
import sqlite3
import threading
import shutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


def _get_old_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)


def get_persistent_data_path():
    path = os.path.join(os.getenv("LOCALAPPDATA"), "BIGestPwd")
    os.makedirs(path, exist_ok=True)
    return path


def migrate_old_data():
    old_data_path = os.path.join(_get_old_base_path(), "data")
    new_data_path = get_persistent_data_path()

    if os.path.exists(old_data_path) and old_data_path != new_data_path:
        old_db_file = os.path.join(old_data_path, "bigestpwd_secure.db")
        new_db_file = os.path.join(new_data_path, "bigestpwd_secure.db")

        if os.path.exists(old_db_file) and not os.path.exists(new_db_file):
            try:
                shutil.copy2(old_db_file, new_db_file)
                # Opcional: renombrar la carpeta antigua para evitar futuras migraciones
                # os.rename(old_data_path, old_data_path + "_migrated")
            except Exception as e:
                pass


migrate_old_data()

DB_PATH = os.path.join(get_persistent_data_path(), "bigestpwd_secure.db")


class SecureEncryption:
    def __init__(self):
        self.backend = default_backend()

    def derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        if isinstance(password, str):
            password = password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend,
        )
        key = kdf.derive(password)
        return base64.urlsafe_b64encode(key)

    def generate_salt(self) -> bytes:
        return os.urandom(32)

    def hash_master_password(self, password: str) -> tuple[bytes, bytes]:
        salt = self.generate_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend,
        )
        if isinstance(password, str):
            password = password.encode()
        hashed = kdf.derive(password)
        return hashed, salt

    def verify_master_password(
        self, password: str, stored_hash: bytes, salt: bytes
    ) -> bool:
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend,
            )
            if isinstance(password, str):
                password = password.encode()
            test_hash = kdf.derive(password)
            return test_hash == stored_hash
        except:
            return False

    def encrypt_data(self, data: str, password: str) -> tuple[bytes, bytes]:
        salt = self.generate_salt()
        key = self.derive_key_from_password(password, salt)
        cipher_suite = Fernet(key)
        if isinstance(data, str):
            data = data.encode()
        encrypted_data = cipher_suite.encrypt(data)
        return encrypted_data, salt

    def decrypt_data(self, encrypted_data: bytes, salt: bytes, password: str) -> str:
        try:
            key = self.derive_key_from_password(password, salt)
            cipher_suite = Fernet(key)
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode("utf-8")
        except:
            raise ValueError("Error desencriptando")


class DatabaseManager:
    def __init__(self, encryption_system: SecureEncryption):
        self.encryption = encryption_system
        self.db_path = DB_PATH
        self.db_lock = threading.Lock()
        self.setup_database()
        self.repair_database_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=20.0)

    def setup_database(self):
        with self.db_lock:
            with self._get_connection() as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                cursor = conn.cursor()

                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS master_config (id INTEGER PRIMARY KEY, master_hash BLOB NOT NULL, master_salt BLOB NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, color TEXT DEFAULT '#3b82f6', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )

                default_categories = [
                    ("Redes Sociales", "#ef4444"),
                    ("Trabajo", "#3b82f6"),
                    ("Personal", "#10b981"),
                    ("Finanzas", "#f59e0b"),
                    ("Correos", "#8b5cf6"),
                    ("Juegos", "#ec4899"),
                    ("Streaming", "#06b6d4"),
                    ("Compras", "#84cc16"),
                    ("Otros", "#6b7280"),
                ]
                for name, color in default_categories:
                    cursor.execute(
                        "INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)",
                        (name, color),
                    )

                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS password_entries (id INTEGER PRIMARY KEY, category_id INTEGER, title TEXT NOT NULL, username TEXT, encrypted_password BLOB NOT NULL, password_salt BLOB NOT NULL, url TEXT, notes BLOB, notes_salt BLOB, strength INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (category_id) REFERENCES categories(id))"
                )

                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS totp_secrets (id INTEGER PRIMARY KEY, service_name TEXT DEFAULT 'BIGestPwd', encrypted_secret BLOB NOT NULL, secret_salt BLOB NOT NULL, backup_codes BLOB, backup_salt BLOB, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )

                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS mfa_config (id INTEGER PRIMARY KEY, method_name TEXT NOT NULL UNIQUE, is_enabled BOOLEAN DEFAULT 0, is_configured BOOLEAN DEFAULT 0, config_data BLOB, config_salt BLOB, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )

                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS user_profile (id INTEGER PRIMARY KEY, display_name TEXT NOT NULL, is_anonymous BOOLEAN DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )

                mfa_methods = [
                    ("master_password", 1, 1),
                    ("totp_offline", 0, 0),
                    ("usb_bypass", 0, 0),
                ]
                for method_name, is_enabled, is_configured in mfa_methods:
                    cursor.execute(
                        "INSERT OR IGNORE INTO mfa_config (method_name, is_enabled, is_configured) VALUES (?, ?, ?)",
                        (method_name, is_enabled, is_configured),
                    )

                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS usb_devices (id INTEGER PRIMARY KEY, device_name TEXT NOT NULL, device_uuid TEXT UNIQUE NOT NULL, device_path TEXT DEFAULT '', created_at DATETIME DEFAULT CURRENT_TIMESTAMP, last_seen DATETIME DEFAULT CURRENT_TIMESTAMP, is_active BOOLEAN DEFAULT 1)"
                )
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS usb_security_files (id INTEGER PRIMARY KEY, device_uuid TEXT NOT NULL, file_name TEXT NOT NULL, encrypted_data BLOB NOT NULL, file_salt BLOB NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (device_uuid) REFERENCES usb_devices(device_uuid))"
                )
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS usb_blacklist (id INTEGER PRIMARY KEY, device_uuid TEXT UNIQUE NOT NULL, device_name TEXT NOT NULL, revoked_at DATETIME DEFAULT CURRENT_TIMESTAMP, cleaned BOOLEAN DEFAULT 0, reason TEXT DEFAULT 'Usuario eliminó dispositivo')"
                )

                conn.commit()

    def repair_database_tables(self):
        with self.db_lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("PRAGMA table_info(totp_secrets)")
                    columns_totp = [column[1] for column in cursor.fetchall()]
                    if "backup_codes" not in columns_totp:
                        cursor.execute(
                            "ALTER TABLE totp_secrets ADD COLUMN backup_codes BLOB"
                        )
                        cursor.execute(
                            "ALTER TABLE totp_secrets ADD COLUMN backup_salt BLOB"
                        )

                    cursor.execute("PRAGMA table_info(password_entries)")
                    columns_pwd = [column[1] for column in cursor.fetchall()]

                    if "updated_at" not in columns_pwd:
                        cursor.execute(
                            "ALTER TABLE password_entries ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                        )

                    conn.commit()
            except Exception as e:
                pass

    def is_master_configured(self) -> bool:
        with self.db_lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM master_config")
                return cursor.fetchone()[0] > 0

    def configure_master_password(self, master_password: str) -> bool:
        if self.is_master_configured():
            return False
        master_hash, master_salt = self.encryption.hash_master_password(master_password)
        with self.db_lock:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO master_config (master_hash, master_salt) VALUES (?, ?)",
                    (master_hash, master_salt),
                )
                conn.commit()
        return True

    def verify_master_password(self, master_password: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT master_hash, master_salt FROM master_config LIMIT 1"
                )
                result = cursor.fetchone()
            if not result:
                return False
            return self.encryption.verify_master_password(
                master_password, result[0], result[1]
            )
        except:
            return False

    def add_password_entry(
        self, category_id, title, username, password, url, notes, master_password
    ):
        try:
            encrypted_password, password_salt = self.encryption.encrypt_data(
                password, master_password
            )
            encrypted_notes, notes_salt = (None, None)
            if notes:
                encrypted_notes, notes_salt = self.encryption.encrypt_data(
                    notes, master_password
                )

            with self.db_lock:
                with self._get_connection() as conn:
                    conn.execute(
                        "INSERT INTO password_entries (category_id, title, username, encrypted_password, password_salt, url, notes, notes_salt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            category_id,
                            title,
                            username,
                            encrypted_password,
                            password_salt,
                            url,
                            encrypted_notes,
                            notes_salt,
                        ),
                    )
                    conn.commit()
            return True
        except:
            return False

    def update_password_entry(
        self,
        entry_id,
        category_id,
        title,
        username,
        password,
        url,
        notes,
        master_password,
    ):
        try:
            encrypted_password, password_salt = self.encryption.encrypt_data(
                password, master_password
            )
            encrypted_notes, notes_salt = (None, None)
            if notes:
                encrypted_notes, notes_salt = self.encryption.encrypt_data(
                    notes, master_password
                )

            with self.db_lock:
                with self._get_connection() as conn:
                    conn.execute(
                        "UPDATE password_entries SET category_id = ?, title = ?, username = ?, encrypted_password = ?, password_salt = ?, url = ?, notes = ?, notes_salt = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (
                            category_id,
                            title,
                            username,
                            encrypted_password,
                            password_salt,
                            url,
                            encrypted_notes,
                            notes_salt,
                            entry_id,
                        ),
                    )
                    conn.commit()
            return True
        except:
            return False

    def get_password_entries(self, master_password):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT p.id, c.name, c.color, p.title, p.username, p.encrypted_password, p.password_salt, p.url, p.notes, p.notes_salt, p.created_at, p.updated_at FROM password_entries p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.title"
                )
                rows = cursor.fetchall()

            entries = []
            for row in rows:
                try:
                    decrypted_password = self.encryption.decrypt_data(
                        row[5], row[6], master_password
                    )
                    decrypted_notes = ""
                    if row[8] and row[9]:
                        decrypted_notes = self.encryption.decrypt_data(
                            row[8], row[9], master_password
                        )

                    date_to_use = row[11] if row[11] else row[10]

                    entries.append(
                        {
                            "id": row[0],
                            "category": row[1] or "Sin categoría",
                            "color": row[2] or "#6b7280",
                            "title": row[3],
                            "username": row[4],
                            "password": decrypted_password,
                            "url": row[7],
                            "notes": decrypted_notes,
                            "date_for_check": date_to_use,
                        }
                    )
                except:
                    continue
            return entries
        except:
            return []

    def get_categories(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, color FROM categories ORDER BY name")
            return [
                {"id": row[0], "name": row[1], "color": row[2]}
                for row in cursor.fetchall()
            ]

    def delete_password_entry(self, entry_id):
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    conn.execute(
                        "DELETE FROM password_entries WHERE id = ?", (entry_id,)
                    )
                    conn.commit()
            return True
        except:
            return False


encryption_system = SecureEncryption()
db_manager = DatabaseManager(encryption_system)
