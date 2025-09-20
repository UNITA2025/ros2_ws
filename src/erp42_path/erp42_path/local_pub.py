#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from math import cos, sin, sqrt
from typing import List, Optional
import numpy as np
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped, TransformStamped
from visualization_msgs.msg import Marker
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from tf2_ros import TransformBroadcaster


class ImprovedPathPublisher(Node):
    def __init__(self):
        super().__init__('improved_path_pub')

        # === 기본 파라미터 선언 ===
        self.declare_parameter('lookahead_pts_base', 50)           # 기본 lookahead 포인트 수
        self.declare_parameter('lookahead_pts_max', 300)           # 최대 lookahead 포인트 수
        self.declare_parameter('lateral_limit', 10.0)              # 좌우 제한 (m)
        self.declare_parameter('forward_distance_limit', 50.0)     # 전방 거리 제한 (m)
        self.declare_parameter('wrap_path', False)                 # 경로 끝에서 처음으로 래핑할지
        self.declare_parameter('prepend_current', True)            # 현재 위치를 첫 점으로 추가할지
        
        # === 스무딩 파라미터 ===
        self.declare_parameter('enable_path_smoothing', True)      # 경로 스무딩 활성화
        self.declare_parameter('smoothing_window_size', 5)         # 스무딩 윈도우 크기
        self.declare_parameter('min_point_distance', 0.8)         # 최소 점 간격 (m)
        
        # === 필터링 파라미터 ===
        self.declare_parameter('filter_backward_points', True)     # 뒤쪽 점 필터링
        self.declare_parameter('yaw_filter_alpha', 0.8)           # yaw 각도 필터 계수
        self.declare_parameter('enable_speed_adaptation', True)    # 속도 기반 적응형 lookahead
        
        # === 디버깅 파라미터 ===
        self.declare_parameter('enable_debug_logging', False)     # 디버그 로깅
        self.declare_parameter('log_interval_sec', 2.0)          # 로그 출력 간격

        # 파라미터 로드
        self._load_parameters()

        # 구독/퍼블리시
        self.create_subscription(Path, '/active_path', self.global_path_callback, 10)
        self.create_subscription(Odometry, '/odometry/local_enu', self.odom_callback, 10)

        self.local_path_pub = self.create_publisher(Path, '/local_path', 10)
        self.current_pos_marker_pub = self.create_publisher(Marker, '/current_position_marker', 10)
        self.smoothed_path_pub = self.create_publisher(Path, '/smoothed_local_path', 10)  # 디버깅용

        self.tf_broadcaster = TransformBroadcaster(self)

        # 상태 변수
        self.global_path_msg = Path()
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.speed = 0.0
        self.is_status = False
        
        # 필터링용 변수
        self.prev_yaw = 0.0
        self.last_closest_idx = 0
        self.last_log_time = self.get_clock().now()

        # 20 Hz
        self.timer = self.create_timer(0.05, self.timer_callback)
        
        self.get_logger().info('Improved Path Publisher Node started with smoothing enabled.')
        self._log_parameters()

    def _load_parameters(self):
        """파라미터 로드"""
        self.lookahead_pts_base = self.get_parameter('lookahead_pts_base').value
        self.lookahead_pts_max = self.get_parameter('lookahead_pts_max').value
        self.lateral_limit = self.get_parameter('lateral_limit').value
        self.forward_limit = self.get_parameter('forward_distance_limit').value
        self.wrap = self.get_parameter('wrap_path').value
        self.prepend_current = self.get_parameter('prepend_current').value
        
        self.enable_smoothing = self.get_parameter('enable_path_smoothing').value
        self.smoothing_window = self.get_parameter('smoothing_window_size').value
        self.min_point_distance = self.get_parameter('min_point_distance').value
        
        self.filter_backward = self.get_parameter('filter_backward_points').value
        self.yaw_filter_alpha = self.get_parameter('yaw_filter_alpha').value
        self.enable_speed_adaptation = self.get_parameter('enable_speed_adaptation').value
        
        self.debug_logging = self.get_parameter('enable_debug_logging').value
        self.log_interval = self.get_parameter('log_interval_sec').value

    def _log_parameters(self):
        """파라미터 로깅"""
        self.get_logger().info("=== Path Publisher Parameters ===")
        self.get_logger().info(f"Base lookahead points: {self.lookahead_pts_base}")
        self.get_logger().info(f"Path smoothing: {'ON' if self.enable_smoothing else 'OFF'}")
        self.get_logger().info(f"Min point distance: {self.min_point_distance}m")
        self.get_logger().info(f"Smoothing window: {self.smoothing_window}")
        self.get_logger().info(f"Speed adaptation: {'ON' if self.enable_speed_adaptation else 'OFF'}")

    # -------------------- 콜백 함수들 --------------------
    def timer_callback(self):
        if self.is_status:
            self.process_local_path()

    def global_path_callback(self, msg: Path):
        """글로벌 경로 수신"""
        self.global_path_msg = msg
        self.is_status = True
        
        if self.debug_logging:
            self.get_logger().debug(f"Global path received: {len(msg.poses)} points")

    def odom_callback(self, msg: Odometry):
        """오도메트리 수신 및 필터링"""
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        # 속도 계산
        self.speed = sqrt(msg.twist.twist.linear.x**2 + msg.twist.twist.linear.y**2)
        
        # Yaw 각도 필터링
        q = msg.pose.pose.orientation
        _, _, raw_yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        
        # 각도 점프 방지 (wrap-around 처리)
        yaw_diff = raw_yaw - self.prev_yaw
        if abs(yaw_diff) > 3.14159:  # π 이상 차이면 보정
            if yaw_diff > 0:
                raw_yaw -= 2 * 3.14159
            else:
                raw_yaw += 2 * 3.14159
        
        # 저역 통과 필터 적용으로 yaw 안정화
        if self.is_status:  # 이전 값이 있을 때만 필터링
            self.yaw = (self.yaw_filter_alpha * self.prev_yaw + 
                       (1 - self.yaw_filter_alpha) * raw_yaw)
        else:
            self.yaw = raw_yaw
        
        self.prev_yaw = self.yaw
        self.is_status = True

    # -------------------- 핵심 처리 로직 --------------------
    def process_local_path(self):
        """로컬 경로 생성 메인 함수"""
        if not self._validate_inputs():
            return

        x, y, yaw = self.x, self.y, self.yaw

        # TF 브로드캐스트
        self._broadcast_tf(x, y, yaw)
        
        # 현재 위치 마커 발행
        self._publish_current_position_marker(x, y, yaw)

        # 가장 가까운 글로벌 경로 인덱스 (최적화된 탐색)
        start_idx = self.find_closest_index_optimized(x, y)
        poses = self.global_path_msg.poses
        N = len(poses)

        # 동적 lookahead 포인트 수 계산
        lookahead_pts = self._calculate_dynamic_lookahead_pts()

        # 인덱스 목록 구성
        if self.wrap:
            indices = [(start_idx + k) % N for k in range(min(lookahead_pts, N))]
        else:
            end_idx = min(start_idx + lookahead_pts, N)
            indices = list(range(start_idx, end_idx))

        # 기본 로컬 경로 생성
        local_path = self._create_basic_local_path(indices, poses, x, y, yaw)
        
        # 경로 후처리
        local_path.poses = self._post_process_path(local_path.poses)
        
        # 경로 발행
        self.local_path_pub.publish(local_path)
        
        # 디버깅용 스무딩된 경로 발행
        if self.enable_smoothing and self.debug_logging:
            smoothed_debug_path = Path()
            smoothed_debug_path.header = local_path.header
            smoothed_debug_path.poses = local_path.poses
            self.smoothed_path_pub.publish(smoothed_debug_path)
        
        # 주기적 로깅
        self._periodic_logging(len(local_path.poses), start_idx, N)

    def _validate_inputs(self) -> bool:
        """입력 데이터 검증"""
        if not self.global_path_msg.poses:
            if self.debug_logging:
                self.get_logger().warn("Empty global path received")
            return False

        if not self.is_status:
            if self.debug_logging:
                self.get_logger().debug("Odometry not received yet")
            return False

        # 경로가 너무 오래된 경우 체크
        current_time = self.get_clock().now()
        if self.global_path_msg.header.stamp.sec != 0:  # 타임스탬프가 설정된 경우만
            path_age = (current_time - rclpy.time.Time.from_msg(
                self.global_path_msg.header.stamp)).nanoseconds / 1e9
            if path_age > 10.0:  # 10초 이상 된 경로
                self.get_logger().warn(f"Global path is too old: {path_age:.1f}s")
                return False

        return True

    def _calculate_dynamic_lookahead_pts(self) -> int:
        """속도에 따른 동적 lookahead 포인트 수 계산"""
        if not self.enable_speed_adaptation:
            return self.lookahead_pts_base
        
        # 속도가 높을수록 더 많은 점을 봄 (5m/s 기준)
        speed_factor = max(1.0, self.speed / 5.0)
        dynamic_pts = int(self.lookahead_pts_base * speed_factor)
        
        return min(dynamic_pts, self.lookahead_pts_max)

    def _create_basic_local_path(self, indices: List[int], poses: List[PoseStamped], 
                                x: float, y: float, yaw: float) -> Path:
        """기본 로컬 경로 생성"""
        local_path = Path()
        local_path.header.frame_id = 'vehicle_frame'
        local_path.header.stamp = self.get_clock().now().to_msg()

        cos_m = cos(-yaw)
        sin_m = sin(-yaw)

        # 1) 현재 위치를 첫 점으로 추가
        if self.prepend_current:
            current_pose = PoseStamped()
            current_pose.header = local_path.header
            current_pose.pose.position.x = 0.0
            current_pose.pose.position.y = 0.0
            current_pose.pose.position.z = 0.0
            current_pose.pose.orientation.w = 1.0
            local_path.poses.append(current_pose)

        # 2) 글로벌 경로 점들을 vehicle_frame으로 변환
        for i in indices:
            wp = poses[i]
            dx = wp.pose.position.x - x
            dy = wp.pose.position.y - y

            # 좌표 변환: map -> vehicle_frame
            local_x = dx * cos_m - dy * sin_m
            local_y = dx * sin_m + dy * cos_m

            # 필터링 적용
            if not self._apply_point_filters(local_x, local_y):
                continue

            pose = PoseStamped()
            pose.header = local_path.header
            pose.pose.position.x = local_x
            pose.pose.position.y = local_y
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0
            local_path.poses.append(pose)

        return local_path

    def _post_process_path(self, poses: List[PoseStamped]) -> List[PoseStamped]:
        """경로 후처리 (데시메이션 + 스무딩)"""
        if len(poses) < 2:
            return poses
        
        # 1단계: 점 간격 조정 (데시메이션)
        decimated_poses = self._decimate_path(poses)
        
        # 2단계: 스무딩 적용
        if self.enable_smoothing and len(decimated_poses) >= 3:
            smoothed_poses = self._smooth_path(decimated_poses)
            return smoothed_poses
        
        return decimated_poses

    def _decimate_path(self, poses: List[PoseStamped]) -> List[PoseStamped]:
        """너무 촘촘한 점들 제거 (데시메이션)"""
        if len(poses) < 2:
            return poses

        decimated = [poses[0]]  # 첫 번째 점은 항상 유지
        
        for i in range(1, len(poses)):
            curr = poses[i]
            prev = decimated[-1]
            
            dx = curr.pose.position.x - prev.pose.position.x
            dy = curr.pose.position.y - prev.pose.position.y
            dist = sqrt(dx*dx + dy*dy)
            
            if dist >= self.min_point_distance:
                decimated.append(curr)
        
        return decimated

    def _smooth_path(self, poses: List[PoseStamped]) -> List[PoseStamped]:
        """경로 스무딩으로 급격한 변화 제거"""
        if len(poses) < 3:
            return poses
        
        smoothed_poses = []
        window = self.smoothing_window
        
        for i in range(len(poses)):
            if i == 0 or i == len(poses) - 1:
                # 첫 번째와 마지막 점은 그대로 유지
                smoothed_poses.append(poses[i])
            else:
                # 윈도우 범위 계산
                start_idx = max(0, i - window // 2)
                end_idx = min(len(poses), i + window // 2 + 1)
                
                # 가중 평균 계산 (중앙에 더 큰 가중치)
                total_weight = 0.0
                weighted_x = 0.0
                weighted_y = 0.0
                
                for j in range(start_idx, end_idx):
                    # 거리 기반 가중치 (중앙점일수록 큰 가중치)
                    distance_from_center = abs(j - i)
                    weight = max(0.1, 1.0 / (1.0 + distance_from_center))
                    
                    weighted_x += poses[j].pose.position.x * weight
                    weighted_y += poses[j].pose.position.y * weight
                    total_weight += weight
                
                # 스무딩된 점 생성
                smoothed_pose = PoseStamped()
                smoothed_pose.header = poses[i].header
                smoothed_pose.pose.position.x = weighted_x / total_weight
                smoothed_pose.pose.position.y = weighted_y / total_weight
                smoothed_pose.pose.position.z = 0.0
                smoothed_pose.pose.orientation.w = 1.0
                
                smoothed_poses.append(smoothed_pose)
        
        return smoothed_poses

    def _apply_point_filters(self, local_x: float, local_y: float) -> bool:
        """포인트 필터링 적용"""
        # 뒤쪽 점 제거
        if self.filter_backward and local_x < -1.0:
            return False
        
        # 좌우 제한
        if abs(local_y) > self.lateral_limit:
            return False
        
        # 너무 먼 점 제거
        if local_x > self.forward_limit:
            return False
        
        return True

    def find_closest_index_optimized(self, x: float, y: float) -> int:
        """최적화된 가장 가까운 인덱스 탐색"""
        poses = self.global_path_msg.poses
        if not poses:
            return 0
        
        # 이전 인덱스 주변만 탐색 (성능 최적화)
        search_range = min(20, len(poses) // 4)  # 전체의 1/4 또는 20개 중 작은 값
        start_search = max(0, self.last_closest_idx - search_range)
        end_search = min(len(poses), self.last_closest_idx + search_range + 1)
        
        min_ds = float('inf')
        closest_idx = self.last_closest_idx
        
        for i in range(start_search, end_search):
            wp = poses[i]
            dx = wp.pose.position.x - x
            dy = wp.pose.position.y - y
            ds = dx*dx + dy*dy
            if ds < min_ds:
                min_ds = ds
                closest_idx = i
        
        # 지역 최솟값에 빠지지 않도록 가끔 전체 탐색
        if self.get_clock().now().nanoseconds % 1000000000 < 50000000:  # 1초에 한 번 정도
            global_closest_idx = self.find_closest_index(x, y)
            if global_closest_idx != closest_idx:
                closest_idx = global_closest_idx
        
        self.last_closest_idx = closest_idx
        return closest_idx

    def find_closest_index(self, x: float, y: float) -> int:
        """전체 경로에서 가장 가까운 인덱스 (원본 함수)"""
        min_ds = float('inf')
        closest_idx = 0
        for i, wp in enumerate(self.global_path_msg.poses):
            dx = wp.pose.position.x - x
            dy = wp.pose.position.y - y
            ds = dx*dx + dy*dy
            if ds < min_ds:
                min_ds = ds
                closest_idx = i
        return closest_idx

    # -------------------- 유틸리티 함수들 --------------------
    def _broadcast_tf(self, x: float, y: float, yaw: float):
        """TF 브로드캐스트"""
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'vehicle_frame'
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = 0.0
        
        quat = quaternion_from_euler(0.0, 0.0, yaw)
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]
        
        self.tf_broadcaster.sendTransform(t)

    def _publish_current_position_marker(self, x: float, y: float, yaw: float):
        """현재 위치 마커 발행"""
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'current_position'
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = x
        marker.pose.position.y = y
        marker.pose.position.z = 0.0
        marker.scale.x = 0.4
        marker.scale.y = 0.4
        marker.scale.z = 0.4
        marker.color.a = 1.0
        marker.color.r = 0.0
        marker.color.g = 0.0
        marker.color.b = 1.0
        
        quat = quaternion_from_euler(0.0, 0.0, yaw)
        marker.pose.orientation.x = quat[0]
        marker.pose.orientation.y = quat[1]
        marker.pose.orientation.z = quat[2]
        marker.pose.orientation.w = quat[3]
        
        self.current_pos_marker_pub.publish(marker)

    def _periodic_logging(self, path_length: int, start_idx: int, total_poses: int):
        """주기적 상태 로깅"""
        current_time = self.get_clock().now()
        if (current_time - self.last_log_time).nanoseconds > self.log_interval * 1e9:
            self.get_logger().info(
                f"Local path: {path_length} points, "
                f"start_idx: {start_idx}/{total_poses}, "
                f"pos: ({self.x:.2f}, {self.y:.2f}), "
                f"yaw: {self.yaw:.3f}, speed: {self.speed:.2f}m/s"
            )
            self.last_log_time = current_time

    # -------------------- 파라미터 동적 업데이트 --------------------
    def update_parameters(self):
        """런타임 중 파라미터 업데이트 (필요시 사용)"""
        try:
            self._load_parameters()
            self.get_logger().info("Parameters updated successfully")
        except Exception as e:
            self.get_logger().error(f"Failed to update parameters: {e}")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        path_publisher = ImprovedPathPublisher()
        rclpy.spin(path_publisher)
    except KeyboardInterrupt:
        print("Shutting down Path Publisher...")
    except Exception as e:
        print(f"Path Publisher failed: {e}")
    finally:
        if 'path_publisher' in locals():
            path_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()