#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

### path.txt 경로
file_txt = '/home/unita/ros2_ws/src/erp42_path/erp42_path/test_path_global.txt'
###



class ReadPathPublisher(Node):
    def __init__(self):
        super().__init__('read_path_pub')

        self.global_path_pub = self.create_publisher(Path, '/global_path', 10)

        # 미리 한 번만 읽어서 보관
        self.global_path_msg = Path()
        self.global_path_msg.header.frame_id = 'map'
        self.global_path_msg.poses = []

        # 원하는 경로 파일로 교체
        self.read_path_from_file(file_txt)

        # 10 Hz로 전체 경로 퍼블리시
        self.create_timer(0.1, self.publish_full_global_path)
        self.get_logger().info('ReadPathPublisher (full path mode) initialized.')

    def read_path_from_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            self.get_logger().error(f"Failed to read file: {e}")
            return

        poses = []
        for idx, line in enumerate(lines):
            tmp = line.strip().split()
            if len(tmp) >= 2:
                try:
                    x = float(tmp[0]); y = float(tmp[1])
                except ValueError:
                    self.get_logger().warn(f"Invalid float on line {idx}: {line}")
                    continue

                pose = PoseStamped()
                pose.header.frame_id = 'map'
                pose.header.stamp = self.get_clock().now().to_msg()
                pose.pose.position.x = x
                pose.pose.position.y = y
                pose.pose.position.z = 0.0
                pose.pose.orientation.w = 1.0
                poses.append(pose)

        self.global_path_msg.poses = poses
        self.get_logger().info(f"Loaded {len(self.global_path_msg.poses)} waypoints.")

    def publish_full_global_path(self):
        # 오도메트리와 무관하게 전체 경로 그대로 퍼블리시
        if not self.global_path_msg.poses:
            return
        self.global_path_msg.header.stamp = self.get_clock().now().to_msg()
        self.global_path_pub.publish(self.global_path_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ReadPathPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
