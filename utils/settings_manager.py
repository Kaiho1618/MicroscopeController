import json
import os
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages persistent GUI settings"""

    def __init__(self, settings_file: str = "settings/gui_settings.json"):
        """
        Initialize the settings manager

        Args:
            settings_file (str): Path to the settings file
        """
        self.settings_file = settings_file
        self.default_settings = {
            "speed": "S1",
            "grid_x": 3,
            "grid_y": 3,
            "magnitude": "x10",
            "corner": "top_left",
            "last_save_directory": os.path.expanduser("~"),
            "x_position": 0.0,
            "y_position": 0.0,
            "relative": True
        }

    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from file

        Returns:
            Dict[str, Any]: Settings dictionary
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge with defaults to handle new settings
                    return {**self.default_settings, **settings}
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Warning: Failed to load settings from {self.settings_file}: {e}")
            return self.default_settings.copy()

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save settings to file

        Args:
            settings (Dict[str, Any]): Settings to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Failed to save settings to {self.settings_file}: {e}")
            return False

    def get_setting(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a specific setting value

        Args:
            key (str): Setting key
            default (Optional[Any]): Default value if key not found

        Returns:
            Any: Setting value
        """
        settings = self.load_settings()
        return settings.get(key, default)

    def update_setting(self, key: str, value: Any) -> bool:
        """
        Update a specific setting

        Args:
            key (str): Setting key
            value (Any): New value

        Returns:
            bool: True if successful
        """
        settings = self.load_settings()
        settings[key] = value
        return self.save_settings(settings)
