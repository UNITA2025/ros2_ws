#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import numpy as np
from enum import Enum
from typing import List, Optional, Tuple
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from std_msgs.msg import String, Bool
from sensor_msgs.msg import LaserScan

class PathSource(Enum):
    """경로 소스 타입"""
    GLOBAL_PATH = "global_path"      # 전체 맵 경로
    LOCAL_PATH = "local_path"        # 지역 주행 경로  
    PARKING_PATH = "parking_path"    # 주차 경로
    EMERGENCY_PATH = "emergency_path" # 긴급 경로

class TriggerCondition(Enum):
    """전환 트리거 조건"""
    PROXIMITY_TO_DESTINATION = "near_destination"     # 목적지 근접
    PARKING_SPACE_DETECTED = "parking_detected"       # 주차칸 감지
    USER_COMMAND = "user_command"                      # 사용자 명령
    AUTONOMOUS_DECISION = "autonomous_decision"        # 자율 판단

class PathSwitchingManager(Node):
    """경로 자동 전환 관리 시스템"""
    
    def __init__(self):
        super().__init__('path_switching_manager')
        
        # 상태 변수
        self.current_path_source = PathSource.LOCAL_PATH
        self.available_paths = {}
        self.destination_point: Optional[Point] = None
        self.detected_parking_spaces = []
        self.current_position: Optional[Point] = None
        
        # 전환 조건 파라미터
        self.destination_proximity_threshold = 5.0  # 목적지 5m 이내
        self.parking_detection_threshold = 3.0      # 주차칸 3m 이내
        self.path_switch_cooldown = 5.0             # 전환 후 5초 대기
        self.last_switch_time = 0.0
        
        # ROS 인터페이스 설정
        self._setup_ros_interfaces()
        
        # 메인 루프
        self.main_timer = self.create_timer(0.2, self.path_switching_loop)  # 5Hz
        
        self.get_logger().info("Path Switching Manager initialized")
    
    def _setup_ros_interfaces(self):
        """ROS 인터페이스 설정"""
        # 경로 구독자들
        self.create_subscription(Path, '/local_path', self.local_path_callback, 10)
        self.create_subscription(Path, '/parking_path', self.parking_path_callback, 10)
        self.create_subscription(Path, '/global_path', self.global_path_callback, 10)
        
        # 센서 데이터
        self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        
        # 명령 및 상태
        self.create_subscription(Point, '/destination', self.destination_callback, 10)
        self.create_subscription(PoseStamped, '/current_pose', self.pose_callback, 10)
        self.create_subscription(String, '/parking_command', self.parking_command_callback, 10)
        
        # 출력 퍼블리셔
        self.active_path_pub = self.create_publisher(Path, '/active_path', 10)
        self.path_source_pub = self.create_publisher(String, '/current_path_source', 10)
        self.switch_status_pub = self.create_publisher(String, '/path_switch_status', 10)
    
    def local_path_callback(self, msg: Path):
        """지역 경로 업데이트"""
        self.available_paths[PathSource.LOCAL_PATH] = msg
        self.get_logger().debug("Local path updated")
    
    def parking_path_callback(self, msg: Path):
        """주차 경로 업데이트"""
        self.available_paths[PathSource.PARKING_PATH] = msg
        self.get_logger().info("Parking path received - new parking opportunity detected")
        
        # 주차 경로가 새로 생성되면 자동 전환 고려
        if self._should_switch_to_parking():
            self._switch_to_path(PathSource.PARKING_PATH, TriggerCondition.PARKING_SPACE_DETECTED)
    
    def global_path_callback(self, msg: Path):
        """전체 경로 업데이트"""
        self.available_paths[PathSource.GLOBAL_PATH] = msg
        self.get_logger().debug("Global path updated")
    
    def destination_callback(self, msg: Point):
        """목적지 설정"""
        self.destination_point = msg
        self.get_logger().info(f"Destination set: ({msg.x:.2f}, {msg.y:.2f})")
    
    def pose_callback(self, msg: PoseStamped):
        """현재 위치 업데이트"""
        self.current_position = msg.pose.position
    
    def parking_command_callback(self, msg: String):
        """주차 명령 처리"""
        if msg.data == "start_parking":
            if PathSource.PARKING_PATH in self.available_paths:
                self._switch_to_path(PathSource.PARKING_PATH, TriggerCondition.USER_COMMAND)
            else:
                self.get_logger().warn("Parking command received but no parking path available")
        
        elif msg.data == "cancel_parking":
            if self.current_path_source == PathSource.PARKING_PATH:
                self._switch_to_path(PathSource.LOCAL_PATH, TriggerCondition.USER_COMMAND)
    
    def lidar_callback(self, msg: LaserScan):
        """라이다 데이터로 주차 공간 감지"""
        detected_spaces = self._detect_parking_spaces_from_lidar(msg)
        self.detected_parking_spaces = detected_spaces
        
        # 새로운 주차 공간 감지시 주차 경로 요청
        if detected_spaces and self.current_path_source == PathSource.LOCAL_PATH:
            self._request_parking_path_generation(detected_spaces[0])
    
    def path_switching_loop(self):
        """경로 전환 메인 루프"""
        try:
            # 쿨다운 체크
            current_time = self.get_clock().now().nanoseconds / 1e9
            if current_time - self.last_switch_time < self.path_switch_cooldown:
                return
            
            # 전환 조건 확인
            switch_decision = self._evaluate_switching_conditions()
            
            if switch_decision:
                target_source, trigger = switch_decision
                self._switch_to_path(target_source, trigger)
            
            # 현재 활성 경로 발행
            self._publish_active_path()
            self._publish_status()
            
        except Exception as e:
            self.get_logger().error(f"Path switching loop error: {e}")
    
    def _evaluate_switching_conditions(self) -> Optional[Tuple[PathSource, TriggerCondition]]:
        """전환 조건 평가"""
        if not self.current_position:
            return None
        
        # 1. 목적지 근접 확인
        if self.destination_point:
            distance_to_dest = math.hypot(
                self.current_position.x - self.destination_point.x,
                self.current_position.y - self.destination_point.y
            )
            
            # 목적지 근처에서 주차 경로로 전환
            if (distance_to_dest < self.destination_proximity_threshold and 
                self.current_path_source == PathSource.LOCAL_PATH and
                PathSource.PARKING_PATH in self.available_paths):
                
                return (PathSource.PARKING_PATH, TriggerCondition.PROXIMITY_TO_DESTINATION)
        
        # 2. 주차 공간 감지 확인
        if (self.detected_parking_spaces and 
            self.current_path_source == PathSource.LOCAL_PATH and
            PathSource.PARKING_PATH in self.available_paths):
            
            # 감지된 주차 공간 근처인지 확인
            for space in self.detected_parking_spaces:
                distance = math.hypot(
                    self.current_position.x - space.x,
                    self.current_position.y - space.y
                )
                
                if distance < self.parking_detection_threshold:
                    return (PathSource.PARKING_PATH, TriggerCondition.PARKING_SPACE_DETECTED)
        
        # 3. 주차 완료 후 복귀
        if (self.current_path_source == PathSource.PARKING_PATH and 
            self._is_parking_completed()):
            
            return (PathSource.LOCAL_PATH, TriggerCondition.AUTONOMOUS_DECISION)
        
        # 4. 주차 경로 실패시 복귀
        if (self.current_path_source == PathSource.PARKING_PATH and 
            self._is_parking_failed()):
            
            return (PathSource.LOCAL_PATH, TriggerCondition.AUTONOMOUS_DECISION)
        
        return None
    
    def _should_switch_to_parking(self) -> bool:
        """주차 경로로 전환해야 하는지 판단"""
        # 현재 로컬 경로 사용 중이고, 현재 위치가 적절한지 확인
        if (self.current_path_source != PathSource.LOCAL_PATH or 
            not self.current_position):
            return False
        
        # 주차 경로의 시작점이 현재 위치와 가까운지 확인
        parking_path = self.available_paths.get(PathSource.PARKING_PATH)
        if not parking_path or not parking_path.poses:
            return False
        
        start_point = parking_path.poses[0].pose.position
        distance_to_start = math.hypot(
            self.current_position.x - start_point.x,
            self.current_position.y - start_point.y
        )
        
        return distance_to_start < 2.0  # 시작점 2m 이내
    
    def _switch_to_path(self, target_source: PathSource, trigger: TriggerCondition):
        """경로 전환 실행"""
        if target_source not in self.available_paths:
            self.get_logger().warn(f"Cannot switch to {target_source.value} - path not available")
            return
        
        old_source = self.current_path_source
        self.current_path_source = target_source
        self.last_switch_time = self.get_clock().now().nanoseconds / 1e9
        
        self.get_logger().info(
            f"Path switched: {old_source.value} → {target_source.value} "
            f"(trigger: {trigger.value})"
        )
        
        # 전환 상태 발행
        switch_msg = String()
        switch_msg.data = f"switched_to_{target_source.value}_by_{trigger.value}"
        self.switch_status_pub.publish(switch_msg)
    
    def _publish_active_path(self):
        """현재 활성 경로 발행"""
        if self.current_path_source in self.available_paths:
            active_path = self.available_paths[self.current_path_source]
            
            # 경로에 메타데이터 추가
            active_path.header.frame_id = f"active_{self.current_path_source.value}"
            active_path.header.stamp = self.get_clock().now().to_msg()
            
            self.active_path_pub.publish(active_path)
    
    def _publish_status(self):
        """현재 상태 발행"""
        status_msg = String()
        status_msg.data = self.current_path_source.value
        self.path_source_pub.publish(status_msg)
    
    def _detect_parking_spaces_from_lidar(self, scan: LaserScan) -> List[Point]:
        """라이다로 주차 공간 감지 (간단한 버전)"""
        spaces = []
        
        ranges = np.array(scan.ranges)
        angles = np.linspace(scan.angle_min, scan.angle_max, len(ranges))
        
        # 유효한 거리 데이터
        valid_mask = (ranges > scan.range_min) & (ranges < scan.range_max) & (ranges < 10.0)
        if not np.any(valid_mask):
            return spaces
        
        valid_ranges = ranges[valid_mask]
        valid_angles = angles[valid_mask]
        
        # 거리 차이로 빈 공간 찾기
        range_diff = np.diff(valid_ranges)
        gap_indices = np.where(np.abs(range_diff) > 1.5)[0]  # 1.5m 이상 차이
        
        for i in range(len(gap_indices) - 1):
            start_idx = gap_indices[i]
            end_idx = gap_indices[i + 1]
            
            if end_idx - start_idx < 5:  # 너무 작은 간격 무시
                continue
            
            # 빈 공간의 중심점 계산
            center_idx = (start_idx + end_idx) // 2
            center_range = valid_ranges[center_idx]
            center_angle = valid_angles[center_idx]
            
            # 공간 크기 확인
            gap_width = center_range * abs(valid_angles[end_idx] - valid_angles[start_idx])
            
            if gap_width > 2.5:  # 최소 2.5m 폭
                space = Point()
                space.x = center_range * np.cos(center_angle)
                space.y = center_range * np.sin(center_angle)
                space.z = gap_width  # 폭 정보 저장
                spaces.append(space)
        
        return spaces
    
    def _request_parking_path_generation(self, target_space: Point):
        """주차 경로 생성 요청"""
        # 실제 구현에서는 path planner에게 주차 경로 생성 요청
        self.get_logger().info(
            f"Requesting parking path generation for space at "
            f"({target_space.x:.2f}, {target_space.y:.2f})"
        )
        
        # 예시: 주차 경로 생성 서비스 호출
        # self.parking_planner_client.call_async(target_space)
    
    def _is_parking_completed(self) -> bool:
        """주차 완료 여부 확인"""
        if not self.current_position or self.current_path_source != PathSource.PARKING_PATH:
            return False
        
        parking_path = self.available_paths.get(PathSource.PARKING_PATH)
        if not parking_path or not parking_path.poses:
            return False
        
        # 주차 경로의 마지막 지점과 현재 위치 비교
        end_point = parking_path.poses[-1].pose.position
        distance_to_end = math.hypot(
            self.current_position.x - end_point.x,
            self.current_position.y - end_point.y
        )
        
        return distance_to_end < 0.5  # 50cm 이내 도착
    
    def _is_parking_failed(self) -> bool:
        """주차 실패 여부 확인"""
        # 간단한 실패 조건: 주차 경로가 너무 오래 지속됨
        if self.current_path_source != PathSource.PARKING_PATH:
            return False
        
        # 실제로는 더 복잡한 실패 조건 필요:
        # - 장애물로 인한 경로 차단
        # - 제한 시간 초과
        # - 센서 오류 등
        
        return False

