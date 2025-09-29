from typing import Dict, Any
from datetime import datetime
from mock.test_env import test_env
from application.event_bus import event_bus, ImageCaptureEvent, ErrorEvent


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
        try:
            print("Capturing image in MockImageService...")
            test_env.display_status()
            image_data = test_env.capture()
            # Publish image capture event
            event = ImageCaptureEvent(
                image_data=image_data,
                timestamp=datetime.now()
            )
            event_bus.publish(event)
            return image_data
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to capture image: {str(e)}")
            event_bus.publish(error_event)
            return None


class ImageService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def capture(self):
        try:
            # Actual camera capture logic would go here
            image_data = None  # Replace with actual capture
            # Publish image capture event
            event = ImageCaptureEvent(
                image_data=image_data,
                timestamp=datetime.now()
            )
            event_bus.publish(event)
            return image_data
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to capture image: {str(e)}")
            event_bus.publish(error_event)
            return None

    def stop(self):
        # サービス停止のロジック
        pass
