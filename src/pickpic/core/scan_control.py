from __future__ import annotations

import threading


class ScanAborted(Exception):
    """Raised when the active scan is aborted."""


class ScanController:
    def __init__(self):
        self._resume_event = threading.Event()
        self._resume_event.set()
        self._abort_event = threading.Event()

    @property
    def is_paused(self) -> bool:
        return not self._resume_event.is_set() and not self._abort_event.is_set()

    @property
    def is_aborted(self) -> bool:
        return self._abort_event.is_set()

    def pause(self) -> None:
        if not self._abort_event.is_set():
            self._resume_event.clear()

    def resume(self) -> None:
        self._resume_event.set()

    def abort(self) -> None:
        self._abort_event.set()
        self._resume_event.set()

    def checkpoint(self) -> None:
        if self._abort_event.is_set():
            raise ScanAborted()
        while not self._resume_event.wait(0.1):
            if self._abort_event.is_set():
                raise ScanAborted()
        if self._abort_event.is_set():
            raise ScanAborted()
