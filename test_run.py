from utils import config_loader
import time
import tkinter as tk
import threading

from service.file_service import FileService
from service.image_service import create_image_service
from service.controller_service import create_controller_service
from presentation.gui import ManualControllerGUI
from application.manual_controller import ManualController
from application.event_bus import event_bus
from mock.test_env import test_env


def main():
    config = config_loader.load_config("settings/config.yaml")
    controller_service = create_controller_service(config)
    image_service = create_image_service(config)
    file_service = FileService(config)

    root = tk.Tk()
    app = ManualControllerGUI(
        root, config, controller_service, image_service, file_service
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
    
    # Start the update thread as daemon
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
    print("Move out of bounds, stopping test.")


if __name__ == "__main__":
    main()