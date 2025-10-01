from typing import Dict, Any
from mock.test_env import test_env
from application.event_bus import event_bus, StartMoveEvent, StopMoveEvent, MoveToEvent
from application.event_bus import ErrorEvent


def create_controller_service(config: Dict[str, Any]):
    mock = config["mock"]
    if mock:
        return MockControllerService(config)    
    return ControllerService(config)


class MockControllerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connect()
        self.setup_event_subscriptions()

    def connect(self):
        test_env.connect()

    def start_move(self, speed: float, degree: float):
        test_env.start_move(speed, degree)

    def stop_move(self):
        test_env.stop_move()

    def is_moving(self):
        return test_env.is_moving

    def move_to(self, x: float, y: float, is_relative: bool = True):
        return test_env.move_to(x, y, is_relative)

    def setup_event_subscriptions(self):
        event_bus.subscribe(StartMoveEvent, self.on_start_move)
        event_bus.subscribe(StopMoveEvent, self.on_stop_move)
        event_bus.subscribe(MoveToEvent, self.on_move_to)

    def on_start_move(self, event: StartMoveEvent):
        print(f"Controller Service: Start move - Speed: {event.speed}, Direction: {event.direction}")
        try:
            self.start_move(event.speed, event.direction)
            # Could publish a MoveStartedEvent here if needed
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to start move: {str(e)}")
            event_bus.publish(error_event)

    def on_stop_move(self, event: StopMoveEvent):
        print("Controller Service: Stop move")
        try:
            self.stop_move()
            # Could publish a MoveStoppedEvent here if needed
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to stop move: {str(e)}")
            event_bus.publish(error_event)

    def on_move_to(self, event: MoveToEvent):
        print(f"Controller Service: Move to {event.target_pos}, Relative: {event.is_relative}")
        try:
            self.move_to(event.target_pos[0], event.target_pos[1], event.is_relative)
            # Could publish a MoveCompletedEvent here if needed
        except Exception as e:
            from application.event_bus import ErrorEvent
            error_event = ErrorEvent(error_message=f"Failed to move to position: {str(e)}")
            event_bus.publish(error_event)

    def get_current_position(self):
        return test_env.get_current_position()

    def is_valid_movement(self, x, y, is_relative) -> bool:
        """指定座標への移動が範囲内かチェックする"""
        if is_relative:
            current_pos = self.get_current_position()
            x += current_pos[0]
            y += current_pos[1]
        return (test_env.min_x <= x <= test_env.max_x) and (test_env.min_y <= y <= test_env.max_y)


class ControllerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_event_subscriptions()

    def setup_event_subscriptions(self):
        event_bus.subscribe(StartMoveEvent, self.on_start_move)
        event_bus.subscribe(StopMoveEvent, self.on_stop_move)
        event_bus.subscribe(MoveToEvent, self.on_move_to)

    def on_start_move(self, event: StartMoveEvent):
        print(f"Controller Service: Start move - Speed: {event.speed}, Direction: {event.direction}")
        try:
            # Actual hardware control logic would go here
            pass
        except Exception as e:
            from application.event_bus import ErrorEvent
            error_event = ErrorEvent(error_message=f"Failed to start move: {str(e)}")
            event_bus.publish(error_event)

    def on_stop_move(self, event: StopMoveEvent):
        print("Controller Service: Stop move")
        try:
            # Actual hardware control logic would go here
            pass
        except Exception as e:
            from application.event_bus import ErrorEvent
            error_event = ErrorEvent(error_message=f"Failed to stop move: {str(e)}")
            event_bus.publish(error_event)

    def on_move_to(self, event: MoveToEvent):
        print(f"Controller Service: Move to {event.target_pos}, Relative: {event.is_relative}")
        try:
            # Actual hardware control logic would go here
            pass
        except Exception as e:
            from application.event_bus import ErrorEvent
            error_event = ErrorEvent(error_message=f"Failed to move to position: {str(e)}")
            event_bus.publish(error_event)

    def stop(self):
        # サービス停止のロジック
        event_bus.unsubscribe(StartMoveEvent, self.on_start_move)
        event_bus.unsubscribe(StopMoveEvent, self.on_stop_move)
        event_bus.unsubscribe(MoveToEvent, self.on_move_to)
