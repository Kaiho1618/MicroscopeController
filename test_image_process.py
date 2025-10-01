#!/usr/bin/env python3
"""
Test script for image processing service
"""

import cv2
import numpy as np
from service.image_process_service import create_image_process_service
from utils import config_loader


def create_test_images(count: int, size: tuple = (200, 200)) -> list:
    """Create test images with different patterns"""
    images = []
    height, width = size

    for i in range(count):
        # Create a test image with different patterns
        img = np.zeros((height, width, 3), dtype=np.uint8)

        # Add some pattern based on index
        color = (
            (i * 50) % 256,
            (i * 80) % 256,
            (i * 120) % 256
        )

        # Add rectangle
        cv2.rectangle(img, (20, 20), (width-20, height-20), color, -1)

        # Add text
        cv2.putText(img, f"IMG {i+1}", (width//4, height//2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Add some noise
        noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
        img = cv2.add(img, noise)

        images.append(img)

    return images


def test_image_concatenation():
    """Test image concatenation functionality"""
    print("Testing image processing service...")

    # Load config
    config = config_loader.load_config("settings/config.yaml")

    # Create image process service
    image_process_service = create_image_process_service(config)

    # Test cases
    test_cases = [
        {"grid_x": 2, "grid_y": 2, "name": "2x2 grid"},
        {"grid_x": 3, "grid_y": 2, "name": "3x2 grid"},
        {"grid_x": 1, "grid_y": 3, "name": "1x3 grid"},
    ]

    for test_case in test_cases:
        grid_x = test_case["grid_x"]
        grid_y = test_case["grid_y"]
        name = test_case["name"]

        print(f"\nTesting {name}...")

        # Create test images
        num_images = grid_x * grid_y
        test_images = create_test_images(num_images)

        # Concatenate images
        result = image_process_service.concatenate(
            stitching_type="grid",
            images=test_images,
            grid_size_x=grid_x,
            grid_size_y=grid_y
        )

        if result is not None:
            print(f"✓ Successfully created stitched image: {result.shape}")

            # Save result for visual inspection
            output_path = f"test_output_{grid_x}x{grid_y}.png"
            cv2.imwrite(output_path, result)
            print(f"  Saved to: {output_path}")
        else:
            print("✗ Failed to create stitched image")

    # Test error cases
    print("\nTesting error cases...")

    # Test with wrong number of images
    test_images = create_test_images(3)  # Wrong count
    result = image_process_service.concatenate(
        stitching_type="grid",
        images=test_images,
        grid_size_x=2,
        grid_size_y=2  # Expects 4 images, got 3
    )

    if result is None:
        print("✓ Correctly handled wrong image count")
    else:
        print("✗ Should have failed with wrong image count")

    # Test with empty image list
    result = image_process_service.concatenate(
        stitching_type="grid",
        images=[],
        grid_size_x=2,
        grid_size_y=2
    )

    if result is None:
        print("✓ Correctly handled empty image list")
    else:
        print("✗ Should have failed with empty image list")

    print("\nImage processing service test completed!")


def test_enhancement_functions():
    """Test image enhancement utilities"""
    print("\nTesting image enhancement functions...")

    config = config_loader.load_config("settings/config.yaml")
    image_process_service = create_image_process_service(config)

    # Create a test image
    test_img = create_test_images(1)[0]

    # Test contrast enhancement
    enhanced = image_process_service.enhance_contrast(test_img)
    if enhanced is not None:
        print("✓ Contrast enhancement works")
        cv2.imwrite("test_contrast_enhanced.png", enhanced)
    else:
        print("✗ Contrast enhancement failed")

    # Test sharpening
    sharpened = image_process_service.apply_sharpening(test_img)
    if sharpened is not None:
        print("✓ Sharpening works")
        cv2.imwrite("test_sharpened.png", sharpened)
    else:
        print("✗ Sharpening failed")


if __name__ == "__main__":
    test_image_concatenation()
    test_enhancement_functions()