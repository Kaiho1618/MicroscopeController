from enum import Enum


class CornerPosition(Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class CameraMagnitude(Enum):
    MAG_5X = "x5"
    MAG_10X = "x10"
    MAG_20X = "x20"
    MAG_50X = "x50"
    MAG_100X = "x100"


class ProgressStatus(Enum):
    FAILED = "failed"
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StitchingType(Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"

class SpeedLevel(Enum):
    S1 = 100
    S2 = 200
    S3 = 300
