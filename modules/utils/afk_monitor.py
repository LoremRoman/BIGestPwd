import time
import threading
import ctypes
from ctypes import Structure, windll, c_uint, sizeof, byref


class LASTINPUTINFO(Structure):
    _fields_ = [
        ("cbSize", c_uint),
        ("dwTime", c_uint),
    ]


class AFKMonitor:
    def __init__(self, timeout_minutes=15, on_afk_callback=None):
        self.timeout_seconds = timeout_minutes * 60
        self.callback = on_afk_callback
        self.running = False
        self.thread = None
        self._last_input = LASTINPUTINFO()
        self._last_input.cbSize = sizeof(LASTINPUTINFO)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _get_idle_time(self):
        windll.user32.GetLastInputInfo(byref(self._last_input))
        millis = windll.kernel32.GetTickCount() - self._last_input.dwTime
        return millis / 1000.0

    def _monitor_loop(self):
        while self.running:
            try:
                idle_time = self._get_idle_time()
                if idle_time >= self.timeout_seconds:
                    if self.callback:
                        self.callback()
                        self._wait_for_activity()
                time.sleep(5)
            except Exception:
                time.sleep(10)

    def _wait_for_activity(self):
        while self.running:
            if self._get_idle_time() < 2:
                break
            time.sleep(1)
