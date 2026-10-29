#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

class DetectorNode(Node):
    def __init__(self):
        super().__init__('detector_node')
        
        # /camera/image_raw トピックのサブスクライブ
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
        
        # 偏差（ズレ量）のパブリッシャー
        self.publisher_ = self.create_publisher(Float32, '/yolo/detection', 10)
        
        # デバッグ用（YOLO描画済み画像）のパブリッシャー
        self.debug_pub = self.create_publisher(Image, '/yolo/debug_image', 10)
        
        self.bridge = CvBridge()
        
        self.get_logger().info('Loading YOLOv8 model...')
        self.model = YOLO('yolov8n.pt')
        self.get_logger().info('Detector Node initialized successfully!')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            height, width, _ = cv_image.shape
            img_center_x = width / 2.0

            # 信頼度閾値を conf=0.1 に設定して検出
            results = self.model(cv_image, conf=0.1, verbose=False)

            best_box = None
            max_conf = 0.0

            for result in results:
                for box in result.boxes:
                    conf = float(box.conf)
                    if conf > max_conf:
                        max_conf = conf
                        best_box = box

            error_msg = Float32()

            if best_box is not None:
                # [x1, y1, x2, y2] の座標を正しく取得
                x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
                obj_center_x = float((x1 + x2) / 2.0)
                
                error_x = obj_center_x - img_center_x
                error_msg.data = float(error_x)

                cls_id = int(best_box.cls[0])
                cls_name = self.model.names[cls_id]

                self.get_logger().info(
                    f'Detected [{cls_name}]! Center X: {obj_center_x:.1f}px, '
                    f'Error X: {error_x:.1f}px (Conf: {max_conf:.2f})'
                )
            else:
                error_msg.data = 0.0
                self.get_logger().info('Searching for objects (not detected)...', throttle_duration_sec=1.0)

            self.publisher_.publish(error_msg)

            # デバッグ用画像の描画とパブリッシュ (results[0].plot() を使用)
            if len(results) > 0:
                annotated_frame = results[0].plot()
                debug_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
                self.debug_pub.publish(debug_msg)

        except Exception as e:
            self.get_logger().error(f'Error in image_callback: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()