"""The notice board.

A module that notices something publishes a named event. Any module that cares
subscribes. The publisher never learns who listened, which is what lets a
notification module hear about a sale later without the Vinted module knowing
notifications exist.

A subscriber that throws is logged and skipped — one broken listener must never
stop the others, or the isolation the modules are for is lost.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from .appLogging import getLogger

log = getLogger("events")

Handler = Callable[..., None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[tuple[str, Handler]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler, owner: str = "unknown") -> None:
        self._handlers[event].append((owner, handler))
        log.debug(f"{owner} is listening for {event}")

    def emit(self, event: str, **payload) -> int:
        listeners = self._handlers.get(event, [])
        delivered = 0
        for owner, handler in listeners:
            try:
                handler(**payload)
                delivered += 1
            except Exception as error:  # a bad listener must not stop the rest
                log.error(f"{owner} failed handling {event}: {error}")
        return delivered

    def listeners(self, event: str) -> list[str]:
        return [owner for owner, _ in self._handlers.get(event, [])]

    @property
    def events(self) -> list[str]:
        return sorted(self._handlers)
