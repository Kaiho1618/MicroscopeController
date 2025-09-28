# 目的と背景
- やりたいこと
  - スニッチング(顕微鏡ステージを自動で操作し、複数の画像をつなぎ合わせる)
  - GUI操作(本プログラム上で手動で顕微鏡を操作できるようにする)
  
## 機能要件
- スニッチング
  - ステージの相対移動
  - パラメータのGUIでの設定
  - 画像のキャプチャ
  - 画像のつなぎ合わせ
  - 画像の保存

- GUI操作
  - 現在の画像の表示
  - 手動操作
    - 矢印キーでの操作
    - クリックした画像の場所に移動

- エラー処理
    - カメラが認識されなかった場合
    - コントローラーが認識できなかった場合
- テスト環境
  - カメラおよびコントローラーの接続なしで、スニッチングおよびGUI操作が正常に動作するかをテスト
  

## アーキテクチャ
- プレゼンテーション層
  - メイン画面
    - 顕微鏡の画像表示画面
    - パラメータの表示・変更画面
- アプリケーション層
  - イベントバス
    - GUI、各種サービス、各種コントローラでの操作など、すべてはここで管理される。
  - スニッチングコントローラ
    - スニッチングのためのステージ移動および画像撮影・結合・保存の要請を行う
  - 手動コントローラ
    - ステージの移動および画像撮影・保存の要請を行う
-  サービス層
   -  カメラサービス
   -  ステージサービス
   -  ファイルサービス


# データフロー
イベント駆動型である。
イベントバス←→GUI  
イベントバス←→コントローラ  
イベントバス←→サービス  

## テスト環境
サービス層をMOCKにすることで、それより上位の層を変更せずにテストを可能にする

## ファイル構成
   microscope_controller/  
   ├── __init__.py  
   ├── presentation/  
   │   ├── __init__.py  
   │   ├── main_window.py  
   │   └── dialogs/  
   ├── application/  
   │   ├── __init__.py  
   │   ├── event_bus.py  
   │   ├── stitching_controller.py  
   |   └── manual_controller.py  
   ├── services/  
   │   ├── __init__.py
   │   ├── image_process_service.py
   │   ├── file_service.py  
   │   ├── camera_service.py  
   │   └── stage_service.py  
   |   
   └── settings  
       └── config.yaml  

# 仕様の詳細
## イベントの種類
- ImageCaptureEvenet
  - 発生条件: 顕微鏡から画像を取得したとき
  - 変数: image_data, timestamp
- ErrorEvenet:
  - 発生条件: 何かしらのエラーが発生した時
  - 変数: error_message
- StageMoveEvent
  - 発生条件: ステージが移動しているとき
  - 変数: speed, target_pos, is_relative
- SnitchingProgressEvent
  - 発生条件: スティッチングをしているとき
  - 変数: error_message
  
## 各ファイルの主な関数
- main_window.py
    - gui
      - GUIを構成する
      - 入力: なし
      - 出力: なし
    - setup_event_subscriptions
      - ImageCaptureEvent, ErrorEvent, SnitchingProgressEventの購読を行う
      - 入力:なし
      - 出力: なし
    - on_image_capture
      - 画像のキャプチャの通知を受け取り、GUIの画像を更新する
      - 入力: ImageCaptureEvent
      - 出力: なし
    - on_error
      - GUIにエラーを表示する
      - 入力: ErrorEvent
      - 出力: なし
    - on_stiching
      - スティッチング中は、ボタンを押せないようにする。
      - スティッチング終了後は、撮影した結合写真を表示する
      - 入力: StinchigEvent
      - 出力: なし
    - start_stitching_clicked
      - マニュアルコントローラーを停止し、スティッチングコントローラーを呼び出す
      - 入力: なし
    - manual_control_clicked
      - マニュアルコントローラーを呼び出す
      - 出力: なし
    - save_image_clicked
      - エクスプローラを開き、現在表示されている画像を保存する
      - 入力: なし
      - 出力: なし

- stiching_controller
  - stiching
    - スティッチングを行うおおもとの関数
    - 入力: なし
    - 出力: なし
  - generate_trajectory
    - StageServiceから現在の座標を取得し、ステージの軌跡を生成する
    - 入力: なし
    - 出力: ステージの軌跡の相対位置のリスト。もし移動制限に触れる場合は空のリストを返す
  - move_and_capture
    - 移動された座標に移動し、撮影することを繰り返す
    - 入力: ステージの軌跡の相対位置のリスト
    - 出力: 各位置で取得した画像
  - concatenate_images
    - image_process_serviceを呼び出し、画像を結合する
    - 入力: 各位置で取得した画像
    - 出力: 結合された画像

- manual_controller
  - stop
    - マニュアルコントローラを停止する(コントローラがうごいているならばstop_moveを呼び出す)
    - 入力: なし
    - 出力: なし
  - start_move
    - ステージの移動を開始する
    - 入力: speed, direction
    - 出力: なし
  - stop_move
    - ステージの移動を終了する
    - 入力: なし
    - 出力: なし
  - move_to
    - 指定された座標に移動する
    - 入力: x, y, is_relative(相対座標か)
    - 出力: なし
- image_process_service
  - concatenate
    - 画像を結合する
    - 入力: ステージの動きの種類、画像
    - 出力: 結合した画像
- camera_service
  - init
    - カメラと接続する。接続できなかった場合はErrorEventを発生させる
    - 入力: なし
    - 出力: なし
  - capture
    - 画像を撮影する。
    - 入力: なし
    - 出力: 撮影した画像
  - handle_error
    - 撮影が失敗した場合、カメラと接続できているかなどの確認を行う
- stage_service
  - init
    - ステージと接続する。接続できなかった場合はErrorEventを発生させる
    - 入力: COMなどシリアル通信に必要な情報
    - 出力: なし
  - move_to
    - 指定された座標に移動する
    - 入力: x, y, is_relative(相対座標か)
    - 出力: なし
  - start_move
    - 移動を開始する
    - 入力: speed, direction
    - 出力: なし
  - stop_move
    - 移動を停止する
    - 入力: なし
    - 出力: なし
  - is_moving
    - ステージが動いているかどうかを判定する
    - 入力: なし
    - 出力: 動いているならばtrue, 停止しているならばfalse

  

# 非同期処理
以下のみ非同期で動かす。これ以外は同期処理とする。
・GUI
・画像の保存