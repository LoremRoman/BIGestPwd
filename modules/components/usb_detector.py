import threading
import time
from modules.auth.usb_bypass import USBBypass


class USBDetector:
    def __init__(self, update_callback=None):
        self.usb_bypass = USBBypass()
        self.update_callback = update_callback
        self.detection_active = False
        self.detection_thread = None
        self._stop_event = threading.Event()

    def start_detection(self):
        if self.detection_active:
            return

        self.detection_active = True
        self._stop_event.clear()
        self.detection_thread = threading.Thread(
            target=self._detection_loop, daemon=True
        )
        self.detection_thread.start()

    def stop_detection(self):
        self.detection_active = False
        self._stop_event.set()

        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=0.5)

    def _detection_loop(self):
        last_state = None

        while self.detection_active and not self._stop_event.is_set():
            try:
                current_state = self.usb_bypass.verify_device()

                if current_state != last_state:
                    if self.update_callback:
                        self.update_callback(current_state)
                    last_state = current_state

                self._stop_event.wait(2.0)

            except Exception as e:
                print(f"⚠️ [USB Detector] Error en ciclo de detección: {e}")
                self._stop_event.wait(5.0)

    def get_detection_status(self):
        return {
            "active": self.detection_active,
            "devices_connected": self.usb_bypass.verify_device(),
            "authorized_devices": self.usb_bypass.get_authorized_devices(),
        }

    def force_detection(self):
        return self.usb_bypass.verify_device()
