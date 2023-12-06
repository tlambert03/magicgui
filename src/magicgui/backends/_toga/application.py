from collections.abc import Callable
from threading import Timer

import toga

from magicgui.widgets.protocols import BaseApplicationBackend


class ApplicationBackend(BaseApplicationBackend):
    _app: toga.App

    def _mgui_get_backend_name(self):
        return "toga"

    def _mgui_process_events(self):
        ...

    def _mgui_run(self):
        app = self._mgui_get_native_app()
        app.main_loop()

    def _mgui_quit(self):
        return self._mgui_get_native_app().exit()

    def _mgui_get_native_app(self) -> toga.App:
        # Get native app
        if getattr(self, "_app", None) is None:
            self._app = toga.App("Magicgui App", "org.pyapp-kit.magicgui")
        return self._app

    def _mgui_start_timer(self, interval=0, on_timeout=None, single=False):
        self._timer = RepeatTimer(interval, on_timeout, single)
        self._timer.start()

    def _mgui_stop_timer(self):
        if getattr(self, "_timer", None):
            self._timer.cancel()



class RepeatTimer(Timer):
    def __init__(
        self,
        interval: float,
        function: Callable[..., object] | None,
        single: bool = False,
    ) -> None:
        self.single_shot = single
        super().__init__(interval, function or (lambda: None))

    def run(self):
        if self.single_shot:
            super().run()
        else:
            while not self.finished.wait(self.interval):
                self.function(*self.args, **self.kwargs)
