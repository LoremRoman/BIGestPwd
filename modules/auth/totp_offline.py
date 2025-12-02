import base64
import hashlib
import time
import sqlite3
import secrets
import qrcode
import os
from io import BytesIO
import pyotp
from modules.encryption import encryption_system

# --- PATH ---
DATA_DIR = os.path.join(os.getcwd(), 'data')
DEFAULT_DB_PATH = os.path.join(DATA_DIR, 'bigestpwd_secure.db')
# ------------

class TOTPOffline:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else DEFAULT_DB_PATH
    
    def generate_secret(self): return pyotp.random_base32()
    
    def save_secret(self, secret, master_password):
        encrypted_secret, secret_salt = encryption_system.encrypt_data(secret, master_password)
        backup_codes = self.generate_backup_codes()
        encrypted_backup, backup_salt = encryption_system.encrypt_data(','.join(backup_codes), master_password)
        return self._save_to_db(encrypted_secret, secret_salt, encrypted_backup, backup_salt, backup_codes)

    def _save_to_db(self, enc_secret, sec_salt, enc_backup, back_salt, return_value):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM totp_secrets")
                    cursor.execute("INSERT INTO totp_secrets (encrypted_secret, secret_salt, backup_codes, backup_salt) VALUES (?, ?, ?, ?)", (enc_secret, sec_salt, enc_backup, back_salt))
                    conn.commit()
                return return_value
            except sqlite3.OperationalError:
                time.sleep(0.5)
                continue
            except: return [] if isinstance(return_value, list) else False
        return []

    def get_secret(self, master_password):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT encrypted_secret, secret_salt FROM totp_secrets LIMIT 1')
                result = cursor.fetchone()
            if not result: return None
            return encryption_system.decrypt_data(result[0], result[1], master_password)
        except: return None

    def generate_backup_codes(self, count=8):
        return [''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(8)) for _ in range(count)]
    
    def generate_qr_code(self, secret, username="BIGestPwd User"):
        try:
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(name=username, issuer_name="BIGestPwd 2.3")
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(uri); qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            bio = BytesIO(); img.save(bio, format="PNG"); bio.seek(0)
            return bio.getvalue(), uri
        except: return None, None
    
    def verify_code(self, code, master_password):
        secret = self.get_secret(master_password)
        if not secret: return False
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def is_configured(self):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM totp_secrets")
                return cursor.fetchone()[0] > 0
        except: return False
    
    def reencrypt_secret(self, old_pwd, new_pwd):
        try:
            secret = self.get_secret(old_pwd)
            if not secret: return False
            return bool(self.save_secret(secret, new_pwd))
        except: return False