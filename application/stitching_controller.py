from typing import Dict, Any, List, Tuple
from datetime import datetime
from application.event_bus import event_bus, ErrorEvent, StitchingProgressEvent, ImageCaptureEvent
from enums.stage import CornerPosition
from enums.camera import CameraMagnitude


class StitchingController:
    def __init__(self, config: Dict[str, Any], controller_service, image_service, image_process_service):
        self.config = config
        self.controller_service = controller_service
        self.image_service = image_service
        self.image_process_service = image_process_service
        self.is_active = False
        self.captured_images = []

    def start(self):
        self.is_active = True

    def stop(self):
        self.is_active = False

    def stitching(self, grid_size_x: int, grid_size_y: int, magnitude: CameraMagnitude, corner: CornerPosition):
        """
        スティッチングを行うおおもとの関数
        param grid_size_x: x方向の撮影枚数
        param grid_size_y: y方向の撮影枚数
        param magnitude: 顕微鏡の倍率
        param corner: スティッチングの開始位置
        """
        if not self.is_active:
            return

        try:
            # ステータス更新: スティッチング開始
            progress_event = StitchingProgressEvent(progress_message="Stitching started")
            event_bus.publish(progress_event)

            # 軌跡生成
            trajectory = self.generate_trajectory(grid_size_x, grid_size_y, magnitude, corner)
            if len(trajectory) == 0:
                error_event = ErrorEvent(error_message="Failed to generate trajectory. It may exceed movement limits.")
                event_bus.publish(error_event)
                return

            # 移動と撮影
            images = self.move_and_capture(trajectory)
            if not images:
                error_event = ErrorEvent(error_message="Failed to capture images.")
                event_bus.publish(error_event)
                return

            # 画像結合
            stitched_image = self.concatenate_images(images)
            if stitched_image is None:
                error_event = ErrorEvent(error_message="Failed to stitch images.")
                event_bus.publish(error_event)
                return

            # 結合画像のイベント発行
            image_event = ImageCaptureEvent(
                image_data=stitched_image,
                timestamp=datetime.now()
            )
            event_bus.publish(image_event)

            # ステータス更新: スティッチング完了
            progress_event = StitchingProgressEvent(progress_message="Stitching completed")
            event_bus.publish(progress_event)

        except Exception as e:
            error_event = ErrorEvent(error_message=f"Error occurred during stitching: {str(e)}")
            event_bus.publish(error_event)

    def generate_trajectory(self, grid_size_x: int, grid_size_y: int, magnitude: CameraMagnitude, corner: CornerPosition) -> List[Tuple[float, float]]:
        """
        StageServiceから現在の座標を取得し、スティッチングするためのステージの軌跡を生成する
        param grid_size_x: x方向の撮影枚数
        param grid_size_y: y方向の撮影枚数
        param magnitude: 顕微鏡の倍率
        param corner: スティッチングの開始位置
        """
        try:
            # 現在位置を取得
            current_pos = self.controller_service.get_current_position()

            # 設定から軌跡パラメータを取得
            img_size = self.config["camera"]["image_size"][magnitude.value]

            overlap_ratio = self.config["stitching"].get("overlap_ratio", 0.1)
            step_size_x = img_size[0] * (1 - overlap_ratio)
            step_size_y = img_size[1] * (1 - overlap_ratio)

            total_move_x = step_size_x * (grid_size_x - 1)
            total_move_y = step_size_y * (grid_size_y - 1)

            trajectory = []
            # 開始位置の調整
            if corner == CornerPosition.TOP_LEFT:
                start_x = current_pos[0]
                start_y = current_pos[1]
            elif corner == CornerPosition.TOP_RIGHT:
                start_x = current_pos[0] - total_move_x
                start_y = current_pos[1]
            elif corner == CornerPosition.BOTTOM_LEFT:
                start_x = current_pos[0]
                start_y = current_pos[1] - total_move_y
            elif corner == CornerPosition.BOTTOM_RIGHT:
                start_x = current_pos[0] - total_move_x
                start_y = current_pos[1] - total_move_y
            else:
                start_x = current_pos[0]
                start_y = current_pos[1]

            print(f"start:{start_x}, {start_y}")
            print(f"total_move:{total_move_x}, {total_move_y}")
            # 移動が範囲内かチェック
            # 開始位置とその対角の頂点が範囲内であることを確認
            if not self.controller_service.is_valid_movement(start_x, start_y, is_relative=True):
                return []
            if not self.controller_service.is_valid_movement(start_x + total_move_x, start_y + total_move_y, is_relative=True):
                return []

            # ジグザグパターンで軌跡生成
            for y in range(grid_size_y):
                if y % 2 == 0:  # 偶数行は左から右
                    for x in range(grid_size_x):
                        rel_x = x * step_size_x
                        rel_y = y * step_size_y
                        trajectory.append((rel_x, rel_y))
                else:  # 奇数行は右から左
                    for x in range(grid_size_x - 1, -1, -1):
                        rel_x = x * step_size_x
                        rel_y = y * step_size_y
                        trajectory.append((rel_x, rel_y))

            return trajectory

        except Exception as e:
            error_event = ErrorEvent(error_message=f"Error occurred during trajectory generation: {str(e)}")
            event_bus.publish(error_event)
            return []

    def move_and_capture(self, trajectory: List[Tuple[float, float]]) -> List[Any]:
        """移動された座標に移動し、撮影することを繰り返す"""
        images = []

        try:
            for i, (rel_x, rel_y) in enumerate(trajectory):
                # Progress report
                progress_msg = f"Moving to position {i+1}/{len(trajectory)}..."
                progress_event = StitchingProgressEvent(progress_message=progress_msg)
                event_bus.publish(progress_event)

                # 最初の位置以外は相対移動
                is_relative = i > 0
                if i == 0:
                    # 最初の位置は現在位置からの相対移動
                    current_pos = self.controller_service.get_current_position()
                    target_x = current_pos[0] + rel_x
                    target_y = current_pos[1] + rel_y
                    self.controller_service.move_to(target_x, target_y, is_relative=False)
                else:
                    # 前の位置からの相対移動
                    prev_x, prev_y = trajectory[i-1]
                    delta_x = rel_x - prev_x
                    delta_y = rel_y - prev_y
                    self.controller_service.move_to(delta_x, delta_y, is_relative=True)

                # 移動完了を待つ
                self._wait_for_movement_completion()

                # 画像撮影
                progress_msg = f"Capturing image at position {i+1}/{len(trajectory)}..."
                progress_event = StitchingProgressEvent(progress_message=progress_msg)
                event_bus.publish(progress_event)

                image_data = self.image_service.capture()
                if image_data is None:
                    error_event = ErrorEvent(error_message=f"Failed to capture image at position {i+1}")
                    event_bus.publish(error_event)
                    return []

                images.append(image_data)

            return images

        except Exception as e:
            error_event = ErrorEvent(error_message=f"Error occurred during movement and capture: {str(e)}")
            event_bus.publish(error_event)
            return []

    def _wait_for_movement_completion(self):
        """移動完了を待つ"""
        import time
        while self.controller_service.is_moving():
            time.sleep(0.1)

    def concatenate_images(self, images: List[Any]) -> Any:
        """image_process_serviceを呼び出し、画像を結合する"""
        try:
            progress_event = StitchingProgressEvent(progress_message="Stitching images...")
            event_bus.publish(progress_event)

            # 画像結合パラメータを設定から取得
            stitching_type = self.config.get("stitching", {}).get("type", "grid")
            grid_size_x = self.config.get("stitching", {}).get("grid_size_x", 3)
            grid_size_y = self.config.get("stitching", {}).get("grid_size_y", 3)

            # image_process_serviceで画像結合
            stitched_image = self.image_process_service.concatenate(
                stitching_type=stitching_type,
                images=images,
                grid_size_x=grid_size_x,
                grid_size_y=grid_size_y
            )

            return stitched_image

        except Exception as e:
            error_event = ErrorEvent(error_message=f"Error occurred during stitching: {str(e)}")
            event_bus.publish(error_event)
            return None
