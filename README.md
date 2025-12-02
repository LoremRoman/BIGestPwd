# 🛡️ BIGestPwd 2.3

> **Secure. Open Source. Free. Always.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Stable-success)
![Platform](https://img.shields.io/badge/Platform-Windows-blue)

**BIGestPwd 2.3** es un gestor de contraseñas de escritorio robusto, diseñado con la filosofía "Zero-Knowledge" (Cero Conocimiento). Tus datos nunca salen de tu dispositivo y están protegidos por estándares de encriptación militar y autenticación multifactor avanzada.

---

## ✨ Características Principales

### 🔒 Máxima Seguridad
*   **Encriptación AES-256 (Fernet):** Tus contraseñas y notas se encriptan antes de tocar el disco.
*   **Derivación de Claves (PBKDF2-HMAC-SHA256):** Protección contra ataques de fuerza bruta usando 100,000 iteraciones y salts únicos.
*   **Zero-Knowledge:** La base de datos solo guarda datos encriptados. Sin tu contraseña maestra, es imposible acceder.

### 🛡️ Autenticación Multifactor (MFA)
BIGestPwd va más allá de la contraseña maestra. Puedes (y debes) activar una segunda capa:
*   **📱 TOTP (Google Authenticator):** Compatible con cualquier app de autenticación estándar.
*   **💾 Bypass USB (Llave de Hardware):** Convierte cualquier memoria USB en una llave física. Si el USB está conectado, el sistema lo reconoce y permite el acceso.

### 🎨 Diseño Moderno
*   Interfaz gráfica moderna en **Modo Oscuro**.
*   Diseño responsive que se adapta al tamaño de tu ventana.
*   Generador de contraseñas fuertes integrado.
*   Organización por categorías y buscador rápido.

---

## 🚀 Instalación y Uso

### Opción A: Usuario Final (Windows)
1. Ve a la sección de **[Releases](../../releases)** de este repositorio.
2. Descarga el instalador: `Instalador_BIGestPwd_2.3.exe`.
3. Ejecuta el instalador y sigue los pasos.
4. ¡Listo! Busca **BIGestPwd** en tu escritorio.

### Opción B: Desarrolladores (Código Fuente)

Si deseas ejecutarlo desde el código o contribuir:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/LoremRoman/BIGestPwd.git
   cd BIGestPwd