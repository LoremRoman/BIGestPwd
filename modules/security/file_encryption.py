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
        """Deriva una clave segura de la contraseña para archivos (PBKDF2)"""
        if isinstance(password, str):
            password = password.encode()
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        key = kdf.derive(password)
        return base64.urlsafe_b64encode(key)
    
    def generate_salt(self) -> bytes:
        """Genera un salt criptográficamente seguro de 16 bytes"""
        return os.urandom(16)
    
    def encrypt_file(self, data: str, password: str) -> tuple[bytes, bytes]:
        """
        Encripta datos en memoria.
        Retorna: (datos_encriptados_bytes, salt_bytes)
        """
        salt = self.generate_salt()
        key = self.derive_key_from_password(password, salt)
        cipher_suite = Fernet(key)
        
        # Asegurar que data sea bytes antes de encriptar
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
            
        encrypted_data = cipher_suite.encrypt(data_bytes)
        return encrypted_data, salt
    
    def decrypt_file(self, encrypted_data: bytes, salt: bytes, password: str) -> str:
        """Descifra datos usando la contraseña proporcionada"""
        try:
            # Derivar la misma clave
            key = self.derive_key_from_password(password, salt)
            
            # Descifrar
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data)
            
            # Retornar como string
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            # No imprimimos el error completo por seguridad en logs, pero lo relanzamos
            # print(f"❌ Error descifrando: {e}") 
            raise ValueError("Contraseña incorrecta o archivo corrupto")
    
    def validate_encryption_key(self, encrypted_data: bytes, salt: bytes, password: str) -> bool:
        """Valida si la contraseña puede desencriptar los datos sin lanzar error"""
        try:
            self.decrypt_file(encrypted_data, salt, password)
            return True
        except:
            return False
    
    def secure_file_overwrite(self, file_path: str, passes: int = 3):
        """Sobrescribe un archivo de forma segura antes de eliminarlo (Shredding)"""
        try:
            if not os.path.exists(file_path):
                return
            
            file_size = os.path.getsize(file_path)
            
            # Pasadas de sobrescritura
            with open(file_path, 'wb') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno()) # Forzar escritura en disco físico
            
            # Eliminar archivo final
            os.remove(file_path)
            
        except Exception as e:
            print(f"⚠️ Error sobrescribiendo archivo seguro: {e}")
            # Intentar eliminación simple si falla el borrado seguro
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
    
    def create_secure_file(self, file_path: str, content: str, password: str) -> bool:
        """
        Crea un archivo físico encriptado.
        Formato del archivo: [16 bytes SALT] + [CONTENIDO ENCRIPTADO]
        """
        try:
            encrypted_data, salt = self.encrypt_file(content, password)
            
            with open(file_path, 'wb') as f:
                f.write(salt)           # Primero el salt
                f.write(encrypted_data) # Luego los datos
            
            return True
            
        except Exception as e:
            print(f"❌ Error creando archivo seguro: {e}")
            return False
    
    def read_secure_file(self, file_path: str, password: str) -> str:
        """Lee y desencripta un archivo físico seguro"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe")
            
        try:
            with open(file_path, 'rb') as f:
                salt = f.read(16)      # Leer los primeros 16 bytes (salt)
                encrypted_data = f.read() # Leer el resto
            
            return self.decrypt_file(encrypted_data, salt, password)
            
        except Exception as e:
            raise ValueError(f"Error leyendo archivo seguro: {e}")