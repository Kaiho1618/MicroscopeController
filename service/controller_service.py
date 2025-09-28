from typing import Dict, Any
from mock.test_env import test_env


def create_controller_service(config: Dict[str, Any]):
    mock = config["mock"]
    if mock:
        return MockControllerService(config)    
    return ControllerService(config)

class MockControllerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connect()

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

class ControllerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def stop(self):
        # サービス停止のロジック
        pass
