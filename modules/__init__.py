"""
BIGestPwd 2.3 - Módulos principales
Gestor seguro de contraseñas con encriptación avanzada y autenticación multifactor.
"""

__version__ = "2.3.0"
__author__ = "BIGestPwd Team"

# Importaciones principales de autenticación
from .auth.multi_factor import MultiFactorAuth
from .auth.totp_offline import TOTPOffline
from .auth.usb_bypass import USBBypass

__all__ = [
    'MultiFactorAuth',
    'TOTPOffline',
    'USBBypass'
]