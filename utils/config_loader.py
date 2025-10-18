import yaml
from typing import Dict, Any, Optional


def load_config(config_file_path: str, mock_override: Optional[bool] = None) -> Dict[str, Any]:
    """
    YAMLファイルから設定を読み込む関数

    Args:
        config_file_path (str): YAMLファイルのパス
        mock_override (Optional[bool]): コマンドラインからのmockフラグの上書き (Noneの場合はconfig.yamlの値を使用)

    Returns:
        Dict[str, Any]: 設定辞書
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        # コマンドラインからのmockフラグが指定されている場合は上書き
        if mock_override is not None:
            config['mock'] = mock_override

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
