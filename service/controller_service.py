from typing import Dict, Any
import serial
import time

from mock.test_env import test_env
from application.event_bus import event_bus, StartMoveEvent, StopMoveEvent, MoveToEvent
from application.event_bus import ErrorEvent


def create_controller_service(config: Dict[str, Any]):
    mock = config["mock"]
    if mock:
        return MockControllerService(config)    
    return ControllerService(config)


class MockControllerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connect()
        self.setup_event_subscriptions()

    def connect(self):
        test_env.connect()

    def start_move(self, speed: float, degree: float):
        test_env.start_move(speed, degree)

    def stop_move(self):
        test_env.stop_move()

    def is_moving(self):
        return test_env.is_moving

    def move_to(self, x: float, y: float, is_relative: bool = True):
        return test_env.move_to(x, y, is_relative)

    def setup_event_subscriptions(self):
        event_bus.subscribe(StartMoveEvent, self.on_start_move)
        event_bus.subscribe(StopMoveEvent, self.on_stop_move)
        event_bus.subscribe(MoveToEvent, self.on_move_to)

    def on_start_move(self, event: StartMoveEvent):
        print(f"Controller Service: Start move - Speed: {event.speed}, Direction: {event.direction}")
        try:
            self.start_move(event.speed, event.direction)
            # Could publish a MoveStartedEvent here if needed
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to start move: {str(e)}")
            event_bus.publish(error_event)

    def on_stop_move(self, event: StopMoveEvent):
        print("Controller Service: Stop move")
        try:
            self.stop_move()
            # Could publish a MoveStoppedEvent here if needed
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to stop move: {str(e)}")
            event_bus.publish(error_event)

    def on_move_to(self, event: MoveToEvent):
        print(f"Controller Service: Move to {event.target_pos}, Relative: {event.is_relative}")
        try:
            self.move_to(event.target_pos[0], event.target_pos[1], event.is_relative)
            # Could publish a MoveCompletedEvent here if needed
        except Exception as e:
            from application.event_bus import ErrorEvent
            error_event = ErrorEvent(error_message=f"Failed to move to position: {str(e)}")
            event_bus.publish(error_event)

    def get_current_position(self):
        return test_env.get_current_position()

    def is_valid_movement(self, x, y, is_relative) -> bool:
        """指定座標への移動が範囲内かチェックする"""
        if is_relative:
            current_pos = self.get_current_position()
            x += current_pos[0]
            y += current_pos[1]
        return (test_env.min_x <= x <= test_env.max_x) and (test_env.min_y <= y <= test_env.max_y)

    def go_to_origin(self):
        test_env.move_to(0, 0, is_relative=False)


class ControllerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ser = None
        self.connect()
        self.setup_event_subscriptions()

    def connect(self):
        """GSC-02コントローラへのシリアル接続を確立"""
        stage_config = self.config["stage"]
        try:
            self.ser = serial.Serial(
                port=stage_config["com_port"],
                baudrate=stage_config["baud_rate"],
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=stage_config["timeout"],
                rtscts=True  # Hardware flow control
            )
            print(f"Connected to {stage_config['com_port']}")
        except serial.SerialException as e:
            error_msg = f"Failed to connect to controller on {stage_config['com_port']}: {str(e)}"
            error_event = ErrorEvent(error_message=error_msg)
            event_bus.publish(error_event)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error connecting to controller: {str(e)}"
            error_event = ErrorEvent(error_message=error_msg)
            event_bus.publish(error_event)
            raise RuntimeError(error_msg) from e

    def _send_command(self, command: str):
        """コマンドを送信"""
        cmd = command + '\r\n'
        self.ser.write(cmd.encode())

    def _read_response(self) -> str:
        """レスポンスを読み取り"""
        return self.ser.readline().decode().strip()

    def _check_ready(self) -> bool:
        """コントローラがReady状態かチェック"""
        self._send_command('!')
        response = self._read_response()
        return 'R' in response

    def _ensure_ready(self):
        """コントローラがReady状態になるまで待機。Readyでない場合はエラー"""
        if not self._check_ready():
            error_msg = "Controller is not ready (Busy state)"
            error_event = ErrorEvent(error_message=error_msg)
            event_bus.publish(error_event)
            raise RuntimeError(error_msg)

    def _check_status(self):
        """Q:コマンドでステータスをチェックし、エラーやリミットセンサを検出"""
        self._send_command('Q:')
        response = self._read_response()

        # Parse response: "   -1000,   20000, ACK1, ACK2, ACK3"
        parts = [p.strip() for p in response.split(',')]

        if len(parts) >= 5:
            ack1 = parts[2]  # Command error/OK
            ack2 = parts[3]  # Limit sensor status
            ack3 = parts[4]  # Busy/Ready

            # Check command error
            if ack1 == 'X':
                error_msg = "Command error detected"
                error_event = ErrorEvent(error_message=error_msg)
                event_bus.publish(error_event)
                raise RuntimeError(error_msg)

            # Check limit sensor activation
            if ack2 == 'L':
                error_msg = "Axis 1 limit sensor activated"
                error_event = ErrorEvent(error_message=error_msg)
                event_bus.publish(error_event)
                raise RuntimeError(error_msg)
            elif ack2 == 'M':
                error_msg = "Axis 2 limit sensor activated"
                error_event = ErrorEvent(error_message=error_msg)
                event_bus.publish(error_event)
                raise RuntimeError(error_msg)
            elif ack2 == 'W':
                error_msg = "Both axes limit sensors activated"
                error_event = ErrorEvent(error_message=error_msg)
                event_bus.publish(error_event)
                raise RuntimeError(error_msg)

            return ack3 == 'R'  # Return True if Ready

        return False

    def _wait_until_ready(self, poll_interval: float = 0.1):
        """ステージが停止するまで待機（!コマンドでポーリング）"""
        while True:
            self._send_command('!')
            response = self._read_response()
            if 'R' in response:  # Ready
                break
            time.sleep(poll_interval)

        # After movement completes, check for errors/limits
        self._check_status()

    def _mm_to_pulses(self, mm: float) -> int:
        """mmをパルス数に変換"""
        return int(mm * self.config["stage"]["pulses_per_mm"])

    def start_move(self, speed: float, degree: float):
        """JOG移動を開始（degree: 0/90/180/270）"""
        # Ensure controller is ready before sending command
        self._ensure_ready()

        # degree to axis and direction mapping
        if degree == 0:
            axis, direction = '1', '+'
        elif degree == 90:
            axis, direction = '2', '+'
        elif degree == 180:
            axis, direction = '1', '-'
        elif degree == 270:
            axis, direction = '2', '-'
        else:
            raise ValueError(f"Invalid degree: {degree}. Expected 0, 90, 180, or 270")

        # Send JOG command
        self._send_command(f'J:{axis}{direction}')
        self._send_command('G')

    def stop_move(self):
        """移動を停止"""
        self._send_command('L:W')

    def is_moving(self) -> bool:
        """移動中かどうかを確認"""
        self._send_command('!')
        response = self._read_response()
        return 'B' in response  # Busy

    def move_to(self, x: float, y: float, is_relative: bool = True):
        """指定位置に移動（mmで指定）"""
        # Ensure controller is ready before sending command
        self._ensure_ready()

        x_pulses = self._mm_to_pulses(x)
        y_pulses = self._mm_to_pulses(y)

        # Build M command for relative movement
        x_dir = '+' if x_pulses >= 0 else '-'
        y_dir = '+' if y_pulses >= 0 else '-'

        # M:WnmPxnmPx format for both axes
        cmd = f'M:W{x_dir}P{abs(x_pulses)}{y_dir}P{abs(y_pulses)}'
        self._send_command(cmd)
        self._send_command('G')

        # Wait until movement completes
        self._wait_until_ready()

    def get_current_position(self):
        """現在位置を取得（Q:コマンド）"""
        try:
            self._send_command('Q:')
            response = self._read_response()
            # Parse response: "   -1000,   20000, ACK1, ACK2, ACK3"
            # Extract coordinates and convert to mm
            parts = response.split(',')
            if len(parts) >= 2:
                x_pulses = int(parts[0].strip())
                y_pulses = int(parts[1].strip())
                pulses_per_mm = self.config["stage"]["pulses_per_mm"]
                return (x_pulses / pulses_per_mm, y_pulses / pulses_per_mm)
            return (0.0, 0.0)
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to get position: {str(e)}")
            event_bus.publish(error_event)
            return (0.0, 0.0)

    def is_valid_movement(self, x, y, is_relative) -> bool:
        """指定座標への移動が範囲内かチェックする"""
        if is_relative:
            current_pos = self.get_current_position()
            x += current_pos[0]
            y += current_pos[1]

        stage_config = self.config["stage"]
        return (stage_config["x_min"] <= x <= stage_config["x_max"]) and \
               (stage_config["y_min"] <= y <= stage_config["y_max"])

    def go_to_origin(self):
        """原点に移動"""
        current_pos = self.get_current_position()
        self.move_to(-current_pos[0], -current_pos[1], is_relative=True)

    def setup_event_subscriptions(self):
        event_bus.subscribe(StartMoveEvent, self.on_start_move)
        event_bus.subscribe(StopMoveEvent, self.on_stop_move)
        event_bus.subscribe(MoveToEvent, self.on_move_to)

    def on_start_move(self, event: StartMoveEvent):
        print(f"Controller Service: Start move - Speed: {event.speed}, Direction: {event.direction}")
        try:
            self.start_move(event.speed, event.direction)
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to start move: {str(e)}")
            event_bus.publish(error_event)

    def on_stop_move(self, event: StopMoveEvent):
        print("Controller Service: Stop move")
        try:
            self.stop_move()
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to stop move: {str(e)}")
            event_bus.publish(error_event)

    def on_move_to(self, event: MoveToEvent):
        print(f"Controller Service: Move to {event.target_pos}, Relative: {event.is_relative}")
        try:
            self.move_to(event.target_pos[0], event.target_pos[1], event.is_relative)
        except Exception as e:
            error_event = ErrorEvent(error_message=f"Failed to move to position: {str(e)}")
            event_bus.publish(error_event)


if __name__ == "__main__":
    # For direct testing in real environment
    test_config = {
        "mock": False,
        "stage": {
            "com_port": "COM3",
            "baud_rate": 9600,
            "timeout": 5.0,
            "x_min": -50.0,
            "x_max": 50.0,
            "y_min": -50.0,
            "y_max": 50.0,
            "pulses_per_mm": 1000,
            "speed_slow": 500,
            "speed_fast": 5000,
            "speed_accel_time": 200
        }
    }

    # Create real controller service
    controller = ControllerService(test_config)

    print("Controller initialized successfully")
    print(f"Current position: {controller.get_current_position()}")

    # Test relative movement
    print("\nTesting relative movement: move 1mm in X direction")
    controller.move_to(1.0, 0.0, is_relative=True)
    print(f"Current position: {controller.get_current_position()}")

    # Test movement back
    print("\nMoving back to origin")
    controller.move_to(-1.0, 0.0, is_relative=True)
    print(f"Current position: {controller.get_current_position()}")

    print("\nTest completed")
