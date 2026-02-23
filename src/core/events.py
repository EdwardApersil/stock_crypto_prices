from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, ClassVar, List
import threading

from models import Ticker, PriceSnapshot

@dataclass(frozen=True)
class PriceUpdateEvent:
    """fired after a successful price update"""
    snapshot: PriceSnapshot
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class FetchFailedEvent:
    """fired when a fetcher returns None ( bad ticker, network error, etc"""
    ticker: Ticker
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class TickerAddedEvent:
    """Fired when the user adds a new ticker to the watchlist."""
    ticker: Ticker


@dataclass(frozen=True)
class TickerRemovedEvent:
    """Fired when the user removes a ticker from the watchlist."""
    ticker: Ticker


@dataclass(frozen=True)
class RefreshStartedEvent:
    """Fired when the user requests a refresh."""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class RefreshCompletedEvent:
    """Fired when all tickers in a refresh cycle have been processed."""
    success_count: int
    failure_count: int
    timestamp: datetime = field(default_factory=datetime.now)

EventHandler = Callable[[object], None]

EventType = type

# Singleton event bus
class EventBus:


    _instance: ClassVar[Optional[EventBus]] = None
    _lock = ClassVar[threading.lock] = threading.Lock()

    def __init__(self) -> None:
        self._subscribers: dict[EventType, List[EventHandler]] = {}

        self._sub_lock = threading.Lock()

        @classmethod
        def instance(cls) -> "EventBus":
            """
            Return the single shared EventBus instance.

            Double-checked locking pattern:
            - First check avoids acquiring the lock on every call (fast path)
            - Second check inside the lock prevents race condition on first creation
            """
            if cls._instance is None:
                with cls._lock:
                    if cls._instance is None:  # second check
                        cls._instance = cls()
            return cls._instance

        @classmethod
        def reset(cls) -> None:
            """
            Destroy the singleton instance. Used in tests ONLY.
            Never call this in production code.
            """
            with cls._lock:
                cls._instance = None

        def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
            """
            Register a callback for a specific event type.

            Args:
                event_type: The class of event to listen for (e.g. PriceUpdatedEvent)
                handler:    Callable that accepts one argument — the event instance
            """
            with self._sub_lock:
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = []
                self._subscribers[event_type].append(handler)

        def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
            """Deregister a previously subscribed handler."""
            with self._sub_lock:
                handlers = self._subscribers.get(event_type, [])
                if handler in handlers:
                    handlers.remove(handler)

        def publish(self, event: object) -> None:
            """
            Dispatch an event to all registered handlers for its type.

            We copy the handler list before iterating so that a handler
            unsubscribing itself mid-loop doesn't cause a RuntimeError.
            """
            event_type = type(event)
            with self._sub_lock:
                handlers = list(self._subscribers.get(event_type, []))

            for handler in handlers:
                try:
                    handler(event)
                except Exception as exc:
                    # A bad handler must never crash the publisher
                    print(f"[EventBus] Handler {handler} raised: {exc}")



