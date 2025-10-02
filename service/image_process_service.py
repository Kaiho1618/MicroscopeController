from typing import Dict, Any, List
import cv2
import numpy as np

from application.event_bus import event_bus, ErrorEvent
from enums.enums import StitchingType

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

            if stitching_type == StitchingType.SIMPLE.value:
                return self._concatenate_grid(images, grid_size_x, grid_size_y)
            elif stitching_type == StitchingType.ADVANCED.value:
                return self._concatenate_advanced(images, grid_size_x, grid_size_y)
            else:
                raise ValueError(f"Unsupported stitching type: {stitching_type}")

        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to concatenate images: {str(e)}")
            event_bus.publish(error_event)
            return None

    def _concatenate_grid(self, images: List[Any], grid_size_x: int, grid_size_y: int) -> Any:
        """Simple grid concatenation with overlap from config"""
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

        # Get overlap ratio from config
        overlap_ratio = self.config.get('stitching', {}).get('overlap_ratio', 0.1)

        # Calculate overlap in pixels
        overlap_x = int(img_width * overlap_ratio)
        overlap_y = int(img_height * overlap_ratio)

        # Calculate step size (image size minus overlap)
        step_x = img_width - overlap_x
        step_y = img_height - overlap_y

        # Create output image with overlap accounted for
        output_height = step_y * (grid_size_y - 1) + img_height
        output_width = step_x * (grid_size_x - 1) + img_width

        if channels == 1:
            stitched_image = np.zeros((output_height, output_width), dtype=processed_images[0].dtype)
        else:
            stitched_image = np.zeros((output_height, output_width, channels), dtype=processed_images[0].dtype)

        # Arrange images in grid pattern with overlap
        idx = 0
        for y in range(grid_size_y):
            for x in range(grid_size_x):
                start_y = y * step_y
                end_y = start_y + img_height
                start_x = x * step_x
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
        """Advanced concatenation with adaptive overlap adjustment by minimizing region differences"""
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

        # Get initial overlap ratio from config
        overlap_ratio = self.config.get('stitching', {}).get('overlap_ratio', 0.1)

        # Calculate initial overlap in pixels
        initial_overlap_x = int(img_width * overlap_ratio)
        initial_overlap_y = int(img_height * overlap_ratio)

        # Build stitched image row by row
        rows = []
        for y in range(grid_size_y):
            row_images = []
            for x in range(grid_size_x):
                # Handle zigzag pattern
                if y % 2 == 0:  # Even rows: left to right
                    grid_x = x
                else:  # Odd rows: right to left
                    grid_x = grid_size_x - 1 - x

                img_idx = y * grid_size_x + grid_x
                if img_idx < len(processed_images):
                    current_img = processed_images[img_idx]
                    if current_img.shape[:2] != (img_height, img_width):
                        current_img = cv2.resize(current_img, (img_width, img_height))
                    row_images.append(current_img)

            # Stitch images horizontally with adaptive overlap
            if row_images:
                row_stitched = self._stitch_horizontal_adaptive(row_images, initial_overlap_x)
                rows.append(row_stitched)

        # Stitch rows vertically with adaptive overlap
        if not rows:
            raise ValueError("No rows to stitch")

        result = self._stitch_vertical_adaptive(rows, initial_overlap_y)
        return result

    def _stitch_horizontal_adaptive(self, images: List[np.ndarray], initial_overlap: int) -> np.ndarray:
        """Stitch images horizontally with adaptive overlap to minimize differences"""
        if len(images) == 0:
            raise ValueError("No images to stitch")
        if len(images) == 1:
            return images[0]

        result = images[0].copy()

        for i in range(1, len(images)):
            # Find optimal overlap by minimizing difference in overlap region
            overlap = self._find_optimal_horizontal_overlap(result, images[i], initial_overlap)

            # Merge with the found overlap
            result = self._merge_horizontal(result, images[i], overlap)

        return result

    def _stitch_vertical_adaptive(self, images: List[np.ndarray], initial_overlap: int) -> np.ndarray:
        """Stitch images vertically with adaptive overlap to minimize differences"""
        if len(images) == 0:
            raise ValueError("No images to stitch")
        if len(images) == 1:
            return images[0]

        result = images[0].copy()

        for i in range(1, len(images)):
            # Find optimal overlap by minimizing difference in overlap region
            overlap = self._find_optimal_vertical_overlap(result, images[i], initial_overlap)

            # Merge with the found overlap
            result = self._merge_vertical(result, images[i], overlap)

        return result

    def _find_optimal_horizontal_overlap(self, img1: np.ndarray, img2: np.ndarray, initial_overlap: int) -> int:
        """Find optimal horizontal overlap by minimizing pixel differences"""
        # Search range: ±20% of initial overlap
        search_range = max(int(initial_overlap * 0.2), 10)
        min_overlap = max(1, initial_overlap - search_range)
        max_overlap = min(img1.shape[1], img2.shape[1], initial_overlap + search_range)

        best_overlap = initial_overlap
        min_diff = float('inf')

        for overlap in range(min_overlap, max_overlap + 1):
            # Get right edge of img1 and left edge of img2
            region1 = img1[:, -overlap:]
            region2 = img2[:, :overlap]

            # Match heights if different
            min_height = min(region1.shape[0], region2.shape[0])
            region1 = region1[:min_height]
            region2 = region2[:min_height]

            # Calculate mean squared difference
            diff = np.mean((region1.astype(float) - region2.astype(float)) ** 2)

            if diff < min_diff:
                min_diff = diff
                best_overlap = overlap

        return best_overlap

    def _find_optimal_vertical_overlap(self, img1: np.ndarray, img2: np.ndarray, initial_overlap: int) -> int:
        """Find optimal vertical overlap by minimizing pixel differences"""
        # Search range: ±20% of initial overlap
        search_range = max(int(initial_overlap * 0.2), 10)
        min_overlap = max(1, initial_overlap - search_range)
        max_overlap = min(img1.shape[0], img2.shape[0], initial_overlap + search_range)

        best_overlap = initial_overlap
        min_diff = float('inf')

        for overlap in range(min_overlap, max_overlap + 1):
            # Get bottom edge of img1 and top edge of img2
            region1 = img1[-overlap:, :]
            region2 = img2[:overlap, :]

            # Match widths if different
            min_width = min(region1.shape[1], region2.shape[1])
            region1 = region1[:, :min_width]
            region2 = region2[:, :min_width]

            # Calculate mean squared difference
            diff = np.mean((region1.astype(float) - region2.astype(float)) ** 2)

            if diff < min_diff:
                min_diff = diff
                best_overlap = overlap

        return best_overlap

    def _merge_horizontal(self, img1: np.ndarray, img2: np.ndarray, overlap: int) -> np.ndarray:
        """Merge two images horizontally with linear blending in overlap region"""
        height = max(img1.shape[0], img2.shape[0])
        width = img1.shape[1] + img2.shape[1] - overlap

        # Resize if heights don't match
        if img1.shape[0] != height:
            img1 = cv2.resize(img1, (img1.shape[1], height))
        if img2.shape[0] != height:
            img2 = cv2.resize(img2, (img2.shape[1], height))

        # Create output array
        if len(img1.shape) == 3:
            result = np.zeros((height, width, img1.shape[2]), dtype=img1.dtype)
        else:
            result = np.zeros((height, width), dtype=img1.dtype)

        # Copy non-overlapping part of img1
        result[:, :img1.shape[1] - overlap] = img1[:, :img1.shape[1] - overlap]

        # Blend overlapping region
        if overlap > 0:
            for i in range(overlap):
                alpha = i / overlap  # Linear blending weight
                col_idx1 = img1.shape[1] - overlap + i
                col_idx2 = i
                result_col = img1.shape[1] - overlap + i

                result[:, result_col] = ((1 - alpha) * img1[:, col_idx1].astype(float) +
                                         alpha * img2[:, col_idx2].astype(float)).astype(img1.dtype)

        # Copy non-overlapping part of img2
        result[:, img1.shape[1]:] = img2[:, overlap:]

        return result

    def _merge_vertical(self, img1: np.ndarray, img2: np.ndarray, overlap: int) -> np.ndarray:
        """Merge two images vertically with linear blending in overlap region"""
        width = max(img1.shape[1], img2.shape[1])
        height = img1.shape[0] + img2.shape[0] - overlap

        # Resize if widths don't match
        if img1.shape[1] != width:
            img1 = cv2.resize(img1, (width, img1.shape[0]))
        if img2.shape[1] != width:
            img2 = cv2.resize(img2, (width, img2.shape[0]))

        # Create output array
        if len(img1.shape) == 3:
            result = np.zeros((height, width, img1.shape[2]), dtype=img1.dtype)
        else:
            result = np.zeros((height, width), dtype=img1.dtype)

        # Copy non-overlapping part of img1
        result[:img1.shape[0] - overlap, :] = img1[:img1.shape[0] - overlap, :]

        # Blend overlapping region
        if overlap > 0:
            for i in range(overlap):
                alpha = i / overlap  # Linear blending weight
                row_idx1 = img1.shape[0] - overlap + i
                row_idx2 = i
                result_row = img1.shape[0] - overlap + i

                result[result_row, :] = ((1 - alpha) * img1[row_idx1, :].astype(float) +
                                         alpha * img2[row_idx2, :].astype(float)).astype(img1.dtype)

        # Copy non-overlapping part of img2
        result[img1.shape[0]:, :] = img2[overlap:, :]

        return result

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