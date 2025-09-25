#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from std_msgs.msg import Float32MultiArray
from interfaces_control_pkg.msg import ErpCmdMsg

import math
import time

class ScenarioManager(Node):
    def __init__(self):
        super().__init__('scenario_manager')

        # Publishers
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
        self.path_pub = self.create_publisher(Path, '/selected_path', 10)

        # Subscribers
        self.create_subscription(Float32MultiArray, '/gps_map', self.gps_callback, 10)
        self.create_subscription(Path, '/global_path', self.global_path_callback, 10)
        self.create_subscription(Path, '/parking_path', self.parking_path_callback, 10)

        # States
        self.state = "DRIVE_GLOBAL"
        self.global_path = None
        self.parking_path = None
        self.current_path = None

        # Trigger points (예시 좌표, 실제 GPS 좌표로 수정 필요)
        self.parking_trigger = (123.0, 456.0)

        self.current_pose = (0.0, 0.0)

        # 후진 관련
        self.reverse_duration = 5.0   # n초간 후진
        self.reverse_speed = 50       # ERP42 speed 값 (저속)
        self.reverse_start_time = None

        self.timer = self.create_timer(0.1, self.run)

    def gps_callback(self, msg: Float32MultiArray):
        if len(msg.data) >= 2:
            self.current_pose = (msg.data[0], msg.data[1])

    def global_path_callback(self, msg: Path):
        self.global_path = msg
        if self.state == "DRIVE_GLOBAL":
            self.current_path = msg

    def parking_path_callback(self, msg: Path):
        self.parking_path = msg

    def run(self):
        x, y = self.current_pose

        if self.state == "DRIVE_GLOBAL":
            if self.distance(self.current_pose, self.parking_trigger) < 3.0:
                self.get_logger().info("🚗 Parking mode 진입")
                self.state = "ENTER_PARKING"
                self.current_path = self.parking_path

        elif self.state == "ENTER_PARKING":
            if self.is_path_finished(self.parking_path, x, y):
                self.get_logger().info("✅ Parking 완료 → 후진 시작")
                self.state = "PARKING_DONE"
                self.reverse_start_time = time.time()

        elif self.state == "PARKING_DONE":
            self.state = "REVERSE_OUT"

        elif self.state == "REVERSE_OUT":
            elapsed = time.time() - self.reverse_start_time
            if elapsed < self.reverse_duration:
                self.publish_cmd(gear=2, speed=self.reverse_speed, steer=0, brake=0)  # 후진
                return
            else:
                self.get_logger().info("↩ 후진 완료 → Global Path 합류")
                self.state = "MERGE_GLOBAL"
                self.current_path = self.global_path

        elif self.state == "MERGE_GLOBAL":
            self.publish_cmd(gear=1, speed=30, steer=0, brake=0)  # 다시 주행
            # 필요하다면 다시 DRIVE_GLOBAL로 전환
            self.state = "DRIVE_GLOBAL"

        # 현재 선택된 path publish
        if self.current_path:
            self.path_pub.publish(self.current_path)

        # Global/ Parking 모드일 때만 Drive 명령
        if self.state in ["DRIVE_GLOBAL", "ENTER_PARKING"]:
            self.publish_cmd(gear=1, speed=30, steer=0, brake=0)

    def publish_cmd(self, gear=1, speed=0, steer=0, brake=0):
        cmd = ErpCmdMsg()
        cmd.e_stop = False
        cmd.gear = gear
        cmd.speed = speed
        cmd.steer = steer
        cmd.brake = brake
        self.cmd_pub.publish(cmd)

    def distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def is_path_finished(self, path_msg: Path, x, y):
        if not path_msg or not path_msg.poses:
            return False
        last = path_msg.poses[-1].pose.position
        return self.distance((x, y), (last.x, last.y)) < 2.0


def main(args=None):
    rclpy.init(args=args)
    node = ScenarioManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()