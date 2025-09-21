#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from nav_msgs.msg import Path, Odometry
from std_msgs.msg import String

from interfaces_control_pkg.msg import ErpCmdMsg


class PathManager(Node):
    """전역경로 → 주차(조향) → 주차 전진 → 후진 → 전역경로 복귀 FSM"""

    def __init__(self):
        super().__init__('path_manager')

        # 상태
        self.current_mode = "normal"
        self.current_position: Optional[Point] = None
        self.global_path: Optional[Path] = None
        self.parking_path: Optional[Path] = None

        # 타이머 변수
        self.parking_start_time = None
        self.parking_forward_start_time = None
        self.reverse_start_time = None

        # 파라미터
        self.declare_parameter('parking_proximity_threshold', 1.0)   # 주차 진입 거리
        self.declare_parameter('parking_complete_threshold', 1.0)    # 주차 완료 거리
        self.declare_parameter('steer_duration', 3.0)                # 주차 조향 시간
        self.declare_parameter('forward_duration', 3.0)              # 주차 후 전진 시간
        self.declare_parameter('reverse_duration_s', 5.0)            # 후진 시간
        self.declare_parameter('reverse_speed', 30)                  # 후진 속도
        self.declare_parameter('reverse_steer', 0)                   # 후진 조향
        self.declare_parameter('reverse_brake', 0)

        self.parking_thr = float(self.get_parameter('parking_proximity_threshold').value)
        self.done_thr = float(self.get_parameter('parking_complete_threshold').value)
        self.steer_duration = float(self.get_parameter('steer_duration').value)
        self.forward_duration = float(self.get_parameter('forward_duration').value)
        self.reverse_duration = float(self.get_parameter('reverse_duration_s').value)
        self.reverse_speed = int(self.get_parameter('reverse_speed').value)
        self.reverse_steer = int(self.get_parameter('reverse_steer').value)
        self.reverse_brake = int(self.get_parameter('reverse_brake').value)

        # ROS Pub/Sub
        self.active_path_pub = self.create_publisher(Path, '/active_path', 10)
        self.mode_pub = self.create_publisher(String, '/controller_mode', 10)
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)

        self.create_subscription(Odometry, '/odometry/local_enu', self.odom_cb, 10)
        self.create_subscription(Path, '/global_path', self.global_path_cb, 10)
        self.create_subscription(Path, '/parking_path', self.parking_path_cb, 10)

        self.timer = self.create_timer(0.1, self.main_loop)

        self.get_logger().info("✅ PathManager started (FSM only)")

    # --- 콜백 ---
    def odom_cb(self, msg: Odometry):
        self.current_position = msg.pose.pose.position

    def global_path_cb(self, msg: Path):
        self.global_path = msg
        if self.current_mode == "normal":
            self.active_path_pub.publish(msg)

    def parking_path_cb(self, msg: Path):
        self.parking_path = msg

    # --- 메인 FSM ---
    def main_loop(self):
        if not self.current_position:
            return

        if self.current_mode == "normal":
            if self._should_enter_parking():
                self.current_mode = "parking"
                self.parking_start_time = time.time()   # ✅ parking 시작 시점 기록
                self._publish_mode()
                self.get_logger().info("🚗 Parking start")
                if self.parking_path:
                    self.active_path_pub.publish(self.parking_path)

        elif self.current_mode == "parking":
            elapsed = time.time() - self.parking_start_time
            if elapsed < self.steer_duration:
                self.pakring_steer_cmd()  # ✅ 조향 명령
            else:
                # 조향 끝나면 parking_forward로 전환
                self.current_mode = "parking_forward"
                self.parking_forward_start_time = time.time()
                self._publish_mode()
                self.get_logger().info("➡ Parking forward start")

        elif self.current_mode == "parking_forward":
            elapsed = time.time() - self.parking_forward_start_time
            if elapsed < self.forward_duration:
                self.publish_forward_cmd()
            else:
                # 전진 끝나면 후진 시작
                self.current_mode = "reverse_out"
                self.reverse_start_time = time.time()
                self._publish_mode()
                self.get_logger().info("↩ Reverse start")

        elif self.current_mode == "reverse_out":
            elapsed = time.time() - self.reverse_start_time
            if elapsed < self.reverse_duration:
                self.publish_reverse_cmd()
            else:
                # 후진 완료 → 전역경로 복귀
                self.current_mode = "normal"
                self._publish_mode()
                if self.global_path:
                    self.active_path_pub.publish(self.global_path)
                self.get_logger().info("✅ Back to normal path")

    # --- 조건 ---
    def _should_enter_parking(self) -> bool:
        if not self.parking_path or not self.parking_path.poses:
            return False
        start = self.parking_path.poses[0].pose.position
        return self._dist(self.current_position, start) < self.parking_thr

    # --- 퍼블리시 ---
    def _publish_mode(self):
        msg = String()
        msg.data = self.current_mode
        self.mode_pub.publish(msg)

    def pakring_steer_cmd(self):
        cmd = ErpCmdMsg()
        cmd.gear = 1  # 전진
        cmd.speed = 70
        cmd.steer = 2000   # 조향 크게
        cmd.brake = 0
        self.cmd_pub.publish(cmd)

    def publish_forward_cmd(self):
        cmd = ErpCmdMsg()
        cmd.gear = 1  # 전진
        cmd.speed = 70
        cmd.steer = 0
        cmd.brake = 0
        self.cmd_pub.publish(cmd)

    def publish_reverse_cmd(self):
        cmd = ErpCmdMsg()
        cmd.gear = 2  # 후진
        cmd.speed = self.reverse_speed
        cmd.steer = self.reverse_steer
        cmd.brake = self.reverse_brake
        self.cmd_pub.publish(cmd)

    # --- 유틸 ---
    @staticmethod
    def _dist(p1: Point, p2: Point) -> float:
        return math.hypot(p1.x - p2.x, p1.y - p2.y)


def main(args=None):
    rclpy.init(args=args)
    node = PathManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
