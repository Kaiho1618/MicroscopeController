"""
顕微鏡操作ソフト用のロガーモジュール
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


class MicroscopeLogger:
    """
    顕微鏡操作ソフト専用のロガークラス
    """

    _instance: Optional["MicroscopeLogger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """ロガーの初期設定"""
        # ログディレクトリの作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # ロガーの作成
        self._logger = logging.getLogger("MicroscopeController")
        self._logger.setLevel(logging.DEBUG)

        # 既存のハンドラーをクリア（重複防止）
        self._logger.handlers.clear()

        # フォーマッターの作成
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s")

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # ファイルハンドラー（日付別）
        today = datetime.now().strftime("%Y%m%d")
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"microscope_{today}.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        # エラー専用ファイルハンドラー
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"microscope_error_{today}.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"  # 5MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self._logger.addHandler(error_handler)

        self._logger.info("MicroscopeLogger initialized")

    def get_logger(self) -> logging.Logger:
        """ロガーインスタンスを取得"""
        return self._logger

    def log_camera_operation(self, operation: str, result: str = "success", details: str = ""):
        """カメラ操作専用ログ"""
        message = f"CAMERA - {operation}: {result}"
        if details:
            message += f" ({details})"

        if result.lower() in ["success", "completed"]:
            self._logger.info(message)
        elif result.lower() in ["warning", "retry"]:
            self._logger.warning(message)
        else:
            self._logger.error(message)

    def log_stage_operation(self, operation: str, position: tuple = None, result: str = "success", details: str = ""):
        """ステージ操作専用ログ"""
        message = f"STAGE - {operation}: {result}"
        if position:
            message += f" at position {position}"
        if details:
            message += f" ({details})"

        if result.lower() in ["success", "completed"]:
            self._logger.info(message)
        elif result.lower() in ["warning", "retry"]:
            self._logger.warning(message)
        else:
            self._logger.error(message)

    def log_stitching_progress(self, current_step: int, total_steps: int, operation: str = ""):
        """スティッチング進捗専用ログ"""
        progress = (current_step / total_steps) * 100
        message = f"STITCHING - Progress: {current_step}/{total_steps} ({
            progress:.1f}%)"
        if operation:
            message += f" - {operation}"
        self._logger.info(message)

    def log_event(self, event_type: str, event_data: dict = None):
        """イベント発生専用ログ"""
        message = f"EVENT - {event_type}"
        if event_data:
            details = ", ".join([f"{k}:{v}" for k, v in event_data.items()])
            message += f" ({details})"
        self._logger.debug(message)

    def log_error_with_context(self, error: Exception, context: str = "", component: str = ""):
        """エラーとコンテキスト情報を詳細ログ"""
        message = "ERROR"
        if component:
            message += f" in {component}"
        if context:
            message += f" during {context}"
        message += f": {type(error).__name__}: {str(error)}"

        self._logger.error(message, exc_info=True)

    def set_log_level(self, level: str):
        """ログレベルの動的変更"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if level.upper() in level_map:
            self._logger.setLevel(level_map[level.upper()])
            self._logger.info(f"Log level changed to {level.upper()}")
        else:
            self._logger.warning(f"Invalid log level: {level}")

    def info(self, msg: str):
        """情報ログの簡易関数"""
        self._logger.info(msg)

    def debug(self, msg: str):
        """デバッグログの簡易関数"""
        self._logger.debug(msg)

    def critical(self, msg: str):
        """クリティカルログの簡易関数"""
        self._logger.critical(msg)

    def warning(self, msg: str):
        """警告ログの簡易関数"""
        self._logger.warning(msg)

    def error(self, msg: str):
        """エラーログの簡易関数"""
        self._logger.error(msg)


# シングルトンインスタンス
logger = MicroscopeLogger()


# 便利な関数エイリアス
def get_logger() -> logging.Logger:
    """メインロガーを取得"""
    return logger.get_logger()


def log_camera(operation: str, result: str = "success", details: str = ""):
    """カメラ操作ログの簡易関数"""
    logger.log_camera_operation(operation, result, details)


def log_stage(operation: str, position: tuple = None, result: str = "success", details: str = ""):
    """ステージ操作ログの簡易関数"""
    logger.log_stage_operation(operation, position, result, details)


def log_stitching(current_step: int, total_steps: int, operation: str = ""):
    """スティッチング進捗ログの簡易関数"""
    logger.log_stitching_progress(current_step, total_steps, operation)


def log_event(event_type: str, event_data: dict = None):
    """イベントログの簡易関数"""
    logger.log_event(event_type, event_data)


def log_error(error: Exception, context: str = "", component: str = ""):
    """エラーログの簡易関数"""
    logger.log_error_with_context(error, context, component)


# 使用例
if __name__ == "__main__":
    # 基本的な使用方法
    logger = get_logger()
    logger.info("Application started")

    # 専用ログ関数の使用例
    log_camera("initialize", "success", "Camera connected successfully")
    log_stage("move_to", (10, 20), "success")
    log_stitching(3, 10, "capturing image")
    log_event("ImageCaptureEvent", {"position": (10, 20), "timestamp": "2025-01-01"})

    try:
        # エラーの例
        raise ValueError("Test error")
    except Exception as e:
        log_error(e, "testing error logging", "main")
