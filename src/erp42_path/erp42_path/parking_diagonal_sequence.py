#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from typing import Optional
from enum import Enum

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from interfaces_control_pkg.msg import ErpCmdMsg


class ParkingState(Enum):
    """주차 상태 정의"""
    STEER = "steer"
    FORWARD = "forward"
    STOP = "stop"
    REVERSE = "reverse"
    COMPLETED = "completed"
    REVERSE_STEER = "reverse_steer"


class ParkingSequenceNode(Node):
    """주차 시퀀스 전용 노드 - 스티어 → 전진 → 정지 → 후진"""

    def __init__(self):
        super().__init__('parking_diagonal_sequence')

        # === 파라미터 (코드에서 직접 수정) ===
        # 시간 설정 (초)
        self.steer_duration = 4.0      # 조향 시간
        self.reverse_steer_duration = 1.5      # 조향 시간
        self.forward_duration = 2.5    # 전진 시간
        self.stop_duration = 3.0       # 정지 시간
        self.reverse_duration = 3.0    # 후진 시간
        
        # 조향 설정
        self.steer_angle = 2000        # 조향각 (좌측)
        self.reverse_steer_angle = 0   # 후진 시 조향각
        
        # 속도 설정
        self.forward_speed = 100        # 전진 속도
        self.reverse_speed = 100        # 후진 속도
        
        # 브레이크 설정
        self.stop_brake = 33          # 정지 시 브레이크
        
        # === 내부 변수 ===
        self.current_state = ParkingState.STEER  # 바로 시작
        self.state_start_time = time.time()      # 현재 시간으로 시작
        
        # 기어 상수
        self.FORWARD_GEAR = 0
        self.REVERSE_GEAR = 2

        # ROS Publishers
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
        self.state_pub = self.create_publisher(String, '/parking_state', 10)

        # 메인 타이머 (20Hz)
        self.timer = self.create_timer(0.05, self.main_loop)

        self.get_logger().info("🅿️ Diagonal Parking sequence started!")
        self._log_parameters()

    def _log_parameters(self):
        """현재 파라미터 출력"""
        self.get_logger().info("=== Diagonal Parking Parameters ===")
        self.get_logger().info(f"0. STOP     : {self.stop_duration}s, brake={self.stop_brake}")
        self.get_logger().info(f"1. STEER    : {self.steer_duration}s, angle={self.steer_angle}, speed={self.forward_speed}")
        self.get_logger().info(f"2. FORWARD  : {self.forward_duration}s, speed={self.forward_speed}")
        self.get_logger().info(f"3. STOP     : {self.stop_duration}s, brake={self.stop_brake}")
        self.get_logger().info(f"4. REVERSE  : {self.reverse_duration}s, speed={self.reverse_speed}, steer={self.reverse_steer_angle}")
        self.get_logger().info(f"4. REVERSE_STEER  : {self.reverse_steer_duration}s, speed={self.reverse_speed}, steer={self.steer_angle}")
        self.get_logger().info("===========================")

    def main_loop(self):
        """메인 FSM 루프"""
        elapsed = time.time() - self.state_start_time
        
        if self.current_state == ParkingState.STEER:
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
            self._transition_to_state(ParkingState.STOP)

    def _handle_stop(self, elapsed: float):
        """정지 상태"""
        if elapsed < self.stop_duration:
            self._publish_stop_cmd()
            self._log_progress("STOP", elapsed, self.stop_duration)
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
        """완료 상태 - 정지 유지"""
        self._publish_stop_cmd()

    def _transition_to_state(self, new_state: ParkingState):
        """상태 전이"""
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        # 상태 발행
        self._publish_state()

        self.get_logger().info(f"🔄 {old_state.value} → {new_state.value}")
        
        if new_state == ParkingState.COMPLETED:
            self.get_logger().info("✅ Parking sequence completed!")

    def _publish_cmd(self, gear: int, speed: int, steer: int, brake: int):
        """명령 발행"""
        cmd = ErpCmdMsg()
        cmd.gear = gear
        cmd.speed = speed
        cmd.steer = steer
        cmd.brake = brake
        self.cmd_pub.publish(cmd)

    def _publish_steer_cmd(self):
        """조향 명령 (조향하면서 전진)"""
        self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, self.steer_angle, 0)

    def _publish_forward_cmd(self):
        """전진 명령 (직진)"""
        self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, 0, 0)

    def _publish_stop_cmd(self):
        """정지 명령"""
        self._publish_cmd(self.FORWARD_GEAR, 0, 0, self.stop_brake)

    def _publish_reverse_cmd(self):
        """후진 명령"""
        self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, 0, 0)

    def _publish_reverse_steer_cmd(self):
        """후진 조향 명령"""
        self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, self.steer_angle, 0)

    def _publish_state(self):
        """현재 상태 발행"""
        msg = String()
        msg.data = self.current_state.value
        self.state_pub.publish(msg)

    def _log_progress(self, state_name: str, elapsed: float, total: float):
        """진행률 로깅 (1초마다)"""
        progress = (elapsed / total) * 100
        if int(elapsed) != int(elapsed - 0.05):  # 1초마다 출력
            self.get_logger().info(f"📍 {state_name}: {elapsed:.1f}/{total:.1f}s ({progress:.0f}%)")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = ParkingSequenceNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n🛑 Parking sequence stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()