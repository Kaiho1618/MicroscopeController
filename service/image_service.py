from typing import Dict, Any
import cv2
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
        self.connected = False
        self.connect()

    def connect(self):
        test_env.connect()
        self.connected = True
        print("Mock camera connected")

    def disconnect(self):
        """Disconnect mock camera"""
        self.connected = False
        print("Mock camera disconnected")

    def is_connected(self):
        """Check if camera is connected"""
        return self.connected

    def capture(self, refresh=False):
        try:
            if not self.connected:
                raise RuntimeError("Mock camera is not connected")
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

    def stop(self):
        """Stop mock camera"""
        self.disconnect()


class ImageService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cap = None
        self.connect()

    def connect(self):
        """カメラに接続"""
        camera_config = self.config["camera"]

        # DirectShow backend for Windows
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config["resolution_width"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config["resolution_height"])
        self.cap.set(cv2.CAP_PROP_FPS, camera_config["frame_rate"])

        print(f"Camera connected: {camera_config['resolution_width']}x{camera_config['resolution_height']} @ {camera_config['frame_rate']}fps")

    def disconnect(self):
        """カメラを切断"""
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Camera disconnected")

    def is_connected(self):
        """Check if camera is connected"""
        return self.cap is not None and self.cap.isOpened()

    def capture(self, refresh=False):
        """画像をキャプチャ"""
        try:
            if not self.cap or not self.cap.isOpened():
                raise RuntimeError("Camera is not connected")

            # Flush the camera buffer by reading and discarding several frames
            # This ensures we get the latest frame, not a buffered old frame
            if refresh:
                num_frames_to_flush = 5
                for _ in range(num_frames_to_flush):
                    self.cap.read()

            # Now read the actual frame
            ret, frame = self.cap.read()
            if not ret:
                raise RuntimeError("Failed to capture frame")

            print("Image captured successfully")

            # Publish image capture event
            event = ImageCaptureEvent(
                image_data=frame,
                timestamp=datetime.now()
            )
            event_bus.publish(event)

            return frame
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to capture image: {str(e)}")
            event_bus.publish(error_event)
            return None

    def stop(self):
        """カメラを停止してリソースを解放"""
        self.disconnect()


if __name__ == "__main__":
    # For direct testing in real environment
    test_config = {
        "mock": False,
        "camera": {
            "resolution_width": 1920,
            "resolution_height": 1080,
            "frame_rate": 10
        }
    }

    # Create real image service
    image_service = ImageService(test_config)

    print("ImageService initialized successfully")

    # Capture test image
    print("\nCapturing test image...")
    frame = image_service.capture()

    if frame is not None:
        # Save the captured image
        save_path = "output/test_capture.jpg"
        cv2.imwrite(save_path, frame)
        print(f"Image saved: {save_path} (shape: {frame.shape})")
    else:
        print("Failed to capture image")

    # Clean up
    image_service.stop()
    print("\nTest completed")
