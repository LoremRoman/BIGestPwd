import threading
import time
from modules.auth.usb_bypass import USBBypass

class USBDetector:
    def __init__(self, update_callback=None):
        self.usb_bypass = USBBypass()
        self.update_callback = update_callback
        self.detection_active = False
        self.detection_thread = None
        # Evento para detener el hilo de forma segura e inmediata
        self._stop_event = threading.Event()
        
    def start_detection(self):
        """Inicia la detección en tiempo real de dispositivos USB"""
        if self.detection_active:
            return
            
        self.detection_active = True
        self._stop_event.clear()
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
    
    def stop_detection(self):
        """Detiene la detección de dispositivos USB de inmediato"""
        self.detection_active = False
        self._stop_event.set() # Despierta el hilo si está durmiendo
        
        # Esperar un momento breve a que cierre, pero sin bloquear la UI
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=0.5)
    
    def _detection_loop(self):
        """Loop principal de detección optimizado"""
        last_state = None
        
        while self.detection_active and not self._stop_event.is_set():
            try:
                # Verificar estado actual del USB
                current_state = self.usb_bypass.verify_device()
                
                # Si cambió el estado, notificar
                if current_state != last_state:
                    if self.update_callback:
                        # Nota: El callback se ejecuta en este hilo secundario.
                        # La UI debe usar root.after() o thread-safe methods si actualiza gráficos.
                        self.update_callback(current_state)
                    last_state = current_state
                
                # Esperar 2 segundos, pero interrumpible si se pide detener
                self._stop_event.wait(2.0)
                
            except Exception as e:
                print(f"⚠️ [USB Detector] Error en ciclo de detección: {e}")
                # Esperar más en caso de error para no saturar el log
                self._stop_event.wait(5.0)
    
    def get_detection_status(self):
        """Obtiene el estado actual de detección"""
        return {
            'active': self.detection_active,
            'devices_connected': self.usb_bypass.verify_device(),
            'authorized_devices': self.usb_bypass.get_authorized_devices()
        }
    
    def force_detection(self):
        """Fuerza una detección inmediata"""
        return self.usb_bypass.verify_device()