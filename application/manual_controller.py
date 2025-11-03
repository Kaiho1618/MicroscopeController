from typing import Dict, Any, Optional
from .event_bus import event_bus, ErrorEvent


class ManualController:
    def __init__(self, config: Dict[str, Any], controller_service, image_service):
        self.config = config
        self.controller_service = controller_service
        self.image_service = image_service
        self.is_active = False

    def start(self):
        self.is_active = True

    def stop(self):
        self.is_active = False
        if self.controller_service.is_moving():
            self.stop_move()

    def start_move(self, speed: float, key: str):
        if not self.is_active:
            return

        # Convert keyboard character to direction
        direction = self._key_to_direction(key)
        if direction is None:
            error_event = ErrorEvent(error_message=f"Invalid key: {key}")
            event_bus.publish(error_event)
            return

        try:
            print(f"Starting move - Speed: {speed}, Direction: {direction}")
            self.controller_service.start_move(speed, direction)
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to start move: {str(e)}")
            event_bus.publish(error_event)

    def _key_to_direction(self, key: str) -> Optional[float]:
        """Convert keyboard character to direction in degrees"""
        key_map = {
            'w': 90,     # Up
            'a': 180,   # Left
            's': 270,   # Down
            'd': 0,    # Right
        }
        return key_map.get(key.lower())

    def stop_move(self):
        try:
            # Publish stop move event
            self.controller_service.stop_move()
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to stop move: {str(e)}")
            event_bus.publish(error_event)

    def move_to(self, x: float, y: float, is_relative: bool = True):
        if not self.is_active:
            return

        try:
            # Publish move to event
            self.controller_service.move_to(x, y, is_relative)
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to move to position: {str(e)}")
            event_bus.publish(error_event)

    def capture_image(self):
        if not self.is_active:
            return None

        try:
            image_data = self.image_service.capture()
            return image_data
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to capture image: {str(e)}")
            event_bus.publish(error_event)
            return None
