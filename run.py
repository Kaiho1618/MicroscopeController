from utils import config_loader
from service.controller_service import create_controller_service
import time
from service.file_service import FileService
from service.image_service import create_image_service

if __name__ == "__main__":
    config_path = "settings/config.yaml"
    config = config_loader.main(config_path)
    print("Loaded configuration:", config)

    controller_service = create_controller_service(config)
    image_service = create_image_service(config)
    file_service = FileService(config)

    for i in range(12):
        image = image_service.capture()
        if image is not None:
            save_path = f"output/mock_image_{i}.png"
            file_service.save_image(image, save_path)

        success_flg = controller_service.move_to(10.0, 0.0, is_relative=True)
        time.sleep(1)
        if not success_flg:
            print("Move out of bounds, stopping test.")
