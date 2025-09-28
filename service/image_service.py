from typing import Dict, Any
from mock.test_env import test_env


def create_image_service(config: Dict[str, Any]):
    mock = config["mock"]
    if mock:
        return MockImageService(config)
    return ImageService(config)

class MockImageService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connect()

    def connect(self):
        test_env.connect()
    
    def capture(self):
        test_env.display_status()
        return test_env.capture()


class ImageService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def stop(self):
        # サービス停止のロジック
        pass

