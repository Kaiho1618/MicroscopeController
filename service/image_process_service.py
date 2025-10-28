from typing import Dict, Any, List, Tuple
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
                return self._concatenate_grid2(images, grid_size_x, grid_size_y)
            elif stitching_type == StitchingType.FEATURE_BASED.value:
                return self._concatenate_grid_features(images, grid_size_x, grid_size_y)
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


    def _concatenate_grid2(self, images: List[Any], grid_size_x: int, grid_size_y: int) -> Any:
        """Grid concatenation with alignment and blending"""
        if len(images) != grid_size_x * grid_size_y:
            raise ValueError(f"Expected {grid_size_x * grid_size_y} images, got {len(images)}")

        images = self._reorder_images_zigzag(images, grid_size_x, grid_size_y)
        # Convert all images to numpy arrays
        processed_images = []
        for img in images:
            if isinstance(img, np.ndarray):
                processed_images.append(img)
            else:
                processed_images.append(np.array(img))

        # Get dimensions
        if len(processed_images[0].shape) == 3:
            img_height, img_width, channels = processed_images[0].shape
        else:
            img_height, img_width = processed_images[0].shape
            channels = 1
            # Convert grayscale to 3-channel for processing
            processed_images = [cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if len(img.shape) == 2 else img 
                            for img in processed_images]


        # Get overlap ratio from config
        overlap_ratio = self.config.get('stitching', {}).get('overlap_ratio', 0.1)
        overlap_x = int(img_width * overlap_ratio)
        overlap_y = int(img_height * overlap_ratio)

        # Build grid with alignment
        aligned_positions = self._align_grid(
            processed_images, grid_size_x, grid_size_y,
            overlap_x, overlap_y, img_width, img_height
        )

        # Create canvas and blend images
        stitched_image = self._blend_images(
            processed_images, aligned_positions,
            grid_size_x, grid_size_y, img_width, img_height
        )

        # Convert back to grayscale if original was grayscale
        if channels == 1:
            stitched_image = cv2.cvtColor(stitched_image, cv2.COLOR_BGR2GRAY)

        return stitched_image

    def _concatenate_grid_features(self, images: List[Any], grid_size_x: int, grid_size_y: int) -> Any:
        """Grid concatenation with feature-based alignment and blending"""
        if len(images) != grid_size_x * grid_size_y:
            raise ValueError(f"Expected {grid_size_x * grid_size_y} images, got {len(images)}")

        images = self._reorder_images_zigzag(images, grid_size_x, grid_size_y)
        # Convert all images to numpy arrays
        processed_images = []
        for img in images:
            if isinstance(img, np.ndarray):
                processed_images.append(img)
            else:
                processed_images.append(np.array(img))

        # Get dimensions
        if len(processed_images[0].shape) == 3:
            img_height, img_width, channels = processed_images[0].shape
        else:
            img_height, img_width = processed_images[0].shape
            channels = 1
            # Convert grayscale to 3-channel for processing
            processed_images = [cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if len(img.shape) == 2 else img
                            for img in processed_images]

        # Get overlap ratio from config
        overlap_ratio = self.config.get('stitching', {}).get('overlap_ratio', 0.1)
        overlap_x = int(img_width * overlap_ratio)
        overlap_y = int(img_height * overlap_ratio)

        # Build grid with feature-based alignment
        aligned_positions = self._align_grid_features(
            processed_images, grid_size_x, grid_size_y,
            overlap_x, overlap_y, img_width, img_height
        )

        # Create canvas and blend images
        stitched_image = self._blend_images(
            processed_images, aligned_positions,
            grid_size_x, grid_size_y, img_width, img_height
        )

        # Convert back to grayscale if original was grayscale
        if channels == 1:
            stitched_image = cv2.cvtColor(stitched_image, cv2.COLOR_BGR2GRAY)

        return stitched_image

    def _align_grid(self, images: List[np.ndarray], grid_x: int, grid_y: int,
                    overlap_x: int, overlap_y: int, img_w: int, img_h: int) -> List[Tuple[int, int]]:
        """
        Align images using phase correlation on overlap regions
        以下の順に並べていく
        123
        456
        789
        """
        # Pre-allocate positions array to match image indices
        num_images = grid_x * grid_y
        positions = [None] * num_images

        # Start with first image at origin
        positions[0] = (0, 0)
        
        for y in range(grid_y):
            for x in range(grid_x):
                if y == 0 and x == 0:
                    continue  # Skip first image already placed
                
                current_idx = y * grid_x + x
                current_img = images[current_idx]

                new_x = img_w * x - overlap_x * x
                new_y = img_h * y - overlap_y * y

                if x > 0:  # Left neighbor exists
                    ref_idx = current_idx - 1
                    ref_img = images[ref_idx]
                    ref_pos = positions[ref_idx]

                    ref_region = ref_img[:, -overlap_x:]
                    curr_region = current_img[:, :overlap_x]    
                    left_shift = self._find_alignment(ref_region, curr_region)
                    
                    if left_shift is not None:
                        new_y = ref_pos[1] - left_shift[1]
                if y > 0:  # Top neighbor exists
                    ref_idx = current_idx - grid_x
                    ref_img = images[ref_idx]
                    ref_pos = positions[ref_idx]

                    ref_region = ref_img[-overlap_y:, :]
                    curr_region = current_img[:overlap_y, :]

                    top_shift = self._find_alignment(ref_region, curr_region)
                    # valid_x_shift = abs(top_shift[0]) < overlap_x * 0.1
                    # valid_y_shift = abs(top_shift[1]) < overlap_y * 0.1
                    # if valid_x_shift and valid_y_shift:
                    if top_shift is not None:
                        new_x = ref_pos[0] - top_shift[0]

                positions[current_idx] = (int(new_x), int(new_y))

        return positions

    def _align_grid_features(self, images: List[np.ndarray], grid_x: int, grid_y: int,
                    overlap_x: int, overlap_y: int, img_w: int, img_h: int) -> List[Tuple[int, int]]:
        """
        Align images using feature matching on overlap regions
        以下の順に並べていく
        123
        456
        789
        """
        # Pre-allocate positions array to match image indices
        num_images = grid_x * grid_y
        positions = [None] * num_images

        # Start with first image at origin
        positions[0] = (0, 0)

        for y in range(grid_y):
            for x in range(grid_x):
                if y == 0 and x == 0:
                    continue  # Skip first image already placed

                current_idx = y * grid_x + x
                current_img = images[current_idx]

                new_x = img_w * x - overlap_x * x
                new_y = img_h * y - overlap_y * y

                if x > 0:  # Left neighbor exists
                    ref_idx = current_idx - 1
                    ref_img = images[ref_idx]
                    ref_pos = positions[ref_idx]

                    ref_region = ref_img[:, -overlap_x:]
                    curr_region = current_img[:, :overlap_x]
                    left_shift = self._find_alignment_features(ref_region, curr_region)

                    if left_shift is not None:
                        new_y = ref_pos[1] - left_shift[1]

                if y > 0:  # Top neighbor exists
                    ref_idx = current_idx - grid_x
                    ref_img = images[ref_idx]
                    ref_pos = positions[ref_idx]

                    ref_region = ref_img[-overlap_y:, :]
                    curr_region = current_img[:overlap_y, :]

                    top_shift = self._find_alignment_features(ref_region, curr_region)

                    if top_shift is not None:
                        new_x = ref_pos[0] - top_shift[0]

                positions[current_idx] = (int(new_x), int(new_y))

        return positions

    def _find_alignment(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[int, int]:
        """
        Find alignment between two overlapping regions using phase correlation
        returns (shift_x, shift_y)
        """
        # Convert to grayscale if needed
        if len(img1.shape) == 3:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        else:
            gray1, gray2 = img1, img2

        # ノイズの影響をなくすためにガウシアンフィルタ→微分フィルタ→二値化
        # gray1 = cv2.GaussianBlur(gray1, (5, 5), 0)
        # gray2 = cv2.GaussianBlur(gray2, (5, 5), 0)

        _, binary1 = cv2.threshold(gray1, 0, 255, cv2.THRESH_OTSU)
        _, binary2 = cv2.threshold(gray2, 0, 255, cv2.THRESH_OTSU)

        # gray1 = gray1.astype(np.float32)
        # gray2 = gray2.astype(np.float32)
        # gray1 -= np.mean(gray1)
        # gray2 -= np.mean(gray2)

        binary1 = binary1.astype(np.float32)
        binary2 = binary2.astype(np.float32)

        # Use phase correlation for sub-pixel accuracy
        shift, response = cv2.phaseCorrelate(
            np.float32(binary1),
            np.float32(binary2),
        )

        # Only use shift if correlation is strong enough
        if response > 0.1:  # Threshold for confidence
            return (int(round(shift[0])), int(round(shift[1])))
        else:
            return None

    def _find_alignment_features(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[int, int]:
        """
        Find alignment between two overlapping regions using feature matching
        Uses ORB or AKAZE keypoint detection and matching
        returns (shift_x, shift_y)
        """
        # Convert to grayscale if needed
        if len(img1.shape) == 3:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        else:
            gray1, gray2 = img1, img2

        _, binary1 = cv2.threshold(gray1, 0, 255, cv2.THRESH_OTSU)
        _, binary2 = cv2.threshold(gray2, 0, 255, cv2.THRESH_OTSU)

        try:
            # Try AKAZE first (better quality, but might fail on some images)
            detector = cv2.AKAZE_create()
            kp1, des1 = detector.detectAndCompute(binary1, None)
            kp2, des2 = detector.detectAndCompute(binary2, None)

            # If not enough keypoints found, try ORB
            if len(kp1) < 10 or len(kp2) < 10:
                detector = cv2.ORB_create(nfeatures=1000)
                kp1, des1 = detector.detectAndCompute(binary1, None)
                kp2, des2 = detector.detectAndCompute(binary1, None)

            # Check if we have enough keypoints
            if len(kp1) < 4 or len(kp2) < 4 or des1 is None or des2 is None:
                return None

            # Match features using BFMatcher
            if detector.__class__.__name__ == 'AKAZE':
                matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            else:
                matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

            # Use KNN matching to get best 2 matches for each descriptor
            matches = matcher.knnMatch(des1, des2, k=2)

            # Apply ratio test (Lowe's ratio test)
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.75 * n.distance:
                        good_matches.append(m)

            # Need at least 4 good matches
            if len(good_matches) < 4:
                return None

            # Extract matched keypoint coordinates
            pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])
            pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])

            # Calculate shifts
            shifts = pts1 - pts2

            # Use median shift to be robust against outliers
            median_shift_x = np.median(shifts[:, 0])
            median_shift_y = np.median(shifts[:, 1])

            # Filter outliers: keep only shifts close to median
            tolerance = 20  # pixels
            mask = (np.abs(shifts[:, 0] - median_shift_x) < tolerance) & \
                   (np.abs(shifts[:, 1] - median_shift_y) < tolerance)

            if np.sum(mask) < 4:
                return None

            # Calculate mean shift from inliers
            inlier_shifts = shifts[mask]
            mean_shift_x = np.mean(inlier_shifts[:, 0])
            mean_shift_y = np.mean(inlier_shifts[:, 1])

            # Calculate confidence based on number of inliers and consistency
            confidence = np.sum(mask) / len(good_matches)
            shift_std = np.std(inlier_shifts, axis=0)
            consistency = 1.0 / (1.0 + np.mean(shift_std))

            overall_confidence = confidence * consistency

            # Only return shift if confidence is high enough
            if overall_confidence > 0.3:
                return (int(round(mean_shift_x)), int(round(mean_shift_y)))
            else:
                return None

        except Exception as e:
            # If feature matching fails, return None
            return None

    def _blend_images(self, images: List[np.ndarray], positions: List[Tuple[int, int]],
                    grid_x: int, grid_y: int, img_w: int, img_h: int) -> np.ndarray:
        """Blend images with feathering in overlap regions"""
        # Calculate canvas size
        max_x = max(pos[0] + img_w for pos in positions)
        max_y = max(pos[1] + img_h for pos in positions)
        min_x = min(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        
        canvas_w = max_x - min_x
        canvas_h = max_y - min_y
        
        # Adjust positions to canvas
        adjusted_positions = [(x - min_x, y - min_y) for x, y in positions]
        
        # Create output and weight accumulator
        output = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
        weights = np.zeros((canvas_h, canvas_w), dtype=np.float32)
        
        # Create feathering weight mask
        weight_mask = self._create_weight_mask(img_h, img_w)
        
        # Blend each image
        for idx, (x, y) in enumerate(adjusted_positions):
            img_idx = idx
            
            img = images[img_idx].astype(np.float32)
            
            # Ensure we don't go out of bounds
            y_end = min(y + img_h, canvas_h)
            x_end = min(x + img_w, canvas_w)
            y_start = max(0, y)
            x_start = max(0, x)
            
            # Crop weight mask if at edges
            mask_y_start = y_start - y
            mask_x_start = x_start - x
            mask_y_end = mask_y_start + (y_end - y_start)
            mask_x_end = mask_x_start + (x_end - x_start)
            
            current_mask = weight_mask[mask_y_start:mask_y_end, mask_x_start:mask_x_end]
            current_img = img[mask_y_start:mask_y_end, mask_x_start:mask_x_end]
            
            # Accumulate weighted image
            output[y_start:y_end, x_start:x_end] += current_img * current_mask[:, :, np.newaxis]
            weights[y_start:y_end, x_start:x_end] += current_mask
        
        # Normalize by weights
        weights[weights == 0] = 1  # Avoid division by zero
        output = output / weights[:, :, np.newaxis]
        
        return output.astype(np.uint8)


    def _create_weight_mask(self, height: int, width: int, feather_pixels: int = 50) -> np.ndarray:
        """Create a weight mask with feathering at edges"""
        mask = np.ones((height, width), dtype=np.float32)
        
        # Apply feathering to all edges
        for i in range(feather_pixels):
            weight = i / feather_pixels
            mask[i, :] = np.minimum(mask[i, :], weight)  # Top
            mask[height-1-i, :] = np.minimum(mask[height-1-i, :], weight)  # Bottom
            mask[:, i] = np.minimum(mask[:, i], weight)  # Left
            mask[:, width-1-i] = np.minimum(mask[:, width-1-i], weight)  # Right
        
        return mask


    def _reorder_images_zigzag(self, images: List[Any], grid_x: int, grid_y: int) -> List[Any]:
        """
        Reorder images from zigzag capture order to grid coordinate order
        
        Example:
        123
        654
        789
        to
        123
        456
        789
        """
        if len(images) != grid_x * grid_y:
            raise ValueError(f"Expected {grid_x * grid_y} images, got {len(images)}")

        reordered_images = [None] * (grid_x * grid_y)

        for y in range(grid_y):
            for x in range(grid_x):
                if y % 2 == 0:
                    zigzag_index = y * grid_x + x
                else:
                    zigzag_index = y * grid_x + (grid_x - 1 - x)

                grid_index = y * grid_x + x
                reordered_images[grid_index] = images[zigzag_index]

        return reordered_images

   