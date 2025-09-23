#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import time
from typing import Optional
from enum import Enum

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from nav_msgs.msg import Path, Odometry
from std_msgs.msg import String

from interfaces_control_pkg.msg import ErpCmdMsg


class ParkingState(Enum):
    """주차 상태 정의"""
    NORMAL = "normal"
    DETECTION_STOP = "detection_stop"
    STEER = "steer"
    FORWARD = "forward"
    PARKING_STOP = "parking_stop"
    REVERSE = "reverse"
    REVERSE_STEER = "reverse_steer"
    COMPLETED = "completed"


class IntegratedParkingManager(Node):
    """통합 주차 관리자 - parking_path 감지 → 정지 → 주차 시퀀스 → 복귀"""

    def __init__(self):
        super().__init__('integrated_parking_manager')

        # === 상태 및 데이터 ===
        self.current_state = ParkingState.NORMAL
        self.current_position: Optional[Point] = None
        self.global_path: Optional[Path] = None
        self.parking_path: Optional[Path] = None
        
        # 타이머 변수
        self.state_start_time = None
        self.is_parking_started = False

        # === 기어 상수 ===
        self.FORWARD_GEAR = 0
        self.REVERSE_GEAR = 2

        # === ROS2 파라미터 ===
        self._declare_parameters()
        self._load_parameters()

        # === ROS Pub/Sub ===
        self.active_path_pub = self.create_publisher(Path, '/active_path', 10)
        self.state_pub = self.create_publisher(String, '/parking_state', 10)
        self.mode_pub = self.create_publisher(String, '/controller_mode', 10)
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)

        self.create_subscription(Odometry, '/odometry/local_enu', self.odom_cb, 10)
        self.create_subscription(Path, '/global_path', self.global_path_cb, 10)
        self.create_subscription(Path, '/parking_path', self.parking_path_cb, 10)

        # 메인 타이머 (10Hz)
        self.timer = self.create_timer(0.1, self.main_loop)

        self.get_logger().info("🅿️ Integrated Parking Manager started!")
        self._log_parameters()

    def _declare_parameters(self):
        """ROS2 파라미터 선언"""
        # 거리 임계값
        self.declare_parameter('parking_proximity_threshold', 0.5) # speed 200 : 5, 100: 3, 50: 1.5 maybe?
        self.declare_parameter('parking_complete_threshold', 1.0)
        
        # 시간 설정
        self.declare_parameter('detection_stop_duration', 4.0)

        self.declare_parameter('steer_duration', 4.0)
        self.declare_parameter('forward_duration', 2.5)
        self.declare_parameter('parking_stop_duration', 3.0)
        self.declare_parameter('reverse_duration', 3.0)
        self.declare_parameter('reverse_steer_duration', 1.5)
        
        # 조향 설정
        self.declare_parameter('steer_angle', 2000)
        self.declare_parameter('reverse_steer_angle', 0)
        
        # 속도 설정
        self.declare_parameter('forward_speed', 100)
        self.declare_parameter('reverse_speed', 100)
        
        # 브레이크 설정
        self.declare_parameter('detection_stop_brake', 33)
        self.declare_parameter('parking_stop_brake', 33)

    def _load_parameters(self):
        """파라미터 로드"""
        # 거리 임계값
        self.parking_thr = self.get_parameter('parking_proximity_threshold').value
        self.done_thr = self.get_parameter('parking_complete_threshold').value
        
        # 시간 설정
        self.detection_stop_duration = self.get_parameter('detection_stop_duration').value
        self.steer_duration = self.get_parameter('steer_duration').value
        self.forward_duration = self.get_parameter('forward_duration').value
        self.parking_stop_duration = self.get_parameter('parking_stop_duration').value
        self.reverse_duration = self.get_parameter('reverse_duration').value
        self.reverse_steer_duration = self.get_parameter('reverse_steer_duration').value
        
        # 조향 설정
        self.steer_angle = self.get_parameter('steer_angle').value
        self.reverse_steer_angle = self.get_parameter('reverse_steer_angle').value
        
        # 속도 설정
        self.forward_speed = self.get_parameter('forward_speed').value
        self.reverse_speed = self.get_parameter('reverse_speed').value
        
        # 브레이크 설정
        self.detection_stop_brake = self.get_parameter('detection_stop_brake').value
        self.parking_stop_brake = self.get_parameter('parking_stop_brake').value

    def _log_parameters(self):
        """현재 파라미터 출력"""
        self.get_logger().info("=== Integrated Parking Parameters ===")
        self.get_logger().info(f"Detection threshold: {self.parking_thr}m")
        self.get_logger().info(f"0. DETECTION_STOP: {self.detection_stop_duration}s, brake={self.detection_stop_brake}")
        self.get_logger().info(f"1. STEER         : {self.steer_duration}s, angle={self.steer_angle}, speed={self.forward_speed}")
        self.get_logger().info(f"2. FORWARD       : {self.forward_duration}s, speed={self.forward_speed}")
        self.get_logger().info(f"3. PARKING_STOP  : {self.parking_stop_duration}s, brake={self.parking_stop_brake}")
        self.get_logger().info(f"4. REVERSE       : {self.reverse_duration}s, speed={self.reverse_speed}")
        self.get_logger().info(f"5. REVERSE_STEER : {self.reverse_steer_duration}s, speed={self.reverse_speed}, steer={self.steer_angle}")
        self.get_logger().info("=====================================")

    # === 콜백 함수 ===
    def odom_cb(self, msg: Odometry):
        """오도메트리 콜백"""
        self.current_position = msg.pose.pose.position

    def global_path_cb(self, msg: Path):
        """전역 경로 콜백"""
        self.global_path = msg
        if self.current_state == ParkingState.NORMAL:
            self.active_path_pub.publish(msg)

    def parking_path_cb(self, msg: Path):
        """주차 경로 콜백"""
        self.parking_path = msg

    # === 메인 FSM 루프 ===
    def main_loop(self):
        """메인 FSM 루프"""
        if not self.current_position:
            return

        elapsed = 0
        if self.state_start_time:
            elapsed = time.time() - self.state_start_time

        if self.current_state == ParkingState.NORMAL:
            self._handle_normal(elapsed)
        elif self.current_state == ParkingState.DETECTION_STOP:
            self._handle_detection_stop(elapsed)
        elif self.current_state == ParkingState.STEER:
            self._handle_steer(elapsed)
        elif self.current_state == ParkingState.FORWARD:
            self._handle_forward(elapsed)
        elif self.current_state == ParkingState.PARKING_STOP:
            self._handle_parking_stop(elapsed)
        elif self.current_state == ParkingState.REVERSE:
            self._handle_reverse(elapsed)
        elif self.current_state == ParkingState.REVERSE_STEER:
            self._handle_reverse_steer(elapsed)
        elif self.current_state == ParkingState.COMPLETED:
            self._handle_completed()

    # === 상태별 핸들러 ===
    def _handle_normal(self, elapsed: float):
        """일반 주행 상태"""
        if self._should_enter_parking() and not self.is_parking_started:
            self._transition_to_state(ParkingState.DETECTION_STOP)
            self.is_parking_started = True
            self.get_logger().info("🛑 Parking path detected! Stopping for safety...")

    def _handle_detection_stop(self, elapsed: float):
        """주차 경로 감지 후 정지 상태"""
        if elapsed < self.detection_stop_duration:
            self._publish_detection_stop_cmd()
            self._log_progress("DETECTION_STOP", elapsed, self.detection_stop_duration)
        else:
            self._transition_to_state(ParkingState.STEER)
            if self.parking_path:
                self.active_path_pub.publish(self.parking_path)

    def _handle_steer(self, elapsed: float):
        """조향 상태"""
        if elapsed < self.steer_duration:
            self._publish_steer_cmd()
            self._log_progress("STEER", elapsed, self.steer_duration)
        else:
            self._transition_to_state(ParkingState.FORWARD)

    def _handle_forward(self, elapsed: float):
        """전진 상태"""
        if elapsed < self.forward_duration:
            self._publish_forward_cmd()
            self._log_progress("FORWARD", elapsed, self.forward_duration)
        else:
            self._transition_to_state(ParkingState.PARKING_STOP)

    def _handle_parking_stop(self, elapsed: float):
        """주차 완료 후 정지 상태"""
        if elapsed < self.parking_stop_duration:
            self._publish_parking_stop_cmd()
            self._log_progress("PARKING_STOP", elapsed, self.parking_stop_duration)
        else:
            self._transition_to_state(ParkingState.REVERSE)

    def _handle_reverse(self, elapsed: float):
        """후진 상태"""
        if elapsed < self.reverse_duration:
            self._publish_reverse_cmd()
            self._log_progress("REVERSE", elapsed, self.reverse_duration)
        else:
            self._transition_to_state(ParkingState.REVERSE_STEER)

    def _handle_reverse_steer(self, elapsed: float):
        """후진 조향 상태"""
        if elapsed < self.reverse_steer_duration:
            self._publish_reverse_steer_cmd()
            self._log_progress("REVERSE_STEER", elapsed, self.reverse_steer_duration)
        else:
            self._transition_to_state(ParkingState.COMPLETED)

    def _handle_completed(self):
        """완료 상태 - 일반 주행으로 복귀"""
        self._transition_to_state(ParkingState.NORMAL)
        # self.is_parking_started = False
        if self.global_path:
            self.active_path_pub.publish(self.global_path)
        self.get_logger().info("✅ Parking sequence completed! Back to normal driving.")

    # === 조건 검사 ===
    def _should_enter_parking(self) -> bool:
        """주차 진입 조건 검사"""
        if not self.parking_path or not self.parking_path.poses:
            return False
        start = self.parking_path.poses[0].pose.position
        return self._dist(self.current_position, start) < self.parking_thr

    # === 상태 전이 ===
    def _transition_to_state(self, new_state: ParkingState):
        """상태 전이"""
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        # 상태 발행
        self._publish_state()
        self._publish_mode()

        self.get_logger().info(f"🔄 {old_state.value} → {new_state.value}")

    # === 명령 발행 ===
    def _publish_cmd(self, gear: int, speed: int, steer: int, brake: int):
        """기본 명령 발행"""
        cmd = ErpCmdMsg()
        cmd.gear = gear
        cmd.speed = speed
        cmd.steer = steer
        cmd.brake = brake
        self.cmd_pub.publish(cmd)

    def _publish_detection_stop_cmd(self):
        """감지 후 정지 명령"""
        self._publish_cmd(self.FORWARD_GEAR, 0, 0, self.detection_stop_brake)

    def _publish_steer_cmd(self):
        """조향 명령 (조향하면서 전진)"""
        self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, self.steer_angle, 0)

    def _publish_forward_cmd(self):
        """전진 명령 (직진)"""
        self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, 0, 0)

    def _publish_parking_stop_cmd(self):
        """주차 후 정지 명령"""
        self._publish_cmd(self.FORWARD_GEAR, 0, 0, self.parking_stop_brake)

    def _publish_reverse_cmd(self):
        """후진 명령"""
        self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, self.reverse_steer_angle, 0)

    def _publish_reverse_steer_cmd(self):
        """후진 조향 명령"""
        self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, self.steer_angle, 0)

    def _publish_state(self):
        """현재 상태 발행"""
        msg = String()
        msg.data = self.current_state.value
        self.state_pub.publish(msg)

    def _publish_mode(self):
        """현재 모드 발행 (기존 시스템 호환성)"""
        msg = String()
        if self.current_state == ParkingState.NORMAL:
            msg.data = "normal"
        else:
            msg.data = "parking"
        self.mode_pub.publish(msg)

    # === 유틸리티 함수 ===
    @staticmethod
    def _dist(p1: Point, p2: Point) -> float:
        """두 점 사이의 거리 계산"""
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _log_progress(self, state_name: str, elapsed: float, total: float):
        """진행률 로깅 (1초마다)"""
        progress = (elapsed / total) * 100
        if int(elapsed) != int(elapsed - 0.1):  # 1초마다 출력
            self.get_logger().info(f"📍 {state_name}: {elapsed:.1f}/{total:.1f}s ({progress:.0f}%)")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = IntegratedParkingManager()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n🛑 Integrated parking manager stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()