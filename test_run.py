import time
import tkinter as tk
import threading
import argparse

from utils import config_loader
from service.file_service import FileService
from service.image_service import create_image_service
from service.controller_service import create_controller_service
from service.image_process_service import ImageProcessService
from presentation.gui import MicroscopeGUI
from application.manual_controller import ManualController
from application.stitching_controller import StitchingController
from application.event_bus import event_bus
from mock.test_env import test_env
from enums.enums import CameraMagnitude, CornerPosition


def stitching_test():
    config = config_loader.load_config("settings/config.yaml")
    controller_service = create_controller_service(config)
    image_service = create_image_service(config)
    image_process_service = ImageProcessService(config)
    file_service = FileService(config)
    magnitude=CameraMagnitude.MAG_5X

    stitching_controller = StitchingController(
        config,
        controller_service,
        image_service,
        image_process_service,
    )

    stitching_controller.start()
    stitching_controller.stitching(
        grid_size_x=3,
        grid_size_y=3,
        magnitude=CameraMagnitude.MAG_5X,
        corner=CornerPosition.TOP_LEFT
    )


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microscope Controller GUI')
    parser.add_argument('--mock', action='store_true', help='Use mock environment instead of real hardware')
    args = parser.parse_args()

    # Load config with mock override from command line
    config = config_loader.load_config("settings/config.yaml", mock_override=args.mock)

    # Display current mode
    mode = "MOCK" if config.get('mock', False) else "REAL"
    print(f"Starting Microscope Controller in {mode} mode")

    controller_service = create_controller_service(config)
    image_service = create_image_service(config)
    image_process_service = ImageProcessService(config)
    file_service = FileService(config)

    # Initialize manual controller
    manual_controller = ManualController(
        config,
        controller_service,
        image_service,
    )

    stitching_controller = StitchingController(
        config,
        controller_service,
        image_service,
        image_process_service,
    )

    root = tk.Tk()
    app = MicroscopeGUI(
        root, config, controller_service, image_service, file_service, manual_controller, stitching_controller
    )

    stop_event = threading.Event()
    def update_test_env():
        """Update test environment every 20ms"""
        while not stop_event.is_set():
            try:
                test_env.update()
            except Exception as e:
                print(f"Error in test_env.update: {e}")
            time.sleep(0.05)

    # Start the update thread as daemon only if mock mode is enabled
    if config.get('mock', False):
        update_thread = threading.Thread(target=update_test_env, daemon=True)
        update_thread.start()

    # Handle window closing
    def on_closing():
        app.stop_auto_capture()  # Stop auto capture timer
        app.manual_controller.stop()
        event_bus.clear_all_subscribers()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    print("Application closed.")


if __name__ == "__main__":
    main()
    # stitching_test()
