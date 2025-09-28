import yaml
from typing import Dict, Any

def load_config(config_file_path: str) -> Dict[str, Any]:
    """
    YAMLファイルから設定を読み込む関数
    
    Args:
        config_file_path (str): YAMLファイルのパス
    
    Returns:
        Dict[str, Any]: 設定辞書
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"エラー: ファイル '{config_file_path}' が見つかりません")
        return {}
    except yaml.YAMLError as e:
        print(f"YAML読み込みエラー: {e}")
        return {}

def main(config_path: str):
    config = load_config(config_path)
    return config
