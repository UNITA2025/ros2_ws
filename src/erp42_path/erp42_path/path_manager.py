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


class PathManager(Node):
    """위치 기반 자동 경로 전환 관리자"""
    
    def __init__(self):
        super().__init__('path_manager')
        
        # 상태 변수
        self.current_mode = "normal"
        self.current_position: Optional[Point] = None
        self.global_path: Optional[Path] = None
        self.parking_path: Optional[Path] = None
        
        # 파라미터 선언 및 로드
        self.declare_parameter('parking_proximity_threshold', 3.0)  # 주차 경로 접근 거리
        self.declare_parameter('parking_complete_threshold', 1.0)   # 주차 완료 거리  
        self.declare_parameter('mode_check_rate', 5.0)              # 모드 체크 주기 (Hz)
        self.declare_parameter('enable_debug_logging', True)        # 디버그 로깅
        
        self._load_parameters()
        
        # ROS 인터페이스 설정
        self._setup_ros_interfaces()
        
        # 메인 타이머
        check_period = 1.0 / self.mode_check_rate
        self.main_timer = self.create_timer(check_period, self.main_loop)
        
        self.get_logger().info(
            f"Path Manager initialized - "
            f"Parking threshold: {self.parking_threshold}m, "
            f"Check rate: {self.mode_check_rate}Hz"
        )
    
    def _load_parameters(self):
        """파라미터 로드"""
        self.parking_threshold = self.get_parameter('parking_proximity_threshold').value
        self.parking_complete_threshold = self.get_parameter('parking_complete_threshold').value
        self.mode_check_rate = self.get_parameter('mode_check_rate').value
        self.debug_logging = self.get_parameter('enable_debug_logging').value
    
    def _setup_ros_interfaces(self):
        """ROS 인터페이스 설정"""
        # === 구독자 ===
        # 위치 정보
        self.create_subscription(
            Odometry, 
            '/odometry/local_enu', 
            self.odometry_callback, 
            10
        )
        
        # 경로 정보
        self.create_subscription(
            Path, 
            '/global_path', 
            self.global_path_callback, 
            10
        )
        
        self.create_subscription(
            Path, 
            '/parking_path', 
            self.parking_path_callback, 
            10
        )
        
        # === 발행자 ===
        # 활성 경로
        self.active_path_pub = self.create_publisher(Path, '/active_path', 10)
        
        # 컨트롤러 모드
        self.controller_mode_pub = self.create_publisher(String, '/controller_mode', 10)
        
        # 상태 정보
        self.system_status_pub = self.create_publisher(String, '/path_manager_status', 10)
    
    # ================ 콜백 함수들 ================
    
    def odometry_callback(self, msg: Odometry):
        """오도메트리 정보 업데이트"""
        self.current_position = msg.pose.pose.position
        
        if self.debug_logging:
            self.get_logger().debug(
                f"Position updated: ({self.current_position.x:.2f}, "
                f"{self.current_position.y:.2f})"
            )
    
    def global_path_callback(self, msg: Path):
        """글로벌 경로 수신"""
        self.global_path = msg
        self.get_logger().info(f"Global path received: {len(msg.poses)} points")
        
        # 현재 일반 모드면 즉시 발행
        if self.current_mode == "normal":
            self._publish_active_path()
    
    def parking_path_callback(self, msg: Path):
        """주차 경로 수신"""
        self.parking_path = msg
        self.get_logger().info(f"Parking path received: {len(msg.poses)} points")
        
        # 현재 주차 모드면 즉시 발행
        if self.current_mode == "parking":
            self._publish_active_path()
    
    # ================ 메인 로직 ================
    
    def main_loop(self):
        """메인 제어 루프"""
        try:
            # 위치 정보가 없으면 대기
            if not self.current_position:
                return
            
            # 모드 전환 조건 체크
            self._check_mode_transitions()
            
            # 활성 경로 발행
            self._publish_active_path()
            
            # 상태 발행
            self._publish_status()
            
        except Exception as e:
            self.get_logger().error(f"Main loop error: {e}")
    
    def _check_mode_transitions(self):
        """모드 전환 조건 체크"""
        current_mode = self.current_mode
        
        if self.current_mode == "normal":
            # 일반 모드 → 주차 모드 전환 체크
            if self._should_switch_to_parking():
                self._change_mode_to("parking")
        
        elif self.current_mode == "parking":
            # 주차 모드 → 일반 모드 전환 체크
            if self._should_switch_to_normal():
                self._change_mode_to("normal")
        
        # 모드 변경 로깅
        if current_mode != self.current_mode:
            self.get_logger().info(f"Mode transition: {current_mode} → {self.current_mode}")
    
    def _should_switch_to_parking(self) -> bool:
        """주차 모드로 전환해야 하는지 판단"""
        # 주차 경로가 없으면 전환 불가
        if not self.parking_path or not self.parking_path.poses:
            return False
        
        # 주차 경로 시작점과의 거리 계산
        start_point = self.parking_path.poses[0].pose.position
        distance_to_start = self._calculate_distance(self.current_position, start_point)
        
        # 임계 거리 이내면 주차 모드로 전환
        should_switch = distance_to_start < self.parking_threshold
        
        if self.debug_logging and should_switch:
            self.get_logger().info(
                f"Switching to parking mode - distance to start: {distance_to_start:.2f}m"
            )
        
        return should_switch
    
    def _should_switch_to_normal(self) -> bool:
        """일반 모드로 전환해야 하는지 판단"""
        # 주차 경로가 없으면 일반 모드로
        if not self.parking_path or not self.parking_path.poses:
            return True
        
        # 주차 경로 끝점과의 거리 계산
        end_point = self.parking_path.poses[-1].pose.position
        distance_to_end = self._calculate_distance(self.current_position, end_point)
        
        # 끝점에 도달했으면 주차 완료로 간주
        parking_completed = distance_to_end < self.parking_complete_threshold
        
        if self.debug_logging and parking_completed:
            self.get_logger().info(
                f"Parking completed - distance to end: {distance_to_end:.2f}m"
            )
        
        return parking_completed
    
    def _change_mode_to(self, new_mode: str):
        """모드 변경 실행"""
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        # 컨트롤러 모드 신호 발행
        mode_msg = String()
        mode_msg.data = new_mode
        self.controller_mode_pub.publish(mode_msg)
        
        self.get_logger().info(f"Mode changed: {old_mode} → {new_mode}")
    
    def _publish_active_path(self):
        """현재 모드에 맞는 활성 경로 발행"""
        path_to_publish = None
        
        if self.current_mode == "parking" and self.parking_path:
            path_to_publish = self.parking_path
            
        elif self.current_mode == "normal" and self.global_path:
            path_to_publish = self.global_path
        
        if path_to_publish:
            # 타임스탬프 업데이트
            path_to_publish.header.stamp = self.get_clock().now().to_msg()
            self.active_path_pub.publish(path_to_publish)
            
            if self.debug_logging:
                self.get_logger().debug(
                    f"Published {self.current_mode} path: {len(path_to_publish.poses)} points"
                )
    
    def _publish_status(self):
        """시스템 상태 발행"""
        status_info = {
            'mode': self.current_mode,
            'global_path_ready': self.global_path is not None,
            'parking_path_ready': self.parking_path is not None,
            'position_available': self.current_position is not None
        }
        
        status_msg = String()
        status_msg.data = f"mode:{status_info['mode']},global:{status_info['global_path_ready']},parking:{status_info['parking_path_ready']}"
        self.system_status_pub.publish(status_msg)
    
    # ================ 유틸리티 함수들 ================
    
    def _calculate_distance(self, point1: Point, point2: Point) -> float:
        """두 점 사이의 거리 계산"""
        return math.hypot(point1.x - point2.x, point1.y - point2.y)
    
    def get_current_status(self) -> dict:
        """현재 상태 정보 반환 (디버깅용)"""
        status = {
            'current_mode': self.current_mode,
            'position': {
                'x': self.current_position.x if self.current_position else None,
                'y': self.current_position.y if self.current_position else None
            } if self.current_position else None,
            'paths': {
                'global_available': self.global_path is not None,
                'global_points': len(self.global_path.poses) if self.global_path else 0,
                'parking_available': self.parking_path is not None,
                'parking_points': len(self.parking_path.poses) if self.parking_path else 0
            }
        }
        
        # 거리 정보 추가
        if self.current_position:
            if self.parking_path and self.parking_path.poses:
                start_point = self.parking_path.poses[0].pose.position
                end_point = self.parking_path.poses[-1].pose.position
                status['distances'] = {
                    'to_parking_start': self._calculate_distance(self.current_position, start_point),
                    'to_parking_end': self._calculate_distance(self.current_position, end_point)
                }
        
        return status


def main(args=None):
    """메인 함수"""
    rclpy.init(args=args)
    
    try:
        path_manager = PathManager()
        
        # 상태 모니터링용 타이머 (선택사항)
        def print_status():
            status = path_manager.get_current_status()
            path_manager.get_logger().info(f"Status: {status}")
        
        # 10초마다 상태 출력 (디버그 모드에서만)
        if path_manager.debug_logging:
            status_timer = path_manager.create_timer(10.0, print_status)
        
        path_manager.get_logger().info("Path Manager started - monitoring for mode transitions")
        rclpy.spin(path_manager)
        
    except KeyboardInterrupt:
        print("Path Manager shutting down...")
    except Exception as e:
        print(f"Path Manager failed: {e}")
    finally:
        if 'path_manager' in locals():
            try:
                final_status = path_manager.get_current_status()
                print(f"Final Status: {final_status}")
            except:
                pass
            path_manager.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()