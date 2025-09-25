#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from typing import Optional
from enum import Enum

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from interfaces_control_pkg.msg import ErpCmdMsg


class ParallelParkingState(Enum):
    """평행주차 상태 정의"""
    # parking
    REVERSE_RIGHT = "reverse_right"          # 오른쪽 스티어 최대 후진
    REVERSE_STRAIGHT = "reverse_straight"    # 스티어 정렬 후진
    REVERSE_LEFT = "reverse_left"            # 왼쪽 스티어 최대 후진
    STOP_1 = "stop_1"                        # 첫 번째 정지
    FORWARD_RIGHT = "forward_right"          # 오른쪽 스티어 최대 전진
    STOP_2 = "stop_2"                        # 두 번째 정지  (parking complete and 바로 복귀 방지)
    #  parking out
    FORWARD_LEFT = "forward_left"            # 왼쪽 스티어 최대 전진
    FORWARD_STRAIGHT = "forward_straight"    # 스티어 정렬 전진
    FORWARD_RIGHT_FINAL = "forward_right_final"  # 오른쪽 스티어 전진 (마지막)
    COMPLETED = "completed"                  # 완료


class ParallelParkingNode(Node):
    """평행주차 시퀀스 전용 노드"""

    def __init__(self):
        super().__init__('parking_parallel_sequence')

        # === 파라미터 (코드에서 직접 수정) ===
        # 시간 설정 (초) - 모든 단계가 3초씩 (정지는 예외)
        self.reverse_right_duration = 5.0      # 오른쪽 스티어 후진
        self.reverse_straight_duration = 5.0   # 직진 후진
        self.reverse_left_duration = 5.0       # 왼쪽 스티어 후진
        self.stop_1_duration = 3.0             # 첫 번째 정지
        self.forward_right_duration = 3.0      # 오른쪽 스티어 전진
        self.stop_2_duration = 5.0             # 두 번째 정지 (5초) parking comeplete and 바로 복귀 방지
        self.forward_left_duration = 5.0       # 왼쪽 스티어 전진 parking out
        self.forward_straight_duration = 5.0   # 직진 전진
        self.forward_right_final_duration = 3.0 # 마지막 오른쪽 스티어 전진
        
        # 조향 설정
        self.max_steer_right = 2000    # 오른쪽 최대 조향각
        self.max_steer_left = -2000    # 왼쪽 최대 조향각
        self.steer_straight = 0        # 직진 조향각
        
        # 속도 설정
        self.forward_speed = 30        # 전진 속도
        self.reverse_speed = 30        # 후진 속도
        
        # 브레이크 설정
        self.stop_brake = 200          # 정지 시 브레이크
        
        # === 내부 변수 ===
        self.current_state = ParallelParkingState.REVERSE_RIGHT  # 바로 시작
        self.state_start_time = time.time()                     # 현재 시간으로 시작
        
        # 기어 상수
        self.FORWARD_GEAR = 0
        self.REVERSE_GEAR = 2

        # ROS Publishers
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
        self.state_pub = self.create_publisher(String, '/parallel_parking_state', 10)

        # 메인 타이머 (20Hz)
        self.timer = self.create_timer(0.05, self.main_loop)

        self.get_logger().info("🅿️ Parallel Parking sequence started!")
        self._log_parameters()

    def _log_parameters(self):
        """현재 파라미터 출력"""
        self.get_logger().info("=== Parallel Parking Parameters ===")
        self.get_logger().info(f"1. REVERSE_RIGHT    : {self.reverse_right_duration}s, steer={self.max_steer_right}, speed={self.reverse_speed}")
        self.get_logger().info(f"2. REVERSE_STRAIGHT : {self.reverse_straight_duration}s, steer={self.steer_straight}, speed={self.reverse_speed}")
        self.get_logger().info(f"3. REVERSE_LEFT     : {self.reverse_left_duration}s, steer={self.max_steer_left}, speed={self.reverse_speed}")
        self.get_logger().info(f"4. STOP_1           : {self.stop_1_duration}s, brake={self.stop_brake}")
        self.get_logger().info(f"5. FORWARD_RIGHT    : {self.forward_right_duration}s, steer={self.max_steer_right}, speed={self.forward_speed}")
        self.get_logger().info(f"6. STOP_2           : {self.stop_2_duration}s, brake={self.stop_brake}")
        self.get_logger().info(f"7. FORWARD_LEFT     : {self.forward_left_duration}s, steer={self.max_steer_left}, speed={self.forward_speed}")
        self.get_logger().info(f"8. FORWARD_STRAIGHT : {self.forward_straight_duration}s, steer={self.steer_straight}, speed={self.forward_speed}")
        self.get_logger().info(f"9. FORWARD_RIGHT_FINAL: {self.forward_right_final_duration}s, steer={self.max_steer_right}, speed={self.forward_speed}")
        self.get_logger().info("=====================================")

    def main_loop(self):
        """메인 FSM 루프"""
        elapsed = time.time() - self.state_start_time
        
        if self.current_state == ParallelParkingState.REVERSE_RIGHT:
            self._handle_reverse_right(elapsed)
        elif self.current_state == ParallelParkingState.REVERSE_STRAIGHT:
            self._handle_reverse_straight(elapsed)
        elif self.current_state == ParallelParkingState.REVERSE_LEFT:
            self._handle_reverse_left(elapsed)
        elif self.current_state == ParallelParkingState.STOP_1:
            self._handle_stop_1(elapsed)
        elif self.current_state == ParallelParkingState.FORWARD_RIGHT:
            self._handle_forward_right(elapsed)
        elif self.current_state == ParallelParkingState.STOP_2:
            self._handle_stop_2(elapsed)
        elif self.current_state == ParallelParkingState.FORWARD_LEFT:
            self._handle_forward_left(elapsed)
        elif self.current_state == ParallelParkingState.FORWARD_STRAIGHT:
            self._handle_forward_straight(elapsed)
        elif self.current_state == ParallelParkingState.FORWARD_RIGHT_FINAL:
            self._handle_forward_right_final(elapsed)
        elif self.current_state == ParallelParkingState.COMPLETED:
            self._handle_completed()

    # === 상태별 핸들러 ===
    def _handle_reverse_right(self, elapsed: float):
        """오른쪽 스티어 최대 후진"""
        if elapsed < self.reverse_right_duration:
            self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, self.max_steer_right, 0)
            self._log_progress("REVERSE_RIGHT", elapsed, self.reverse_right_duration)
        else:
            self._transition_to_state(ParallelParkingState.REVERSE_STRAIGHT)

    def _handle_reverse_straight(self, elapsed: float):
        """스티어 정렬 후진"""
        if elapsed < self.reverse_straight_duration:
            self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, self.steer_straight, 0)
            self._log_progress("REVERSE_STRAIGHT", elapsed, self.reverse_straight_duration)
        else:
            self._transition_to_state(ParallelParkingState.REVERSE_LEFT)

    def _handle_reverse_left(self, elapsed: float):
        """왼쪽 스티어 최대 후진"""
        if elapsed < self.reverse_left_duration:
            self._publish_cmd(self.REVERSE_GEAR, self.reverse_speed, self.max_steer_left, 0)
            self._log_progress("REVERSE_LEFT", elapsed, self.reverse_left_duration)
        else:
            self._transition_to_state(ParallelParkingState.STOP_1)

    def _handle_stop_1(self, elapsed: float):
        """첫 번째 정지"""
        if elapsed < self.stop_1_duration:
            self._publish_cmd(self.FORWARD_GEAR, 0, 0, self.stop_brake)
            self._log_progress("STOP_1", elapsed, self.stop_1_duration)
        else:
            self._transition_to_state(ParallelParkingState.FORWARD_RIGHT)

    def _handle_forward_right(self, elapsed: float):
        """오른쪽 스티어 최대 전진"""
        if elapsed < self.forward_right_duration:
            self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, self.max_steer_right, 0)
            self._log_progress("FORWARD_RIGHT", elapsed, self.forward_right_duration)
        else:
            self._transition_to_state(ParallelParkingState.STOP_2)

    def _handle_stop_2(self, elapsed: float):
        """두 번째 정지 (5초)"""
        if elapsed < self.stop_2_duration:
            self._publish_cmd(self.FORWARD_GEAR, 0, 0, self.stop_brake)
            self._log_progress("STOP_2", elapsed, self.stop_2_duration)
        else:
            self._transition_to_state(ParallelParkingState.FORWARD_LEFT)

    def _handle_forward_left(self, elapsed: float):
        """왼쪽 스티어 최대 전진"""
        if elapsed < self.forward_left_duration:
            self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, self.max_steer_left, 0)
            self._log_progress("FORWARD_LEFT", elapsed, self.forward_left_duration)
        else:
            self._transition_to_state(ParallelParkingState.FORWARD_STRAIGHT)

    def _handle_forward_straight(self, elapsed: float):
        """스티어 정렬 전진"""
        if elapsed < self.forward_straight_duration:
            self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, self.steer_straight, 0)
            self._log_progress("FORWARD_STRAIGHT", elapsed, self.forward_straight_duration)
        else:
            self._transition_to_state(ParallelParkingState.FORWARD_RIGHT_FINAL)

    def _handle_forward_right_final(self, elapsed: float):
        """마지막 오른쪽 스티어 전진"""
        if elapsed < self.forward_right_final_duration:
            self._publish_cmd(self.FORWARD_GEAR, self.forward_speed, self.max_steer_right, 0)
            self._log_progress("FORWARD_RIGHT_FINAL", elapsed, self.forward_right_final_duration)
        else:
            self._transition_to_state(ParallelParkingState.COMPLETED)

    def _handle_completed(self):
        """완료 상태 - 정지 유지"""
        self._publish_cmd(self.FORWARD_GEAR, 0, 0, self.stop_brake)

    def _transition_to_state(self, new_state: ParallelParkingState):
        """상태 전이"""
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        # 상태 발행
        self._publish_state()

        self.get_logger().info(f"🔄 {old_state.value} → {new_state.value}")
        
        if new_state == ParallelParkingState.COMPLETED:
            self.get_logger().info("✅ Parallel parking sequence completed!")

    def _publish_cmd(self, gear: int, speed: int, steer: int, brake: int):
        """명령 발행"""
        cmd = ErpCmdMsg()
        cmd.gear = gear
        cmd.speed = speed
        cmd.steer = steer
        cmd.brake = brake
        self.cmd_pub.publish(cmd)

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
        node = ParallelParkingNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n🛑 Parallel parking sequence stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()