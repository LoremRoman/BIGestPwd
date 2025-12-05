# 🛡️ BIGestPwd 2.4

> **Secure. Open Source. Free. Always.**

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge)

</div>

---

**BIGestPwd** es la evolución de tu gestor de contraseñas de escritorio. Diseñado bajo la filosofía **"Zero-Knowledge"**, garantiza que tus datos nunca salgan de tu dispositivo sin estar fuertemente encriptados. Ahora con sistema de **actualizaciones automáticas** y correcciones visuales.

## ✨ Novedades en v2.5
*   🚀 **Sistema de Novedades** Nueva interfaz de bienvenida que te informará detalladamente de las mejoras cada vez que actualices.
*   🧹 **Limpieza!:** Ahora, cuándo copias una contraseña, automáticamente después de 1 min borra tu portapapeles para eviar filtrar información de forma malintencionada.
*   🧬 **Vida saludable para tus contraseñas!:** Dentro de tus contraseñas guardadas, ahora verás "Status" de tus contraseñas, para conocer si son seguras o su tiempo de vida es largo.

---

## 🔐 Características de Seguridad

| Tecnología | Descripción |
| :--- | :--- |
| **AES-256 (Fernet)** | Estándar militar. Tus contraseñas y notas se encriptan antes de tocar el disco duro. |
| **PBKDF2-HMAC** | Derivación de claves con 100,000 iteraciones y *salts* únicos para evitar fuerza bruta. |
| **Zero-Knowledge** | La base de datos es inútil sin tu contraseña maestra. Nosotros no tenemos acceso a ella. |

### 🛡️ Autenticación Multifactor (MFA)
No te conformes solo con una contraseña. BIGestPwd ofrece seguridad por capas:

1.  **📱 TOTP (Google Authenticator):** Escanea el QR y genera códigos temporales offline.
2.  **💾 Bypass USB (Llave Física):** Convierte cualquier memoria USB en una llave de acceso física. Si la desconectas, nadie entra.

---

## 🎨 Galería

<div align="center">
  <img src="assets/about.jpg" width="60%" alt="Security" />
</div>

<div align="center">
  <img src="assets/create_password.jpg" width="45%" alt="About" />
  
  <img src="assets/security.jpg" width="45%" alt="Create Password" />
</div>

---

## 🚀 Instalación y Uso

### 👤 Opción A: Usuario Final (Recomendado)
El método más sencillo para empezar a proteger tus contraseñas.

1. Ve a la sección de **[Releases](../../releases)** de este repositorio.
2. Descarga el último instalador: `Instalador_BIGestPwd_2.5.exe`. (O la versión más actual)
3. Ejecútalo e instala.
4. **¡Listo!** Cuando haya una nueva versión, el botón "🔄 Actualizar" dentro de la app hará todo el trabajo por ti.

### 💻 Opción B: Desarrolladores (Código Fuente)
Si deseas auditar el código, contribuir o compilarlo tú mismo:

```bash
# 1. Clonar el repositorio
git clone https://github.com/LoremRoman/BIGestPwd.git

# 2. Entrar a la carpeta
cd BIGestPwd

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```
---

🤝 Contribuir
¡Las contribuciones son bienvenidas! Si encuentras un bug o tienes una idea:
* Haz un Fork del proyecto.
* Crea una rama (git checkout -b feature/NuevaCosa).
* Haz Commit (git commit -m 'Añadir NuevaCosa').
* Haz Push (git push origin feature/NuevaCosa).
* Abre un Pull Request.

---

<div align="center">
<sub>Desarrollado con ❤️ y Python por <b>LoremRoman</b>.</sub>
</div>
