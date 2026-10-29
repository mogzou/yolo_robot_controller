#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_node')
        
        # YOLOのズレ量を取得するサブスクライバ
        self.create_subscription(
            Float32,
            '/yolo/detection',
            self.detection_callback,
            10)
        
        # 現在の関節角度を取得するサブスクライバ
        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10)
        
        # アーム制御用のパブリッシャー
        self.publisher_ = self.create_publisher(
            JointTrajectory,
            '/crane_plus_arm_controller/joint_trajectory',
            10)
        
        self.current_joint1_pos = 0.0
        self.joint_names = [
            'crane_plus_joint1',
            'crane_plus_joint2',
            'crane_plus_joint3',
            'crane_plus_joint4'
        ]
        self.current_positions = [0.0, 0.0, 0.0, 0.0]
        self.joint_state_received = False
        
        # P制御（比例制御）のゲイン設定
        self.kp = 0.0015
        
        self.get_logger().info('Controller Node initialized successfully!')

    def joint_state_callback(self, msg):
        # 現在の各関節の角度を取得
        if 'crane_plus_joint1' in msg.name:
            for i, name in enumerate(self.joint_names):
                if name in msg.name:
                    idx = msg.name.index(name)
                    self.current_positions[i] = msg.position[idx]
            self.current_joint1_pos = self.current_positions[0]
            self.joint_state_received = True

    def detection_callback(self, msg):
        if not self.joint_state_received:
            return

        error_x = msg.data
        
        # 偏差が小さい場合（デッドバンド ±5px）は動かさない
        if abs(error_x) < 5.0:
            return

        # P制御による目標角度の計算
        delta_angle = - self.kp * error_x
        target_joint1 = self.current_joint1_pos + delta_angle

        # 関節可動範囲のガード (-1.57 rad 〜 +1.57 rad)
        target_joint1 = max(-1.57, min(1.57, target_joint1))

        # 軌道コマンドの作成と送信
        traj = JointTrajectory()
        traj.joint_names = self.joint_names
        
        point = JointTrajectoryPoint()
        target_positions = list(self.current_positions)
        target_positions[0] = target_joint1
        point.positions = target_positions
        
        # 0.2秒かけてスムーズに動かす
        point.time_from_start = Duration(sec=0, nanosec=200000000)
        traj.points.append(point)

        self.publisher_.publish(traj)
        self.get_logger().info(
            f'Tracking... Error X: {error_x:.1f}px -> Moving Joint1 to {target_joint1:.3f} rad',
            throttle_duration_sec=0.5
        )


def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()