import sqlite3
import os
from modules.encryption import db_manager

DATA_DIR = os.path.join(os.getcwd(), "data")
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "bigestpwd_secure.db")


class MultiFactorAuth:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else DEFAULT_DB_PATH

    def get_mfa_status(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT method_name, is_enabled, is_configured FROM mfa_config ORDER BY id"
        )
        methods = {}
        for row in cursor.fetchall():
            methods[row[0]] = {"enabled": bool(row[1]), "configured": bool(row[2])}
        conn.close()
        return methods

    def update_mfa_method(self, method_name, enabled=None, configured=None):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        updates = []
        params = []
        if enabled is not None:
            updates.append("is_enabled = ?")
            params.append(enabled)
        if configured is not None:
            updates.append("is_configured = ?")
            params.append(configured)
        if updates:
            params.append(method_name)
            cursor.execute(
                f"UPDATE mfa_config SET {', '.join(updates)} WHERE method_name = ?",
                params,
            )
        conn.commit()
        conn.close()
        return True

    def get_required_methods_count(self):
        return 2

    def get_available_methods(self):
        status = self.get_mfa_status()
        return [m for m, c in status.items() if c["enabled"] and c["configured"]]

    def can_authenticate(self):
        return len(self.get_available_methods()) >= self.get_required_methods_count()

    def validate_authentication(self, provided_methods, master_password=""):
        if len(provided_methods) < self.get_required_methods_count():
            return False

        valid_methods_count = 0

        for method, data in provided_methods.items():
            try:
                if method == "master_password":
                    if db_manager.verify_master_password(data):
                        valid_methods_count += 1
                elif method == "totp_offline":
                    from .totp_offline import TOTPOffline

                    if TOTPOffline(self.db_path).verify_code(data, master_password):
                        valid_methods_count += 1
                elif method == "usb_bypass":
                    from .usb_bypass import USBBypass

                    if USBBypass(self.db_path).verify_device():
                        valid_methods_count += 1
            except:
                continue

        return valid_methods_count >= self.get_required_methods_count()

    def save_user_profile(self, display_name, is_anonymous=False):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_profile")
            cursor.execute(
                "INSERT INTO user_profile (display_name, is_anonymous) VALUES (?, ?)",
                (display_name, is_anonymous),
            )
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def get_user_profile(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT display_name, is_anonymous FROM user_profile LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        if result:
            return {"display_name": result[0], "is_anonymous": bool(result[1])}
        return None
