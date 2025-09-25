#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from enum import Enum

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from interfaces_control_pkg.msg import ErpCmdMsg


class ParkingState(Enum):
    """주차 상태 정의"""
    DRIVE = "drive"                # ① 일정 시간 동안 일정 속도로 주행
    STOP_BEFORE_PARK = "stop_before_park"  # ② 주행 후 정지
    STEER = "steer"                # ③ 주차 시퀀스 시작 (조향하며 전진)
    FORWARD = "forward"
    STOP = "stop"
    REVERSE = "reverse"
    REVERSE_STEER = "reverse_steer"
    COMPLETED = "completed"


class ParkingSequenceNode(Node):
    """주차 시퀀스 전용 노드"""

    def __init__(self):
        super().__init__('plusspeedpark1')

        # === [1단계] 주행 관련 파라미터 ===
        self.drive_duration = 4.0     # 직진 주행 시간 (초)
        self.drive_speed = 200          # 직진 속도

        # === [2단계] 주행 후 정지 시간 ===
        self.prestop_duration = 10.0    # 주행 후 정지 시간 (초)

        # === [3단계] 주차 시퀀스 파라미터 ===
        self.steer_duration = 2.6 # 조향 시간
        self.reverse_steer_duration = 0.5     # 조향 시간
        self.forward_duration = 0.7  # 전진 시간
        self.stop_duration = 5.0       # 정지 시간
        self.reverse_duration = 2.5   # 후진 시간
        
        # 조향 설정
        self.steer_angle = 2000        # 조향각 (좌측)
        self.reverse_steer_angle = 0   # 후진 시 조향각
        
        # 속도 설정
        self.forward_speed = 200        # 전진 속도
        self.reverse_speed = 200        # 후진 속도
        

        # 브레이크 값
        self.stop_brake = 200

        # === 초기 상태 (DRIVE부터 시작) ===
        self.current_state = ParkingState.DRIVE
        self.state_start_time = time.time()

        # 기어 상수
        self.FORWARD_GEAR = 0
        self.REVERSE_GEAR = 2

        # ROS Publishers
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
        self.state_pub = self.create_publisher(String, '/parking_state', 10)

        # 메인 타이머 (20Hz)
        self.timer = self.create_timer(0.05, self.main_loop)

        self.get_logger().info("🅿️ Parking sequence (Drive → Stop → Park) started!")
        self._log_parameters()

    def _log_parameters(self):
        """현재 파라미터 출력"""
        self.get_logger().info("=== Parameters ===")
        self.get_logger().info(f"[DRIVE] {self.drive_duration}s, speed={self.drive_speed}")
        self.get_logger().info(f"[STOP_BEFORE_PARK] {self.prestop_duration}s, brake={self.stop_brake}")
        self.get_logger().info(f"[STEER] {self.steer_duration}s, angle={self.steer_angle}, speed={self.forward_speed}")
        self.get_logger().info(f"[FORWARD] {self.forward_duration}s, speed={self.forward_speed}")
        self.get_logger().info(f"[STOP] {self.stop_duration}s, brake={self.stop_brake}")
        self.get_logger().info(f"[REVERSE] {self.reverse_duration}s, speed={self.reverse_speed}")
        self.get_logger().info(f"[REVERSE_STEER] {self.reverse_steer_duration}s, angle={self.reverse_steer_angle}, speed={self.reverse_speed}")
        self.get_logger().info("===========================")

    def main_loop(self):
        """메인 FSM 루프"""
        elapsed = time.time() - self.state_start_time

        if self.current_state == ParkingState.DRIVE:
            self._handle_drive(elapsed)
        elif self.current_state == ParkingState.STOP_BEFORE_PARK:
            self._handle_stop_before_park(elapsed)
        elif self.current_state == ParkingState.STEER:
            self._handle_steer(elapsed)
        elif self.current_state == ParkingState.FORWARD:
            self._handle_forward(elapsed)
        elif self.current_state == ParkingState.STOP:
            self._handle_stop(elapsed)
        elif self.current_state == ParkingState.REVERSE:
            self._handle_reverse(elapsed)
        elif self.current_state == ParkingState.REVERSE_STEER:
            self._handle_reverse_steer(elapsed)
        elif self.current_state == ParkingState.COMPLETED:
            self._handle_completed()

    # -------------------------------
    # [1단계] 일정 시간 직진 주행
    # -------------------------------
    def _handle_drive(self, elapsed: float):
        if elapsed < self.drive_duration:
            self._publish_cmd(self.FORWARD_GEAR, self.drive_speed, 0, 0)
            self._log_progress("DRIVE", elapsed, self.drive_duration)
        else:
            self._transition_to_state(ParkingState.STOP_BEFORE_PARK)

    # -------------------------------
    # [2단계] 주행 후 정지
    # -------------------------------
    def _handle_stop_before_park(self, elapsed: float):
        if elapsed < self.prestop_duration:
            self._publish_stop_cmd()
            self._log_progress("STOP_BEFORE_PARK", elapsed, self.prestop_duration)
        else:
            self._transition_to_state(ParkingState.STEER)

    # -------------------------------
    # [3단계] 주차 시퀀스 (기존과 동일)
    # -------------------------------
    def _handle_steer(self, elapsed: float):
        if elapsed < self.steer_duration:
            self._publish_steer_cmd()
            self._log_progress("STEER", elapsed, self.steer_duration)
        else:
            self._transition_to_state(ParkingState.FORWARD)

    def _handle_forward(self, elapsed: float):
        if elapsed < self.forward_duration:
            self._publish_forward_cmd()
            self._log_progress("FORWARD", elapsed, self.forward_duration)
        else:
            self._transition_to_state(ParkingState.STOP)

    def _handle_stop(self, elapsed: float):
        if elapsed < self.stop_duration:
            self._publish_stop_cmd()
            self._log_progress("STOP", elapsed, self.stop_duration)
        else:
            self._transition_to_state(ParkingState.REVERSE)

    def _handle_reverse(self, elapsed: float):
        if elapsed < self.reverse_duration:
            self._publish_reverse_cmd()
            self._log_progress("REVERSE", elapsed, self.reverse_duration)
        else:
            self._transition_to_state(ParkingState.REVERSE_STEER)

    def _handle_reverse_steer(self, elapsed: float):
        if elapsed < self.reverse_steer_duration:
            self._publish_reverse_steer_cmd()
            self._log_progress("REVERSE_STEER", elapsed, self.reverse_steer_duration)
        else:
            self._transition_to_state(ParkingState.COMPLETED)

    def _handle_completed(self):
        self._publish_stop_cmd()

    # -------------------------------
    # 상태 전환 및 메시지 발행
    # -------------------------------
    def _transition_to_state(self, new_state: ParkingState):
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()

        self._publish_state()
        self.get_logger().info(f"🔄 {old_state.value} → {new_state.value}")

        if new_state == ParkingState.COMPLETED:
            self.get_logger().info("✅ Parking sequence completed!")

    def _publish_cmd(self, gear: int, speed: int, steer: int, brake: int):
        cmd = ErpCmdMsg()
        cmd.gear = gear
        cmd.speed = speed
        cmd.steer = steer
        cmd.brake = brake
        self.cmd_pub.publish(cmd)

    def _publish_steer_cmd(self):
        self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, self.steer_angle, 0)

    def _publish_forward_cmd(self):
        self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, 0, 0)

    def _publish_stop_cmd(self):
        self._publish_cmd(self.FORWARD_GEAR, 0, 0, self.stop_brake)

    def _publish_reverse_cmd(self):
        self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, 0, 0)

    def _publish_reverse_steer_cmd(self):
        self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, self.reverse_steer_angle, 0)

    def _publish_state(self):
        msg = String()
        msg.data = self.current_state.value
        self.state_pub.publish(msg)

    def _log_progress(self, state_name: str, elapsed: float, total: float):
        progress = (elapsed / total) * 100
        if int(elapsed) != int(elapsed - 0.05):
            self.get_logger().info(f"📍 {state_name}: {elapsed:.1f}/{total:.1f}s ({progress:.0f}%)")


def main(args=None):
    rclpy.init(args=args)
    try:
        node = ParkingSequenceNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n🛑 Parking sequence stopped by user")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
