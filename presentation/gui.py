import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from PIL import Image, ImageTk
import io
import cv2
import numpy as np

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application.event_bus import event_bus, ImageCaptureEvent, ErrorEvent, StartMoveEvent, StopMoveEvent, MoveToEvent, StitchingProgressEvent, PositionUpdateEvent
from enums.enums import CameraMagnitude, CornerPosition, ProgressStatus, SpeedLevel


class MicroscopeGUI:
    def __init__(self, root, config, controller_service, image_service, file_service, manual_controller, stitching_controller):
        self.root = root
        self.root.title("Microscope Controller")
        window_h = config["gui"]["window_height"]
        window_w = config["gui"]["window_width"]
        self.root.geometry(f"{window_w}x{window_h}")

        self.config = config

        # Initialize services
        self.controller_service = controller_service
        self.image_service = image_service
        self.file_service = file_service

        self.manual_controller = manual_controller
        self.stitching_controller = stitching_controller

        # Set up GUI
        self.setup_gui()

        # Set up keyboard bindings
        self.setup_keyboard_bindings()

        # Set up event subscriptions
        self.setup_event_subscriptions()

        # Load and display default no-image placeholder
        self.load_default_image()

        # Start the manual controller
        self.manual_controller.start()

        # Event log
        self.event_log = []

        # Auto capture timer
        self.auto_capture_timer = None
        self.auto_capture_active = False

        # Keyboard movement tracking
        self.current_movement_key = None
        self.key_release_timer = None  # Timer to detect genuine key release

        self.capture_interval = int(1 / self.config["camera"]["frame_rate"] * 1000)  # [ms]

        # 現在表示されている画像がスティッチング画像かどうかのフラグ
        self.stitched_image_flag = False

        # Position update timer
        self.position_update_timer = None
        self.start_position_updates()

    def setup_gui(self):
        # Main frame with less padding
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create left panel for controls and right panel for image
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title in left panel
        title_label = ttk.Label(left_panel, text="Microscope Controller", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # Movement controls in left panel
        movement_frame = ttk.LabelFrame(left_panel, text="Movement Controls", padding="5")
        movement_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        ttk.Label(movement_frame, text="Speed:").grid(row=0, column=0, sticky=tk.W)
        self.speed_var = tk.StringVar(value=SpeedLevel.S1.name)
        speed_combo = ttk.Combobox(movement_frame, textvariable=self.speed_var,
                                  values=[speed.name for speed in SpeedLevel],
                                  width=8, state="readonly")
        speed_combo.grid(row=0, column=1, padx=(2, 10), sticky=tk.W)
        speed_combo.bind('<<ComboboxSelected>>', self.on_speed_change)

        # Movement buttons
        self.button_move_up = ttk.Button(movement_frame, text="↑ (W)", command=lambda: self.move_key('w'))
        self.button_move_up.grid(row=0, column=2)
        self.button_move_left = ttk.Button(movement_frame, text="← (A)", command=lambda: self.move_key('a'))
        self.button_move_left.grid(row=1, column=1)
        self.button_move_down = ttk.Button(movement_frame, text="↓ (S)", command=lambda: self.move_key('s'))
        self.button_move_down.grid(row=1, column=2)
        self.button_move_right = ttk.Button(movement_frame, text="→ (D)", command=lambda: self.move_key('d'))
        self.button_move_right.grid(row=1, column=3)

        # Stop button with less spacing
        ttk.Button(movement_frame, text="STOP", command=self.stop_move, style="Accent.TButton").grid(row=2, column=2, pady=(5, 0))

        # Keyboard status with less spacing
        self.keyboard_status = ttk.Label(movement_frame, text="Keyboard: Ready (W/A/S/D keys)", font=("Arial", 8))
        self.keyboard_status.grid(row=3, column=0, columnspan=4, pady=(2, 0))

        # Position controls in left panel
        position_frame = ttk.LabelFrame(left_panel, text="Position Controls", padding="5")
        position_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # Current position display
        ttk.Label(position_frame, text="Current Position:", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        self.current_pos_label = ttk.Label(position_frame, text="X: 0.00 mm, Y: 0.00 mm", font=("Arial", 9))
        self.current_pos_label.grid(row=0, column=2, columnspan=4, sticky=tk.W, padx=(5, 0))

        # X, Y position with tighter spacing
        ttk.Label(position_frame, text="X:").grid(row=1, column=0, sticky=tk.W)
        self.x_var = tk.DoubleVar(value=0.0)
        ttk.Entry(position_frame, textvariable=self.x_var, width=8).grid(row=1, column=1, padx=2)

        ttk.Label(position_frame, text="Y:").grid(row=1, column=2, sticky=tk.W)
        self.y_var = tk.DoubleVar(value=0.0)
        ttk.Entry(position_frame, textvariable=self.y_var, width=8).grid(row=1, column=3, padx=2)

        # Relative checkbox
        self.relative_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(position_frame, text="Relative", variable=self.relative_var).grid(row=1, column=4, padx=(5, 0))

        # Move to button
        ttk.Button(position_frame, text="Move To", command=self.move_to).grid(row=1, column=5, padx=(5, 0))

        # Go to origin button
        ttk.Button(position_frame, text="Go to Origin", command=self.go_to_origin).grid(row=2, column=0, columnspan=6, pady=(5, 0), sticky=(tk.W, tk.E))

        # Stitching controls in left panel
        stitching_frame = ttk.LabelFrame(left_panel, text="Stitching Controls", padding="5")
        stitching_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # Grid size controls
        ttk.Label(stitching_frame, text="Grid X:").grid(row=0, column=0, sticky=tk.W)
        self.grid_x_var = tk.IntVar(value=3)
        ttk.Entry(stitching_frame, textvariable=self.grid_x_var, width=6).grid(row=0, column=1, padx=2)

        ttk.Label(stitching_frame, text="Grid Y:").grid(row=0, column=2, sticky=tk.W)
        self.grid_y_var = tk.IntVar(value=3)
        ttk.Entry(stitching_frame, textvariable=self.grid_y_var, width=6).grid(row=0, column=3, padx=2)

        # Magnification selection
        ttk.Label(stitching_frame, text="Magnitude:").grid(row=1, column=0, sticky=tk.W)
        self.magnitude_var = tk.StringVar(value=CameraMagnitude.MAG_10X.value)
        magnitude_combo = ttk.Combobox(stitching_frame, textvariable=self.magnitude_var,
                                     values=[mag.value for mag in CameraMagnitude],
                                     width=8, state="readonly")
        magnitude_combo.grid(row=1, column=1, columnspan=2, padx=2, sticky=tk.W)

        # Corner position selection
        ttk.Label(stitching_frame, text="Start Corner:").grid(row=2, column=0, sticky=tk.W)
        self.corner_var = tk.StringVar(value=CornerPosition.TOP_LEFT.value)
        corner_combo = ttk.Combobox(stitching_frame, textvariable=self.corner_var,
                                  values=[corner.value for corner in CornerPosition],
                                  width=12, state="readonly")
        corner_combo.grid(row=2, column=1, columnspan=3, padx=2, sticky=tk.W)

        # Stitching button and status
        self.stitching_button = ttk.Button(stitching_frame, text="Start Stitching", command=self.start_stitching)
        self.stitching_button.grid(row=3, column=0, columnspan=2, pady=(5, 0), sticky=tk.W)

        self.stitching_status = ttk.Label(stitching_frame, text="Ready", font=("Arial", 8))
        self.stitching_status.grid(row=3, column=2, columnspan=2, pady=(5, 0), sticky=tk.W)

        # Image controls in left panel
        image_frame = ttk.LabelFrame(left_panel, text="Image Controls", padding="5")
        image_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        ttk.Button(image_frame, text="Capture Image", command=self.capture_image).grid(row=0, column=0, padx=(0, 5))

        # Auto capture controls
        self.auto_capture_button = ttk.Button(image_frame, text="Start Auto Capture", command=self.toggle_auto_capture)
        self.auto_capture_button.grid(row=0, column=1, padx=(0, 5))

        # Status label
        self.auto_capture_status = ttk.Label(image_frame, text="Auto capture: OFF", font=("Arial", 8))
        self.auto_capture_status.grid(row=0, column=2)

        # Image display in right panel - takes full space
        display_frame = ttk.LabelFrame(right_panel, text="Captured Image", padding="5")
        display_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Image label for displaying captured images with larger minimum size
        self.image_label = ttk.Label(display_frame, text="No image captured yet", anchor="center",
                                   relief="sunken", borderwidth=1)
        self.image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure image display frame to expand
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)

        # Event log in left panel - compact size
        log_frame = ttk.LabelFrame(left_panel, text="Event Log", padding="5")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))

        # Text widget with scrollbar - smaller height and width for left panel
        self.log_text = tk.Text(log_frame, height=8, width=40, font=("Arial", 8))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Configure grid weights - left panel for controls, right panel for image
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=0)  # Left panel fixed width
        main_frame.columnconfigure(1, weight=1)  # Right panel gets all remaining space
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(5, weight=1)  # Event log expands in left panel
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def setup_keyboard_bindings(self):
        """Set up keyboard event bindings for movement control"""
        # Make the root window focusable
        self.root.focus_set()

        # Bind key press and release events
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)

        # Bind focus events to ensure keyboard events work
        self.root.bind('<Button-1>', self.on_click)

    def setup_event_subscriptions(self):
        """Subscribe to events for logging and UI updates"""
        event_bus.subscribe(ImageCaptureEvent, self.on_image_capture)
        event_bus.subscribe(ErrorEvent, self.on_error)
        event_bus.subscribe(StartMoveEvent, self.on_start_move)
        event_bus.subscribe(StopMoveEvent, self.on_stop_move)
        event_bus.subscribe(MoveToEvent, self.on_move_to)
        event_bus.subscribe(StitchingProgressEvent, self.on_stitching_progress)
        event_bus.subscribe(PositionUpdateEvent, self.on_position_update)

    def load_default_image(self):
        """Load and display the default no-image placeholder"""
        try:
            # Get the path to the no-image file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            no_image_path = os.path.join(current_dir, "img", "noimage.png")

            if os.path.exists(no_image_path):
                # Load the default image
                default_image = Image.open(no_image_path)
                self.display_image(default_image)
            else:
                self.log_event(f"Default image not found at: {no_image_path}")
        except Exception as e:
            self.log_event(f"Failed to load default image: {str(e)}")

    def move_key(self, key):
        """Handle keyboard movement"""
        speed_name = self.speed_var.get()
        speed = SpeedLevel[speed_name].value
        self.manual_controller.start_move(speed, key)
        self.log_event(f"Movement started: {key} at speed {speed_name} ({speed})")

    def stop_move(self):
        """Stop movement"""
        # すべてのキーボタンをunpress状態にする
        self.current_movement_key = None
        self.button_move_up.state(['!pressed'])
        self.button_move_left.state(['!pressed'])
        self.button_move_down.state(['!pressed'])
        self.button_move_right.state(['!pressed'])

        self.manual_controller.stop_move()
        self.log_event("Movement stopped")

    def move_to(self):
        """Move to specific position"""
        x = self.x_var.get()
        y = self.y_var.get()
        is_relative = self.relative_var.get()
        self.manual_controller.move_to(x, y, is_relative)
        self.log_event(f"Move to ({x}, {y}), relative: {is_relative}")

    def go_to_origin(self):
        """Move to origin position (0, 0)"""
        self.manual_controller.move_to(0, 0, is_relative=False)
        self.log_event("Moving to origin (0, 0)")

    def on_speed_change(self, event):
        """Handle speed change from combobox"""
        speed_name = self.speed_var.get()
        try:
            speed_level = SpeedLevel[speed_name]
            self.log_event(f"Changing speed to {speed_name}")
            self.controller_service.change_speed(speed_level)
            self.log_event(f"Speed changed to {speed_name}")
        except Exception as e:
            self.log_event(f"Failed to change speed: {str(e)}")

    def on_key_press(self, event):
        """Handle key press events for movement"""
        key = event.keysym.lower()

        # Only handle movement keys
        if key in ['w', 'a', 's', 'd']:
            # Cancel any pending release timer (this is a repeat, not a real release)
            if self.key_release_timer:
                self.root.after_cancel(self.key_release_timer)
                self.key_release_timer = None

            # If this key is not already pressed
            if self.current_movement_key is None:
                self.current_movement_key = key
                self.move_key(key)
                if key == 'w':
                    self.button_move_up.state(['pressed'])
                elif key == 'a':
                    self.button_move_left.state(['pressed'])
                elif key == 's':
                    self.button_move_down.state(['pressed'])
                elif key == 'd':
                    self.button_move_right.state(['pressed'])
            else:
                # Key is pressed but movement is already active
                self.keyboard_status.configure(text=f"Keyboard: Moving {self.current_movement_key.upper()}")

    def on_key_release(self, event):
        """Handle key release events for movement"""
        key = event.keysym.lower()

        # Only handle movement keys
        if key in ['w', 'a', 's', 'd']:
            # Schedule a delayed check to see if this is a genuine release
            # If another KeyPress comes within 50ms, it's just key repeat
            if key == self.current_movement_key:
                if self.key_release_timer:
                    self.root.after_cancel(self.key_release_timer)

                # Delay the actual stop by 50ms to filter out key repeat
                self.key_release_timer = self.root.after(50, lambda: self._actual_key_release(key))

    def _actual_key_release(self, key):
        """Actually handle key release after confirming it's not key repeat"""
        if key == self.current_movement_key:
            self.stop_move()
            self.current_movement_key = None
            self.key_release_timer = None
            self.log_event(f"Keyboard movement stopped: {key.upper()}")

    def on_focus_in(self, event):
        """Handle focus in events to ensure keyboard events work"""
        self.root.focus_set()

    def on_click(self, event):
        """Handle click events to maintain focus"""
        # don't steal focus from Entry widgets
        if not isinstance(event.widget, ttk.Entry):
            self.root.focus_set()

    def capture_image(self):
        """Capture image"""
        # Open file dialog to select save path
        file_path = filedialog.asksaveasfilename(
            title="Save Image As",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            self.log_event("Image capture cancelled by user")
            return

        # Capture image using manual controller
        result = self.manual_controller.capture_image()
        if result is not None:
            try:
                # Save image using image service
                self.file_service.save_image(result, file_path)
                self.log_event(f"Image captured and saved to: {file_path}")
            except Exception as e:
                self.log_event(f"Failed to save image: {str(e)}")
                messagebox.showerror("Save Error", f"Failed to save image: {str(e)}")
        else:
            self.log_event("Image capture failed")

    def toggle_auto_capture(self):
        """Toggle automatic image capture on/off"""
        if self.auto_capture_active:
            self.stop_auto_capture()
        else:
            self.start_auto_capture()

    def start_auto_capture(self):
        """Start automatic image capture"""
        if not self.auto_capture_active:
            self.auto_capture_active = True
            self.auto_capture_button.configure(text="Stop Auto Capture")
            self.auto_capture_status.configure(text="Auto capture: ON")
            self.log_event("Auto capture started")
            self.schedule_next_capture()

    def stop_auto_capture(self):
        """Stop automatic image capture"""
        if self.auto_capture_active:
            self.auto_capture_active = False
            if self.auto_capture_timer:
                self.root.after_cancel(self.auto_capture_timer)
                self.auto_capture_timer = None
            self.auto_capture_button.configure(text="Start Auto Capture)")
            self.auto_capture_status.configure(text="Auto capture: OFF")
            self.log_event("Auto capture stopped")

    def schedule_next_capture(self):
        """Schedule the next automatic capture"""
        if self.auto_capture_active:
            self.auto_capture_timer = self.root.after(self.capture_interval, self.auto_capture_image)

    def auto_capture_image(self):
        """Capture image automatically without file dialog"""
        if self.auto_capture_active:
            # Capture image using manual controller (without file dialog)
            result = self.manual_controller.capture_image()
            if result is not None:
                # Note: We don't save to file during auto capture, just display
                pass  # The image will be displayed via the event system

            # Schedule next capture
            self.schedule_next_capture()

    def on_image_capture(self, event: ImageCaptureEvent):
        """Handle image capture event"""
        self.log_event(f"Image captured at {event.timestamp}")

        if event.is_stitched_image:
            # 画像が更新されないようにauto captureを止める
            if self.auto_capture_active:
                self.stop_auto_capture()
            self.stitched_image_flag = True
        else:
            self.stitched_image_flag = False

        # Display the captured image
        self.display_image(event.image_data)

    def display_image(self, image_data):
        """Display an image in the GUI as large as possible"""
        try:
            # Convert image data to numpy array for cv2 processing
            if isinstance(image_data, bytes):
                # If image_data is bytes, load from bytes
                pil_image = Image.open(io.BytesIO(image_data))
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            elif hasattr(image_data, 'save'):
                # If image_data is already a PIL Image
                cv_image = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGB2BGR)
            else:
                # Assume it's already a numpy array (cv2 image)
                cv_image = image_data

            # Get current image dimensions
            height, width = cv_image.shape[:2]

            # Set maximum display size based on window size - much larger
            # Use most of the available window space for image display
            max_width = int(self.root.winfo_width() * 0.95) if self.root.winfo_width() > 1 else 1200
            max_height = int(self.root.winfo_height() * 0.7) if self.root.winfo_height() > 1 else 800

            # Ensure minimum size for small images
            min_size = 300

            # Calculate scale factor to fit the image in the display area
            scale_x = max_width / width
            scale_y = max_height / height

            # Use the smaller scale to maintain aspect ratio
            scale = min(scale_x, scale_y)

            # If image is smaller than minimum size, enlarge it while maintaining aspect ratio
            if width < min_size and height < min_size:
                min_scale = min_size / min(width, height)
                scale = max(scale, min_scale)
                # Recalculate to ensure we don't exceed max dimensions
                scale = min(scale, max_width / width, max_height / height)

            # Calculate new dimensions
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Resize image using cv2 with high-quality interpolation
            if scale > 1:
                # Use INTER_CUBIC for upscaling (enlarging)
                resized_image = cv2.resize(cv_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            else:
                # Use INTER_AREA for downscaling
                resized_image = cv2.resize(cv_image, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # Convert back to PIL Image for tkinter
            rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)

            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(pil_image)

            # Update the image label
            self.image_label.configure(image=photo, text="")
            # Keep a reference to prevent garbage collection
            self.image_label.image = photo

            # Log the image scaling info
            self.log_event(f"Image displayed: {width}x{height} -> {new_width}x{new_height} (scale: {scale:.2f})")

        except Exception as e:
            self.log_event(f"Failed to display image: {str(e)}")
            self.image_label.configure(image="", text=f"Failed to display image: {str(e)}")

    def on_error(self, event: ErrorEvent):
        """Handle error event"""
        self.log_event(f"ERROR: {event.error_message}")
        messagebox.showerror("Error", event.error_message)

    def on_start_move(self, event: StartMoveEvent):
        """Handle start move event"""
        self.log_event(f"Move started: Speed={event.speed}, Direction={event.direction}°")

    def on_stop_move(self, event: StopMoveEvent):
        """Handle stop move event"""
        self.log_event("Move stopped")

    def on_move_to(self, event: MoveToEvent):
        """Handle move to event"""
        self.log_event(f"Moving to {event.target_pos}, relative: {event.is_relative}")

    def on_position_update(self, event: PositionUpdateEvent):
        """Handle position update event"""
        # Update the current position label
        self.current_pos_label.configure(text=f"X: {event.x:.3f} mm, Y: {event.y:.3f} mm")

    def start_position_updates(self):
        """Start periodic position updates every 1 second"""
        self.update_position()

    def update_position(self):
        """Update position by calling controller service check_status"""
        if self.position_update_timer:
            self.root.after_cancel(self.position_update_timer)

        try:
            # Call check_status which will publish PositionUpdateEvent
            self.controller_service.check_status()
        except Exception as e:
            # Silently handle errors to avoid spamming the log
            pass

        # Schedule next update in 1000ms (1 second)
        self.position_update_timer = self.root.after(1000, self.update_position)

    def stop_position_updates(self):
        """Stop periodic position updates"""
        if self.position_update_timer:
            self.root.after_cancel(self.position_update_timer)
            self.position_update_timer = None

    def start_stitching(self):
        """Start stitching process"""
        try:
            # Get parameters from GUI
            grid_x = self.grid_x_var.get()
            grid_y = self.grid_y_var.get()
            magnitude_str = self.magnitude_var.get()
            corner_str = self.corner_var.get()

            # Convert string values to enums
            magnitude = None
            for mag in CameraMagnitude:
                if mag.value == magnitude_str:
                    magnitude = mag
                    break

            corner = None
            for cor in CornerPosition:
                if cor.value == corner_str:
                    corner = cor
                    break

            if magnitude is None or corner is None:
                self.log_event("ERROR: Invalid magnitude or corner selection")
                return

            # Validate grid size
            if grid_x < 1 or grid_y < 1:
                self.log_event("ERROR: Grid size must be at least 1x1")
                return

            # Disable stitching button and stop manual controller
            self.stitching_button.configure(state="disabled")
            self.stitching_status.configure(text="Starting...")
            self.manual_controller.stop()

            # Start stitching controller
            self.stitching_controller.start()
            success_flag = self.stitching_controller.stitching(grid_x, grid_y, magnitude, corner)
            if not success_flag:
                self.end_stitching()
                self.log_event("ERROR: Stitching process failed to start")
            else:
                self.log_event(f"Stitching started: {grid_x}x{grid_y} grid, {magnitude_str} magnitude, starting from {corner_str}")

        except Exception as e:
            self.log_event(f"ERROR: Failed to start stitching: {str(e)}")
            self.stitching_button.configure(state="normal")
            self.stitching_status.configure(text="Error")

    def on_stitching_progress(self, event: StitchingProgressEvent):
        """Handle stitching progress event"""
        self.log_event(f"STITCHING: {event.progress_message}")
        self.stitching_status.configure(text=event.progress_message)

        if event.status == ProgressStatus.COMPLETED:
            self.log_event("STITCHING: Completed successfully")
            self.end_stitching()
        elif event.status == ProgressStatus.FAILED:
            self.log_event("STITCHING: Failed")
            self.stitching_controller.stop()  # Stop stitching controller
        elif event.status == ProgressStatus.CANCELLED:
            self.log_event("STITCHING: Cancelled")
            self.stitching_controller.stop()  # Stop stitching controller

    def end_stitching(self):
        self.stitching_controller.stop()  # Stop stitching controller
        self.stitching_button.configure(state="normal")
        self.stitching_status.configure(text="Ready")
        # Restart manual controller
        self.manual_controller.start()

    def log_event(self, message):
        """Add event to log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)

        # Keep only last 100 lines
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines) - 100}.0")


def main():
    root = tk.Tk()
    app = MicroscopeGUI(root)

    # Handle window closing
    def on_closing():
        app.stop_auto_capture()  # Stop auto capture timer
        app.stop_position_updates()  # Stop position update timer
        app.manual_controller.stop()
        app.stitching_controller.stop()  # Stop stitching controller
        event_bus.clear_all_subscribers()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
