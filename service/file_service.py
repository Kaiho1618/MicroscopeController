import cv2


class FileService:
    def __init__(self, config):
        self.config = config

    def save_image(self, image, path):
        cv2.imwrite(path, image)
        print(f"Image saved to {path}")
