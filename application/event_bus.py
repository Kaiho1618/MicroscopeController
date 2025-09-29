from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List
import threading


@dataclass
class ImageCaptureEvent:
    image_data: Any
    timestamp: datetime


@dataclass
class ErrorEvent:
    error_message: str


@dataclass
class StartMoveEvent:
    speed: float
    direction: float


@dataclass
class StopMoveEvent:
    pass


@dataclass
class MoveToEvent:
    target_pos: tuple
    is_relative: bool


@dataclass
class StitchingProgressEvent:
    progress_message: str


class EventBus:
    def __init__(self):
        self._subscribers: Dict[type, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: type, callback: Callable):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: type, callback: Callable):
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)

    def publish(self, event):
        event_type = type(event)
        with self._lock:
            subscribers = self._subscribers.get(event_type, []).copy()

        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event callback: {e}")

    def clear_all_subscribers(self):
        with self._lock:
            self._subscribers.clear()


# Global event bus instance
event_bus = EventBus()