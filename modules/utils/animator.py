import tkinter as tk


class WindowAnimator:
    @staticmethod
    def fade_in(window, step=0.05, interval=10):
        window.attributes("-alpha", 0.0)
        window.deiconify()

        current_alpha = 0.0

        def _fade():
            nonlocal current_alpha
            current_alpha += step
            if current_alpha >= 1.0:
                window.attributes("-alpha", 1.0)
                return
            window.attributes("-alpha", current_alpha)
            window.after(interval, _fade)

        _fade()

    @staticmethod
    def fade_out(window, on_complete=None, step=0.1, interval=10):
        current_alpha = float(window.attributes("-alpha"))

        def _fade():
            nonlocal current_alpha
            current_alpha -= step
            if current_alpha <= 0.0:
                window.attributes("-alpha", 0.0)
                window.withdraw()
                if on_complete:
                    on_complete()
                return
            window.attributes("-alpha", current_alpha)
            window.after(interval, _fade)

        _fade()
