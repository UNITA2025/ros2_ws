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
    """전역경로 → 주차경로 → 후진 → 전역경로 복귀 FSM"""

    def __init__(self):
        super().__init__('path_manager')

        # 상태
        self.current_mode = "normal"
        self.current_position: Optional[Point] = None
        self.global_path: Optional[Path] = None
        self.parking_path: Optional[Path] = None
        self.reverse_start_time = None

        # 파라미터
        self.declare_parameter('parking_proximity_threshold', 3.0)   # 주차 진입 거리
        self.declare_parameter('parking_complete_threshold', 1.0)    # 주차 완료 거리
        self.declare_parameter('reverse_duration_s', 5.0)            # 후진 시간
        self.declare_parameter('reverse_speed', 30)                  # 후진 속도
        self.declare_parameter('reverse_steer', 0)                   # 후진 조향
        self.declare_parameter('reverse_brake', 0)

        self.parking_thr = float(self.get_parameter('parking_proximity_threshold').value)
        self.done_thr = float(self.get_parameter('parking_complete_threshold').value)
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
                self._publish_mode()
                if self.parking_path:
                    self.active_path_pub.publish(self.parking_path)

        elif self.current_mode == "parking":
            self.pakring_steer_duration = 3.0  # 주차 예상 시간
            self.parking_foward_duration = 3.0 # 주차 후 전진 예상 시간
            self.parking_start_time = time.time()
            if self._parking_done():
                self.current_mode = "reverse_out"
                self.reverse_start_time = time.time()
                self._publish_mode()
                self.get_logger().info("✅ Parking done → Reverse start")
            elif self.parking_start_time < self.pakring_steer_duration : # 주차 중에는 계속 주차 경로 명령
                self.pakring_steer_cmd()
            elif self.parking_foward_start_time < self.parking_foward_duration: # 주차 후 전진
                cmd = ErpCmdMsg()
                cmd.gear = 1  # 전진
                cmd.speed = 70
                cmd.steer = 0
                cmd.brake = 0
                self.cmd_pub.publish(cmd)
            else: # 주차 후 전진 완료
                cmd = ErpCmdMsg()
                cmd.gear = 1  # 전진
                cmd.speed = 0
                cmd.steer = 0
                cmd.brake = 100
                self.cmd_pub.publish(cmd)
            
        elif self.current_mode == "reverse_out":
            elapsed = time.time() - self.reverse_start_time
            if elapsed < self.reverse_duration:
                self.publish_reverse_cmd()
                return
            else:
                self.get_logger().info("↩ Reverse done → Resume global path")
                self.current_mode = "normal"
                self._publish_mode()
                if self.global_path:
                    self.active_path_pub.publish(self.global_path)

    # --- 조건 ---
    def _should_enter_parking(self) -> bool:
        if not self.parking_path or not self.parking_path.poses:
            return False
        start = self.parking_path.poses[0].pose.position
        return self._dist(self.current_position, start) < self.parking_thr

    def _parking_done(self) -> bool:
        if not self.parking_path or not self.parking_path.poses:
            return False
        end = self.parking_path.poses[-1].pose.position
        return self._dist(self.current_position, end) < self.done_thr

    # --- 퍼블리시 ---
    def _publish_mode(self):
        msg = String()
        msg.data = self.current_mode
        self.mode_pub.publish(msg)

    def pakring_steer_cmd(self):
        cmd = ErpCmdMsg()
        cmd.gear = 1  # 전진
        cmd.speed = 70
        cmd.steer = 2000
        cmd.brake = 0
        self.cmd_pub.publish(cmd)
        self.parking_foward_start_time = time.time()

    def publish_reverse_cmd(self):
        cmd = ErpCmdMsg()
        cmd.gear = 2
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
