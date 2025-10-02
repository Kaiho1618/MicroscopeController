"""
簡易テスト環境管理モジュール
XY平面のみのステージ移動をシミュレート（簡易版）
"""

import time
import cv2
import numpy as np


class TestEnv():
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        
        self.max_x = 1000.0  # ステージの最大X座標 [mm]
        self.max_y = 1000.0  # ステージの最大Y座標 [mm]
        self.min_x = 0.0    # ステージの最小X座標 [mm]
        self.min_y = 0.0    # ステージの最小Y座標 [mm]

        self.speed = 10.0  # ステージの移動速度 [mm/s]
        self.degree = 0.0  # 移動方向（角度）[度]

        self.start_time = time.time()
        self.is_moving = False
        self.mock_image = cv2.imread("mock/img/mock_image2.jpg")

    def connect(self) -> bool:
        """
        ステージコントローラに接続する
        """
        print("Mock: Connected.")
        return True

    def move_to(self, x: float, y: float, is_relative: bool = True) -> bool:
        """
        ステージを指定座標に移動する
        """
        nx = self.x
        ny = self.y

        if is_relative:
            nx += x
            ny += y
        else:
            nx = x
            ny = y

        # 範囲外チェック
        if self.min_x <= nx <= self.max_x and self.min_y <= ny <= self.max_y:
            self.x = nx
            self.y = ny
            print(f"Mock: Moved to ({self.x:.2f}, {self.y:.2f})")
            return True
        else:
            print(f"Error: Target position ({x}, {y}) out of bounds.")
            return False
    
    def start_move(self, speed: float, degree: float):

        # stopが押されたときに、まとめて移動する
        self.start_time = time.time()
        self.speed = speed
        self.degree = degree
        self.is_moving = True
    
    def stop_move(self):
        elapsed = time.time() - self.start_time

        distance = self.speed * elapsed
        dx = distance * np.cos(np.radians(self.degree))
        dy = distance * np.sin(np.radians(self.degree))

        self.move_to(dx, dy, is_relative=True)
        self.is_moving = False

    def capture(self):
        """
        位置に応じてimageをクリップすることでmock画像を作る
        座標と画像の左上を対応させる
        """
        if self.mock_image is None:
            print("Error: Mock image not found.")
            return None
        
        h, w, _ = self.mock_image.shape
        clip_size = 200  # クリップするサイズ [px]
        scale_x = w / (self.max_x - self.min_x)
        scale_y = h / (self.max_y - self.min_y)

        x1 = int(self.x * scale_x)
        y1 = int(self.y * scale_y)
        x1 = max(0, min(x1, w - clip_size))
        y1 = max(0, min(y1, h - clip_size))
        x2 = x1 + clip_size
        y2 = y1 + clip_size

        return self.mock_image[y1:y2, x1:x2]
    
    def display_status(self):
        print(f"Position: ({self.x:.2f}, {self.y:.2f}), Moving: {self.is_moving}")

    def update(self):
        if self.is_moving:
            elapsed = time.time() - self.start_time

            distance = self.speed * elapsed
            dx = distance * np.cos(np.radians(self.degree))
            dy = distance * np.sin(np.radians(self.degree))

            # 範囲外チェック
            if not self.move_to(dx, dy, is_relative=True):
                print("Reached boundary, stopping movement.")
                self.is_moving = False
            self.start_time = time.time()  # Reset start time for next update

    def get_current_position(self):
        return (self.x, self.y)


test_env = TestEnv()

# 使用例とテスト
if __name__ == "__main__":
    # テスト環境の作成
    
    try:
        # 初期化
        if not test_env.initialize():
            print("Failed to initialize test environment")
            exit(1)
        
        # 基本テスト
        if not test_env.run_basic_test():
            print("Basic test failed")
            exit(1)
        
        # スティッチングシミュレーション
        captured_data = test_env.simulate_stitching_pattern(2, 5.0)
        
        # 統計表示
        stats = test_env.get_test_statistics()
        print("\n=== Test Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # 手動移動テスト
        print("\nTesting manual movements...")
        positions = [(5, 0), (0, 5), (-5, 0), (0, -5), (0, 0)]
        for x, y in positions:
            test_env.stage_controller.move_to(x, y)
            test_env.total_movements += 1
            image = test_env.camera_controller.capture_image()
            if image is not None:
                test_env.total_captures += 1
        
    finally:
        # クリーンアップ
        test_env.shutdown()