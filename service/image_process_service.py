from typing import Dict, Any, List
import cv2
import numpy as np
from application.event_bus import event_bus, ErrorEvent


class ImageProcessService:
    """Production image processing service"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def concatenate(self, stitching_type: str, images: List[Any], grid_size_x: int, grid_size_y: int) -> Any:
        """
        Concatenate images for stitching

        Args:
            stitching_type: Type of stitching ("grid", "advanced", etc.)
            images: List of images to concatenate
            grid_size_x: Number of images in X direction
            grid_size_y: Number of images in Y direction

        Returns:
            Concatenated image as numpy array
        """
        try:
            if not images:
                raise ValueError("No images to concatenate")

            if stitching_type == "grid":
                return self._concatenate_grid(images, grid_size_x, grid_size_y)
            elif stitching_type == "advanced":
                return self._concatenate_advanced(images, grid_size_x, grid_size_y)
            else:
                raise ValueError(f"Unsupported stitching type: {stitching_type}")

        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to concatenate images: {str(e)}")
            event_bus.publish(error_event)
            return None

    def _concatenate_grid(self, images: List[Any], grid_size_x: int, grid_size_y: int) -> Any:
        """Simple grid concatenation without blending"""
        if len(images) != grid_size_x * grid_size_y:
            raise ValueError(f"Expected {grid_size_x * grid_size_y} images, got {len(images)}")

        # Convert all images to numpy arrays
        processed_images = []
        for img in images:
            if isinstance(img, np.ndarray):
                processed_images.append(img)
            else:
                processed_images.append(np.array(img))

        # Get dimensions from first image
        if len(processed_images[0].shape) == 3:
            img_height, img_width, channels = processed_images[0].shape
        else:
            img_height, img_width = processed_images[0].shape
            channels = 1

        # Create output image
        output_height = img_height * grid_size_y
        output_width = img_width * grid_size_x

        if channels == 1:
            stitched_image = np.zeros((output_height, output_width), dtype=processed_images[0].dtype)
        else:
            stitched_image = np.zeros((output_height, output_width, channels), dtype=processed_images[0].dtype)

        # Arrange images in grid pattern
        idx = 0
        for y in range(grid_size_y):
            for x in range(grid_size_x):
                start_y = y * img_height
                end_y = start_y + img_height
                start_x = x * img_width
                end_x = start_x + img_width

                # Handle zigzag pattern
                if y % 2 == 0:  # Even rows: left to right
                    grid_x = x
                else:  # Odd rows: right to left
                    grid_x = grid_size_x - 1 - x

                img_idx = y * grid_size_x + grid_x

                if img_idx < len(processed_images):
                    current_img = processed_images[img_idx]
                    if current_img.shape[:2] == (img_height, img_width):
                        stitched_image[start_y:end_y, start_x:end_x] = current_img
                    else:
                        resized_img = cv2.resize(current_img, (img_width, img_height))
                        stitched_image[start_y:end_y, start_x:end_x] = resized_img

        return stitched_image

    def _concatenate_advanced(self, images: List[Any], grid_size_x: int, grid_size_y: int) -> Any:
        """Advanced concatenation with feature matching and blending"""
        # This would implement more sophisticated stitching algorithms
        # For now, fall back to grid concatenation
        return self._concatenate_grid(images, grid_size_x, grid_size_y)

    def _find_overlap_region(self, img1: np.ndarray, img2: np.ndarray, overlap_ratio: float = 0.1) -> tuple:
        """Find overlap region between two images (for future advanced stitching)"""
        # Placeholder for feature matching and overlap detection
        pass

    def _blend_images(self, img1: np.ndarray, img2: np.ndarray, overlap_region: tuple) -> np.ndarray:
        """Blend overlapping regions of two images (for future advanced stitching)"""
        # Placeholder for image blending algorithms
        pass

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast (utility function)"""
        try:
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            if len(image.shape) == 3:
                # Convert to LAB color space
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)

                # Apply CLAHE to lightness channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)

                # Merge channels and convert back to BGR
                enhanced = cv2.merge([l, a, b])
                return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            else:
                # Grayscale image
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                return clahe.apply(image)

        except Exception as e:
            print(f"Warning: Failed to enhance contrast: {e}")
            return image

    def apply_sharpening(self, image: np.ndarray) -> np.ndarray:
        """Apply sharpening filter to image (utility function)"""
        try:
            # Sharpening kernel
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            return cv2.filter2D(image, -1, kernel)
        except Exception as e:
            print(f"Warning: Failed to apply sharpening: {e}")
            return image