# 사용 예시 및 테스트
class PathSwitchingTester:
    """경로 전환 시스템 테스트"""
    
    def __init__(self):
        self.switch_manager = PathSwitchingManager()
    
    def simulate_scenario_1(self):
        """시나리오 1: 목적지 접근 → 자동 주차 전환"""
        print("=== 시나리오 1: 목적지 접근 시 주차 전환 ===")
        
        # 1. 목적지 설정
        destination = Point(x=10.0, y=5.0, z=0.0)
        # self.switch_manager.destination_callback(destination)
        
        # 2. 목적지 근처로 이동 (시뮬레이션)
        current_pose = PoseStamped()
        current_pose.pose.position = Point(x=9.0, y=5.2, z=0.0)
        # self.switch_manager.pose_callback(current_pose)
        
        # 3. 주차 경로 수신 (시뮬레이션)
        parking_path = Path()
        # ... 주차 경로 설정 ...
        # self.switch_manager.parking_path_callback(parking_path)
        
        print("→ 목적지 5m 이내 접근시 자동으로 주차 경로로 전환됨")
    
    def simulate_scenario_2(self):
        """시나리오 2: 주차 공간 발견 → 즉시 전환"""
        print("=== 시나리오 2: 주차 공간 발견 시 즉시 전환 ===")
        
        # 라이다 데이터로 주차 공간 감지 시뮬레이션
        # → 자동으로 주차 경로 생성 요청
        # → 생성된 주차 경로로 즉시 전환
        
        print("→ 라이다로 주차 공간 감지시 즉시 주차 모드로 전환됨")

def main(args=None):
    """메인 함수"""
    rclpy.init(args=args)
    
    try:
        path_manager = PathSwitchingManager()
        rclpy.spin(path_manager)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Path switching manager failed: {e}")
    finally:
        if 'path_manager' in locals():
            path_manager.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()