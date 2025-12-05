import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class FileEncryption:
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
        return os.urandom(16)

    def encrypt_file(self, data: str, password: str) -> tuple[bytes, bytes]:
        salt = self.generate_salt()
        key = self.derive_key_from_password(password, salt)
        cipher_suite = Fernet(key)

        if isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data

        encrypted_data = cipher_suite.encrypt(data_bytes)
        return encrypted_data, salt

    def decrypt_file(self, encrypted_data: bytes, salt: bytes, password: str) -> str:
        try:
            key = self.derive_key_from_password(password, salt)

            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data)

            return decrypted_data.decode("utf-8")

        except Exception as e:
            raise ValueError("Contraseña incorrecta o archivo corrupto")

    def validate_encryption_key(
        self, encrypted_data: bytes, salt: bytes, password: str
    ) -> bool:
        try:
            self.decrypt_file(encrypted_data, salt, password)
            return True
        except:
            return False

    def secure_file_overwrite(self, file_path: str, passes: int = 3):
        try:
            if not os.path.exists(file_path):
                return

            file_size = os.path.getsize(file_path)

            with open(file_path, "wb") as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            os.remove(file_path)

        except Exception as e:
            print(f"⚠️ Error sobrescribiendo archivo seguro: {e}")
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

    def create_secure_file(self, file_path: str, content: str, password: str) -> bool:
        try:
            encrypted_data, salt = self.encrypt_file(content, password)

            with open(file_path, "wb") as f:
                f.write(salt)
                f.write(encrypted_data)

            return True

        except Exception as e:
            print(f"❌ Error creando archivo seguro: {e}")
            return False

    def read_secure_file(self, file_path: str, password: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        try:
            with open(file_path, "rb") as f:
                salt = f.read(16)
                encrypted_data = f.read()

            return self.decrypt_file(encrypted_data, salt, password)

        except Exception as e:
            raise ValueError(f"Error leyendo archivo seguro: {e}")
