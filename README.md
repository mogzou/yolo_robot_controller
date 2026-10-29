# yolo_robot_controller

YOLOv8 と ROS 2 (Humble) を用いた CRANE+ V2 ロボットアームのリアルタイム視覚追従制御（ビジュアルサーボ）パッケージです。

## 概要
Gazebo 上のアーム先端カメラ画像から YOLOv8n で対象物体（Coke Can）を検出し、その偏差（Error X）に基づいて CRANE+ V2 の第1関節（土台）を P制御で自動回転させ、常にカメラ視野中央に対象を追従させます。

## パッケージ構成
- `yolo_robot_controller/detector_node.py`: YOLOv8n による物体検出および中心偏差 (Error X) の計算・パブリッシュ
- `yolo_robot_controller/controller_node.py`: 偏差に基づく P制御 (比例制御) による関節軌道コマンド生成
- `worlds/custom_table.sdf`: 先端カメラおよびターゲットモデル（coke_can）を配置した Gazebo ワールドファイル
- `launch/yolo_crane_plus.launch.py`: シミュレータおよび全ノードの一括起動用ローンチファイル

## 実行方法
```bash
# 1. ビルド
cd /workspace/final_ws
colcon build --symlink-install --packages-select yolo_robot_controller
source install/setup.bash

# 2. システム一括起動
ros2 launch yolo_robot_controller yolo_crane_plus.launch.py
