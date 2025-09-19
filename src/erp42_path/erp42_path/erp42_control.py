# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import math
# from math import atan2, sin
# from typing import List

# import numpy as np
# import rclpy
# from rclpy.node import Node

# from geometry_msgs.msg import Point, PoseStamped
# from nav_msgs.msg import Path
# from visualization_msgs.msg import Marker
# from tf_transformations import quaternion_from_euler

# from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg


# def near_zero(x: float, eps: float = 1e-6) -> bool:
#     return abs(x) < eps


# class PurePursuit(Node):
#     def __init__(self):
#         super().__init__('erp_control')

#         # ================= 파라미터 =================
#         # 단위/샘플링
#         self.declare_parameter('status_speed_unit', 'kmh')  # 'kmh' or 'ms'
#         self.declare_parameter('control_dt', 0.1)           # timer 주기 [s]

#         # 차량/조향
#         self.declare_parameter('wheelbase', 1.82)
#         self.declare_parameter('max_steer_deg', 20.0)           # ±조향 한계
#         self.declare_parameter('max_steer_rate_deg_s', 150.0)   # ±조향 속도 한계

#         # lookahead (속도 스케일)
#         self.declare_parameter('lfd_gain', 2.0)  # lfd = gain * v(m/s)
#         self.declare_parameter('lfd_min', 2.0)
#         self.declare_parameter('lfd_max', 15.0)

#         # 조향 명령 매핑 (ERP42 등)
#         self.declare_parameter('steer_scale_per_deg', 2000.0 / 20.0)  # 20deg -> 2000
#         self.declare_parameter('steer_invert', False)  # 좌/우 반전 필요하면 True

#         # 속도 커맨드 간단 로직
#         self.declare_parameter('speed_cmd_straight', 50)
#         self.declare_parameter('speed_cmd_turn', 50)
#         self.declare_parameter('turn_deg_threshold', 5.0)

#         # (0,0) 첫 점 스킵 여부
#         self.declare_parameter('skip_prepend_current', True)

#         # 파라미터 가져오기
#         self.speed_unit = str(self.get_parameter('status_speed_unit').value).lower()
#         self.dt = float(self.get_parameter('control_dt').value)

#         self.L = float(self.get_parameter('wheelbase').value)
#         self.max_steer_deg = float(self.get_parameter('max_steer_deg').value)
#         self.max_steer_rate_deg_s = float(self.get_parameter('max_steer_rate_deg_s').value)

#         self.lfd_gain = float(self.get_parameter('lfd_gain').value)
#         self.lfd_min = float(self.get_parameter('lfd_min').value)
#         self.lfd_max = float(self.get_parameter('lfd_max').value)

#         self.steer_scale_per_deg = float(self.get_parameter('steer_scale_per_deg').value)
#         self.steer_invert = bool(self.get_parameter('steer_invert').value)

#         self.speed_cmd_straight = int(self.get_parameter('speed_cmd_straight').value)
#         self.speed_cmd_turn = int(self.get_parameter('speed_cmd_turn').value)
#         self.turn_deg_threshold = float(self.get_parameter('turn_deg_threshold').value)

#         self.skip_prepend_current = bool(self.get_parameter('skip_prepend_current').value)

#         # ================= Pub/Sub =================
#         self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
#         self.create_subscription(Path, '/local_path', self.path_callback, 10)
#         self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)

#         # visualization
#         self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
#         self.lookahead_pose_pub   = self.create_publisher(PoseStamped, '/lookahead_pose', 10)

#         # ================= 상태 =================
#         self.is_path = False
#         self.is_status = False
#         self.path = Path()

#         self.cur_speed_ms = 0.0  # m/s로 내부 통일
#         self.vehicle_length = self.L

#         self.forward_point = Point()
#         self._last_steer_deg = 0.0  # 레이트 제한용 메모리

#         self.erp_cmd_msg = ErpCmdMsg()

#         # 타이머 루프
#         self.timer = self.create_timer(self.dt, self.timer_callback)

#         self.get_logger().info(
#             f"PurePursuit started. unit={self.speed_unit}, dt={self.dt}, "
#             f"L={self.L}, max_steer={self.max_steer_deg}deg, rate={self.max_steer_rate_deg_s}deg/s"
#         )

#     # ================= 콜백 =================
#     def path_callback(self, msg: Path):
#         self.path = msg
#         self.is_path = True

#     def status_callback(self, msg: ErpStatusMsg):
#         # 속도 단위 변환
#         if self.speed_unit == 'kmh':
#             self.cur_speed_ms = float(msg.speed) * (1000.0 / 3600.0)
#         else:
#             self.cur_speed_ms = float(msg.speed)
#         self.is_status = True

#     def timer_callback(self):
#         if not self.is_path or not self.is_status:
#             # if not self.is_path:
#             #     self.get_logger().throttle(2000, "[local_path] not received.")
#             # if not self.is_status:
#             #     self.get_logger().throttle(2000, "[erp42_status] not received.")
#             return

#         self.pure_pursuit_control()

#     # ================= 제어 로직 =================
#     def pure_pursuit_control(self):
#         # 1) lookahead 계산 (속도 스케일)
#         v = max(0.0, self.cur_speed_ms)  # m/s
#         lfd = float(np.clip(self.lfd_gain * v, self.lfd_min, self.lfd_max))

#         # 2) 후보 점 집합 (vehicle_frame 기준)
#         poses: List[PoseStamped] = self.path.poses
#         if len(poses) == 0:
#             self.get_logger().warn("Empty /local_path")
#             self.publish_stop()
#             self.clear_lookahead_visuals()
#             return

#         # (0,0) 선두점 스킵 (PREPEND_CURRENT를 쓰는 경우)
#         if self.skip_prepend_current and len(poses) > 0:
#             p0 = poses[0].pose.position
#             if near_zero(p0.x) and near_zero(p0.y):
#                 poses_iter = poses[1:]
#             else:
#                 poses_iter = poses
#         else:
#             poses_iter = poses

#         if len(poses_iter) == 0:
#             self.get_logger().warn("No candidate points after skipping (0,0).")
#             self.publish_stop()
#             self.clear_lookahead_visuals()
#             return

#         # 3) 호길이(arc length) 기반 lookahead 타깃 선택
#         acc = 0.0
#         last_x, last_y = 0.0, 0.0  # vehicle_frame에서 현재 위치는 (0,0)
#         target_found = False
#         for pose in poses_iter:
#             dx = pose.pose.position.x - last_x
#             dy = pose.pose.position.y - last_y
#             acc += math.hypot(dx, dy)
#             last_x, last_y = pose.pose.position.x, pose.pose.position.y
#             if acc >= lfd:
#                 self.forward_point = pose.pose.position
#                 target_found = True
#                 break

#         if not target_found:
#             # 끝점 근접 → 정지
#             end = poses_iter[-1].pose.position
#             if math.hypot(end.x, end.y) < 0.7:
#                 self.get_logger().info("Reached end of path → stop.")
#             else:
#                 self.get_logger().warn("Lookahead not found → stop.")
#             self.publish_stop()
#             self.clear_lookahead_visuals()
#             return

#         # 4) 조향 계산 (Pure Pursuit)
#         theta = atan2(self.forward_point.y, self.forward_point.x)  # 차량좌표계 각도
#         # steer_rad = atan2(2 * L * sin(theta), lfd)
#         steer_rad = math.atan2(2.0 * self.vehicle_length * sin(theta), lfd)
#         steer_deg = math.degrees(steer_rad)

#         # 조향 한계
#         steer_deg = float(np.clip(steer_deg, -self.max_steer_deg, self.max_steer_deg))

#         # 5) 조향 레이트 제한 (deg/s)
#         rate_limit = self.max_steer_rate_deg_s * self.dt
#         d_deg = float(np.clip(steer_deg - self._last_steer_deg, -rate_limit, rate_limit))
#         steer_deg_limited = self._last_steer_deg + d_deg
#         self._last_steer_deg = steer_deg_limited

#         # 6) 조향 명령 매핑
#         steer_cmd = int(self.steer_scale_per_deg * steer_deg_limited)
#         if self.steer_invert:
#             steer_cmd *= -1

#         # 7) 속도 명령(간단)
#         speed_cmd = self.speed_cmd_straight if abs(steer_deg_limited) <= self.turn_deg_threshold else self.speed_cmd_turn

#         # 8) 시각화 & 커맨드 퍼블리시
#         self.publish_lookahead_visuals(theta)
#         self.publish_cmd(steer_cmd, speed_cmd)

#         # 적당한 주기로 로그
#         # self.get_logger().throttle(
#         #     1000,
#         #     f"v={v:.2f}m/s, lfd={lfd:.2f}m, theta={theta:.3f}rad, "
#         #     f"steer={steer_deg_limited:.1f}deg (cmd={steer_cmd})"
#         # )

#     # ================= 퍼블리시/헬퍼 =================
#     def publish_cmd(self, steer_cmd: int, speed_cmd: int):
#         msg = self.erp_cmd_msg
#         msg.steer = steer_cmd
#         msg.speed = speed_cmd
#         msg.gear = 0
#         msg.brake = 0
#         self.cmd_pub.publish(msg)

#     def publish_stop(self):
#         msg = self.erp_cmd_msg
#         msg.gear = 1
#         msg.steer = 0
#         msg.brake = 1
#         self.cmd_pub.publish(msg)

#     def publish_lookahead_visuals(self, theta: float):
#         # marker
#         m = Marker()
#         m.header.frame_id = 'vehicle_frame'
#         m.header.stamp = self.get_clock().now().to_msg()
#         m.ns = 'lookahead'
#         m.id = 0
#         m.type = Marker.SPHERE
#         m.action = Marker.ADD
#         m.pose.position.x = float(self.forward_point.x)
#         m.pose.position.y = float(self.forward_point.y)
#         m.pose.position.z = 0.0
#         m.pose.orientation.w = 1.0
#         m.scale.x = 0.5
#         m.scale.y = 0.5
#         m.scale.z = 0.5
#         m.color.a = 1.0
#         m.color.r = 0.2
#         m.color.g = 0.0
#         m.color.b = 0.9
#         self.lookahead_marker_pub.publish(m)

#         # pose arrow
#         ps = PoseStamped()
#         ps.header.frame_id = 'vehicle_frame'
#         ps.header.stamp = m.header.stamp
#         ps.pose.position.x = float(self.forward_point.x)
#         ps.pose.position.y = float(self.forward_point.y)
#         ps.pose.position.z = 0.0
#         q = quaternion_from_euler(0.0, 0.0, theta)
#         ps.pose.orientation.x = q[0]
#         ps.pose.orientation.y = q[1]
#         ps.pose.orientation.z = q[2]
#         ps.pose.orientation.w = q[3]
#         self.lookahead_pose_pub.publish(ps)

#     def clear_lookahead_visuals(self):
#         m = Marker()
#         m.header.frame_id = 'vehicle_frame'
#         m.header.stamp = self.get_clock().now().to_msg()
#         m.ns = 'lookahead'
#         m.id = 0
#         m.action = Marker.DELETE
#         self.lookahead_marker_pub.publish(m)


# def main(args=None):
#     rclpy.init(args=args)
#     node = PurePursuit()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()


# if __name__ == '__main__':
#     main()



# # 0. 기존 코드 
# # #!/usr/bin/env python3
# # # -*- coding: utf-8 -*-

# # import os
# # import math
# # import numpy as np
# # from math import sqrt, atan2, sin

# # import rclpy
# # from rclpy.node import Node

# # from geometry_msgs.msg import Point, PoseStamped
# # from nav_msgs.msg import Path
# # from visualization_msgs.msg import Marker
# # from tf_transformations import quaternion_from_euler

# # from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg


# # class PurePursuit(Node):
# #     def __init__(self):
# #         super().__init__('erp_control')

# #         # Publishers / Subscribers
# #         self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
# #         self.create_subscription(Path, '/local_path', self.path_callback, 10)
# #         self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)

# #         # NEW: visualization publishers
# #         self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
# #         self.lookahead_pose_pub   = self.create_publisher(PoseStamped, '/lookahead_pose', 10)

# #         # State
# #         self.is_path = False
# #         # self.is_status = False
# #         self.is_status = True
# #         self.forward_point = Point()
# #         self.vehicle_length = 1.82
# #         self.lfd = 3.5

# #         ### 추종할 점의 거리에 대한 gain
# #         self.lfd_gain = 2.0
# #         ###
        
# #         self.cur_speed = 0.0
# #         self.path = Path()
# #         self.erp_cmd_msg = ErpCmdMsg()

# #         self.timer = self.create_timer(0.1, self.timer_callback)

# #     def timer_callback(self):
# #         if self.is_path and self.is_status:
# #             self.pure_pursuit_control(slowdown=True)
# #         else:
# #             os.system('clear')
# #             if not self.is_path:
# #                 self.get_logger().info("[1] '/local_path' x ")
# #             if not self.is_status:
# #                 self.get_logger().info("[2] '/erp42_status' x")

# #     def pure_pursuit_control(self, slowdown=False):
# #         # demo: 고정 속도로 테스트
# #         # self.cur_speed = 30
        
# #         ### lfd 클수록 path상에서 멀리 있는 점 추종. ###
# #         # 즉, 1. 속도가 빠르거나  2. lfd_gain클수록 멀리있는 점 추종.(매끄럽게 주행)
# #         self.lfd = max(2.0, self.lfd_gain  * self.cur_speed)
# #         ##########################################

# #         self.is_look_forward_point = False

# #         # --- find look-ahead point (vehicle_frame 기준) ---
# #         for pose in self.path.poses:
# #             dx = pose.pose.position.x
# #             dy = pose.pose.position.y
# #             # IMPORTANT: >= 0 는 항상 참 -> lfd 사용
# #             dist = sqrt(dx*dx + dy*dy)
# #             self.get_logger().info(f"lfd : {self.lfd:.2f}, cur_speed : {self.cur_speed:.1f}, dist = {dist:.1f} ")
            
# #             if dist >= self.lfd:
# #                 self.forward_point = pose.pose.position
# #                 self.is_look_forward_point = True
# #                 break

# #         if not self.is_look_forward_point:
# #             self.get_logger().warn("추종점 없음.")
# #             self.clear_lookahead_visuals()
# #             self.publish_stop()
# #             return

# #         # 방향각(차량 좌표계에서)
# #         theta = atan2(self.forward_point.y, self.forward_point.x)
# #         steer_rad = atan2(2 * self.vehicle_length * sin(theta), self.lfd)
# #         steer_rad = np.clip(steer_rad, math.radians(-20), math.radians(20))

# #         # --- publish visualization ---
# #         self.publish_lookahead_visuals(theta)

# #         # --- command ---
# #         if -5.0 <= math.degrees(steer_rad) <= 5.0:
# #             self.erp_cmd_msg.speed = 100
# #         else:
# #             self.erp_cmd_msg.speed = 50
# #         self.erp_cmd_msg.steer = -1 *(int((2000/20) * (math.degrees(steer_rad))))
# #         self.erp_cmd_msg.gear = 0
# #         self.erp_cmd_msg.brake = 0

# #         self.cmd_pub.publish(self.erp_cmd_msg)
# #         self.get_logger().info(f"theta={theta:.3f} rad, steer={math.degrees(steer_rad):.1f} deg")

# #     # ========================
# #     # Visualization helpers
# #     # ========================
# #     def publish_lookahead_visuals(self, theta: float):
# #         # Marker (sphere) in vehicle_frame
# #         m = Marker()
# #         m.header.frame_id = 'vehicle_frame'   # /local_path가 vehicle_frame 기준이므로 동일 프레임
# #         m.header.stamp = self.get_clock().now().to_msg()
# #         m.ns = 'lookahead'
# #         m.id = 0
# #         m.type = Marker.SPHERE
# #         m.action = Marker.ADD
# #         m.pose.position.x = float(self.forward_point.x)
# #         m.pose.position.y = float(self.forward_point.y)
# #         m.pose.position.z = 0.0
# #         m.pose.orientation.w = 1.0
# #         m.scale.x = 0.5   # diameter
# #         m.scale.y = 0.5
# #         m.scale.z = 0.5
# #         m.color.a = 1.0
# #         m.color.r = 0.2
# #         m.color.g = 0.0
# #         m.color.b = 0.9
# #         self.lookahead_marker_pub.publish(m)

# #         # PoseStamped (arrow) — RViz 'Pose' 디스플레이에서 확인
# #         ps = PoseStamped()
# #         ps.header.frame_id = 'vehicle_frame'
# #         ps.header.stamp = m.header.stamp
# #         ps.pose.position.x = float(self.forward_point.x)
# #         ps.pose.position.y = float(self.forward_point.y)
# #         ps.pose.position.z = 0.0
# #         q = quaternion_from_euler(0.0, 0.0, theta)
# #         ps.pose.orientation.x = q[0]
# #         ps.pose.orientation.y = q[1]
# #         ps.pose.orientation.z = q[2]
# #         ps.pose.orientation.w = q[3]
# #         self.lookahead_pose_pub.publish(ps)

# #     def clear_lookahead_visuals(self):
# #         m = Marker()
# #         m.header.frame_id = 'vehicle_frame'
# #         m.header.stamp = self.get_clock().now().to_msg()
# #         m.ns = 'lookahead'
# #         m.id = 0
# #         m.action = Marker.DELETE
# #         self.lookahead_marker_pub.publish(m)
# #         # PoseStamped는 굳이 지울 필요 없음(새 값 나오면 갱신)

# #     def publish_stop(self):
# #         self.erp_cmd_msg.gear = 1
# #         self.erp_cmd_msg.steer = 0
# #         self.erp_cmd_msg.brake = 1
# #         self.cmd_pub.publish(self.erp_cmd_msg)

# #     def path_callback(self, msg):
# #         self.path = msg
# #         self.is_path = True

# #     def status_callback(self, msg):
# #         self.cur_speed = msg.speed
# #         self.is_status = True


# # def main(args=None):
# #     rclpy.init(args=args)
# #     node = PurePursuit()
# #     rclpy.spin(node)
# #     node.destroy_node()
# #     rclpy.shutdown()


# # if __name__ == '__main__':
# #     main()

#####

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import logging
import time
import collections
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

import numpy as np
import rclpy
from rclpy.node import Node
import tf2_ros
import tf2_geometry_msgs

from geometry_msgs.msg import Point, PoseStamped, TransformStamped
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker
from tf_transformations import quaternion_from_euler

from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg


def is_near_zero(value: float, tolerance: float = 1e-6) -> bool:
    """Check if a value is close to zero within tolerance."""
    return abs(value) < tolerance


class PurePursuitError(Exception):
    """Pure Pursuit 관련 예외."""
    pass


class TransformError(PurePursuitError):
    """좌표 변환 관련 예외."""
    pass


class ControllerState(Enum):
    """Controller state enumeration for better state management."""
    IDLE = "idle"
    FOLLOWING_PATH = "following_path"
    APPROACHING_GOAL = "approaching_goal"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LookaheadParams:
    """Lookahead distance parameters."""
    gain: float
    min_distance: float
    max_distance: float


@dataclass
class VehicleParams:
    """Vehicle-specific parameters."""
    wheelbase: float
    max_steer_deg: float
    max_steer_rate_deg_s: float
    steer_scale_per_deg: float
    steer_invert: bool


@dataclass
class ControlParams:
    """Control-specific parameters."""
    speed_cmd_straight: int
    speed_cmd_turn: int
    turn_deg_threshold: float
    goal_tolerance: float


@dataclass
class AdaptiveSpeedParams:
    """적응형 속도 제어 파라미터."""
    max_speed: int
    min_speed: int
    curvature_threshold: float
    speed_reduction_factor: float


class PurePursuitController:
    """Pure pursuit control logic separated for testability."""
    
    def __init__(self, vehicle_params: VehicleParams, lookahead_params: LookaheadParams, 
                 adaptive_speed_params: AdaptiveSpeedParams):
        self.vehicle_params = vehicle_params
        self.lookahead_params = lookahead_params
        self.adaptive_speed_params = adaptive_speed_params
        self._last_steer_deg = 0.0
        
        # 성능 최적화를 위한 캐시
        self._position_cache = None
        self._cache_timestamp = 0
    
    def calculate_lookahead_distance(self, current_speed_ms: float) -> float:
        """Calculate adaptive lookahead distance based on speed."""
        lfd = self.lookahead_params.gain * current_speed_ms
        return float(np.clip(lfd, self.lookahead_params.min_distance, self.lookahead_params.max_distance))
    
    def find_closest_point_vectorized(self, poses: List[PoseStamped]) -> int:
        """벡터화를 사용한 가장 가까운 점 찾기."""
        if not poses:
            return 0
        
        # 현재 시간 체크 (캐시 유효성)
        current_time = time.time()
        if (self._position_cache is None or 
            current_time - self._cache_timestamp > 0.1 or 
            len(self._position_cache) != len(poses)):
            
            # 캐시 업데이트
            self._position_cache = np.array([[p.pose.position.x, p.pose.position.y] for p in poses])
            self._cache_timestamp = current_time
        
        distances = np.linalg.norm(self._position_cache, axis=1)
        return int(np.argmin(distances))
    
    def calculate_path_curvature(self, poses: List[PoseStamped], index: int) -> float:
        """경로의 곡률 계산 (3점 방법)."""
        if len(poses) < 3 or index < 1 or index >= len(poses) - 1:
            return 0.0
        
        p1 = poses[index - 1].pose.position
        p2 = poses[index].pose.position  
        p3 = poses[index + 1].pose.position
        
        # 3점을 이용한 곡률 계산
        a = math.hypot(p2.x - p1.x, p2.y - p1.y)
        b = math.hypot(p3.x - p2.x, p3.y - p2.y)
        c = math.hypot(p3.x - p1.x, p3.y - p1.y)
        
        if a < 1e-6 or b < 1e-6 or c < 1e-6:
            return 0.0
        
        # Menger 곡률 공식
        area = abs((p2.x - p1.x) * (p3.y - p1.y) - (p3.x - p1.x) * (p2.y - p1.y)) / 2.0
        curvature = 4.0 * area / (a * b * c)
        
        return curvature
    
    def find_lookahead_point_improved(self, poses: List[PoseStamped], lfd: float) -> Optional[Tuple[Point, float]]:
        """개선된 lookahead 포인트 찾기 (보간 포함). Returns (point, curvature)"""
        if not poses:
            return None
        
        closest_idx = self.find_closest_point_vectorized(poses)
        
        # 역방향 이동 감지 및 처리
        if closest_idx > 0 and closest_idx < len(poses) - 1:
            prev_to_curr = np.array([poses[closest_idx].pose.position.x - poses[closest_idx-1].pose.position.x,
                                    poses[closest_idx].pose.position.y - poses[closest_idx-1].pose.position.y])
            vehicle_direction = np.array([1.0, 0.0])  # 차량 전진 방향
            
            if np.dot(prev_to_curr, vehicle_direction) < 0:
                # 역방향 이동 감지시 더 앞선 포인트부터 시작
                closest_idx = min(closest_idx + 2, len(poses) - 1)
        
        accumulated_distance = 0.0
        if closest_idx < len(poses):
            prev_point = poses[closest_idx].pose.position
        else:
            return None
        
        for i in range(closest_idx + 1, len(poses)):
            curr_point = poses[i].pose.position
            segment_length = math.hypot(curr_point.x - prev_point.x, curr_point.y - prev_point.y)
            
            if accumulated_distance + segment_length >= lfd:
                # 선형 보간으로 정확한 lookahead 포인트 계산
                remaining_dist = lfd - accumulated_distance
                ratio = remaining_dist / segment_length if segment_length > 1e-6 else 0
                
                interpolated_point = Point()
                interpolated_point.x = prev_point.x + ratio * (curr_point.x - prev_point.x)
                interpolated_point.y = prev_point.y + ratio * (curr_point.y - prev_point.y)
                
                # 해당 구간의 곡률 계산
                curvature = self.calculate_path_curvature(poses, i-1) if i > 1 else 0.0
                
                return interpolated_point, curvature
            
            accumulated_distance += segment_length
            prev_point = curr_point
        
        # 경로 끝에 도달한 경우
        if poses:
            curvature = self.calculate_path_curvature(poses, len(poses)-2) if len(poses) > 2 else 0.0
            return poses[-1].pose.position, curvature
        
        return None
    
    def calculate_steering_angle(self, target_point: Point, current_speed_ms: float) -> float:
        """Calculate steering angle using pure pursuit algorithm."""
        lfd = self.calculate_lookahead_distance(current_speed_ms)
        theta = math.atan2(target_point.y, target_point.x)
        
        # Pure pursuit steering calculation
        steer_rad = math.atan2(2.0 * self.vehicle_params.wheelbase * math.sin(theta), lfd)
        steer_deg = math.degrees(steer_rad)
        
        # Apply steering limits
        return float(np.clip(steer_deg, -self.vehicle_params.max_steer_deg, self.vehicle_params.max_steer_deg))
    
    def apply_rate_limit(self, target_steer_deg: float, dt: float) -> float:
        """Apply steering rate limiting."""
        if dt <= 0:
            return self._last_steer_deg
            
        rate_limit = self.vehicle_params.max_steer_rate_deg_s * dt
        delta_deg = float(np.clip(target_steer_deg - self._last_steer_deg, -rate_limit, rate_limit))
        self._last_steer_deg += delta_deg
        return self._last_steer_deg
    
    def calculate_adaptive_speed(self, steer_angle_deg: float, curvature: float) -> int:
        """곡률과 조향각에 따른 적응형 속도 계산."""
        base_speed = self.adaptive_speed_params.max_speed
        
        # 조향각 기반 속도 감소
        steer_factor = 1.0 - min(abs(steer_angle_deg) / self.vehicle_params.max_steer_deg, 1.0) * 0.3
        
        # 경로 곡률 기반 속도 감소  
        curvature_factor = 1.0
        if curvature > self.adaptive_speed_params.curvature_threshold:
            curvature_factor = max(0.5, 1.0 - (curvature - self.adaptive_speed_params.curvature_threshold) * 
                                  self.adaptive_speed_params.speed_reduction_factor)
        
        adaptive_speed = int(base_speed * steer_factor * curvature_factor)
        return max(self.adaptive_speed_params.min_speed, adaptive_speed)
    
    def convert_to_command(self, steer_deg: float) -> int:
        """Convert steering angle to command value."""
        steer_cmd = int(self.vehicle_params.steer_scale_per_deg * steer_deg)
        if self.vehicle_params.steer_invert:
            steer_cmd *= -1
        return steer_cmd


class PurePursuit(Node):
    """Improved Pure Pursuit ROS2 node with enhanced safety and maintainability."""
    
    def __init__(self):
        super().__init__('erp_control')
        
        # Initialize logging
        self.get_logger().set_level(logging.INFO)
        
        # Initialize state
        self.state = ControllerState.IDLE
        self.last_path_time: Optional[rclpy.time.Time] = None
        self.last_status_time: Optional[rclpy.time.Time] = None
        
        # 성능 향상을 위한 히스토리 관리
        self.path_history = collections.deque(maxlen=10)
        self.control_history = collections.deque(maxlen=100)
        
        # 메모리 풀
        self._pose_pool = [PoseStamped() for _ in range(1000)]
        self._pose_pool_index = 0
        
        # Load and validate parameters
        if not self._load_parameters():
            raise RuntimeError("Parameter validation failed")
        
        # Initialize TF2
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Initialize controller
        self.controller = PurePursuitController(
            self.vehicle_params, 
            self.lookahead_params,
            self.adaptive_speed_params
        )
        
        # Initialize ROS interfaces
        self._setup_ros_interfaces()
        
        # Initialize internal state
        self._initialize_state()
        
        # Pre-allocate messages for performance
        self._allocate_messages()
        
        # Performance tracking
        self._last_info_log = self.get_clock().now()
        self._control_start_time = 0.0
        
        # Start control timer
        self.timer = self.create_timer(self.control_dt, self.timer_callback)
        
        self.get_logger().info(
            f"Improved PurePursuit initialized successfully. "
            f"State: {self.state.value}, "
            f"Vehicle frame: {self.vehicle_frame}, "
            f"Control rate: {1.0/self.control_dt:.1f}Hz"
        )
    
    def _get_pooled_pose(self) -> PoseStamped:
        """메모리 풀에서 pose 객체 재사용."""
        pose = self._pose_pool[self._pose_pool_index]
        self._pose_pool_index = (self._pose_pool_index + 1) % len(self._pose_pool)
        return pose
    
    def _load_parameters(self) -> bool:
        """Load and validate all parameters."""
        try:
            # Basic parameters
            self.speed_unit = self._get_parameter('status_speed_unit', str, 'kmh').lower()
            self.control_dt = self._get_parameter('control_dt', float, 0.1)
            
            # Frame parameters
            self.vehicle_frame = self._get_parameter('vehicle_frame', str, 'base_link')
            self.map_frame = self._get_parameter('map_frame', str, 'map')
            
            # Message timeout
            self.msg_timeout_s = self._get_parameter('message_timeout_ms', float, 500.0) / 1000.0
            
            # Vehicle parameters
            wheelbase = self._get_parameter('wheelbase', float, 1.82)
            max_steer_deg = self._get_parameter('max_steer_deg', float, 20.0)
            max_steer_rate_deg_s = self._get_parameter('max_steer_rate_deg_s', float, 150.0)
            steer_scale_per_deg = self._get_parameter('steer_scale_per_deg', float, 100.0)
            steer_invert = self._get_parameter('steer_invert', bool, False)
            
            self.vehicle_params = VehicleParams(
                wheelbase=wheelbase,
                max_steer_deg=max_steer_deg,
                max_steer_rate_deg_s=max_steer_rate_deg_s,
                steer_scale_per_deg=steer_scale_per_deg,
                steer_invert=steer_invert
            )
            
            # Lookahead parameters
            lfd_gain = self._get_parameter('lfd_gain', float, 2.0)
            lfd_min = self._get_parameter('lfd_min', float, 2.0)
            lfd_max = self._get_parameter('lfd_max', float, 15.0)
            
            self.lookahead_params = LookaheadParams(
                gain=lfd_gain,
                min_distance=lfd_min,
                max_distance=lfd_max
            )
            
            # Control parameters
            speed_cmd_straight = self._get_parameter('speed_cmd_straight', int, 100)
            speed_cmd_turn = self._get_parameter('speed_cmd_turn', int, 50)
            turn_deg_threshold = self._get_parameter('turn_deg_threshold', float, 5.0)
            goal_tolerance = self._get_parameter('goal_tolerance', float, 0.7)
            
            self.control_params = ControlParams(
                speed_cmd_straight=speed_cmd_straight,
                speed_cmd_turn=speed_cmd_turn,
                turn_deg_threshold=turn_deg_threshold,
                goal_tolerance=goal_tolerance
            )
            
            # Adaptive speed parameters
            max_speed = self._get_parameter('adaptive_max_speed', int, speed_cmd_straight)
            min_speed = self._get_parameter('adaptive_min_speed', int, 30)
            curvature_threshold = self._get_parameter('curvature_threshold', float, 0.1)
            speed_reduction_factor = self._get_parameter('speed_reduction_factor', float, 0.5)
            
            self.adaptive_speed_params = AdaptiveSpeedParams(
                max_speed=max_speed,
                min_speed=min_speed,
                curvature_threshold=curvature_threshold,
                speed_reduction_factor=speed_reduction_factor
            )
            
            # Path processing
            self.skip_prepend_current = self._get_parameter('skip_prepend_current', bool, True)
            
            return self._validate_parameters()
            
        except Exception as e:
            self.get_logger().error(f"Parameter loading failed: {e}")
            return False
    
    def _get_parameter(self, name: str, param_type: type, default_value: Any) -> Any:
        """Safely get parameter with type checking."""
        self.declare_parameter(name, default_value)
        try:
            value = self.get_parameter(name).value
            return param_type(value)
        except (ValueError, TypeError) as e:
            self.get_logger().warn(f"Parameter {name} conversion error: {e}. Using default: {default_value}")
            return default_value
    
    def _validate_parameters(self) -> bool:
        """더 엄격한 파라미터 검증."""
        validators = [
            (self.lookahead_params.min_distance < self.lookahead_params.max_distance, "lfd_min < lfd_max"),
            (self.vehicle_params.max_steer_deg > 0, "max_steer_deg > 0"),
            (self.vehicle_params.wheelbase > 0, "wheelbase > 0"),
            (0.001 <= self.control_dt <= 1.0, "control_dt in valid range [0.001, 1.0]"),
            (self.msg_timeout_s > 0, "message timeout > 0"),
            (self.lookahead_params.gain > 0, "lookahead gain > 0"),
            (self.vehicle_params.max_steer_rate_deg_s > 0, "steer rate > 0"),
            (self.control_params.goal_tolerance > 0, "goal_tolerance > 0"),
            (self.adaptive_speed_params.min_speed <= self.adaptive_speed_params.max_speed, "min_speed <= max_speed"),
            (self.adaptive_speed_params.curvature_threshold >= 0, "curvature_threshold >= 0"),
            (0 <= self.adaptive_speed_params.speed_reduction_factor <= 1.0, "speed_reduction_factor in [0, 1]"),
        ]
        
        failed_checks = [msg for condition, msg in validators if not condition]
        
        if failed_checks:
            for check in failed_checks:
                self.get_logger().error(f"Parameter validation failed: {check}")
            return False
        
        return True
    
    def _setup_ros_interfaces(self):
        """Setup publishers and subscribers."""
        # Publishers
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
        self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
        self.lookahead_pose_pub = self.create_publisher(PoseStamped, '/lookahead_pose', 10)
        
        # Subscribers
        self.create_subscription(Path, '/local_path', self.path_callback, 10)
        self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)
    
    
    def _initialize_state(self):
        """Initialize internal state variables."""
        self.path = Path()
        self.cur_speed_ms = 0.0
        self.forward_point = Point()
        self.current_curvature = 0.0
    
    def _allocate_messages(self):
        """Pre-allocate message objects for performance."""
        self._cmd_msg = ErpCmdMsg()
        self._marker_msg = Marker()
        self._pose_msg = PoseStamped()
        
        # Setup marker message template
        self._marker_msg.header.frame_id = self.vehicle_frame
        self._marker_msg.ns = 'lookahead'
        self._marker_msg.id = 0
        self._marker_msg.type = Marker.SPHERE
        self._marker_msg.action = Marker.ADD
        self._marker_msg.scale.x = 0.5
        self._marker_msg.scale.y = 0.5
        self._marker_msg.scale.z = 0.5
        self._marker_msg.color.a = 1.0
        self._marker_msg.color.r = 0.2
        self._marker_msg.color.g = 0.0
        self._marker_msg.color.b = 0.9
        self._marker_msg.pose.orientation.w = 1.0
    
    def path_callback(self, msg: Path):
        """Handle incoming path messages."""
        try:
            # Transform path to vehicle frame if needed
            if msg.header.frame_id != self.vehicle_frame:
                transformed_path = self._transform_path_to_vehicle_frame(msg)
                if transformed_path is not None:
                    self.path = transformed_path
                else:
                    self.get_logger().warn(f"Failed to transform path from {msg.header.frame_id} to {self.vehicle_frame}")
                    return
            else:
                self.path = msg
            
            # 경로 히스토리 저장
            self.path_history.append(self.path)
            
            self.last_path_time = self.get_clock().now()
            
            if self.state == ControllerState.IDLE:
                self.state = ControllerState.FOLLOWING_PATH
                self.get_logger().info("Started following path")
                
        except Exception as e:
            self.get_logger().error(f"Path callback error: {e}")
            self.state = ControllerState.ERROR
    
    def status_callback(self, msg: ErpStatusMsg):
        """Handle incoming status messages with safety checks."""
        try:
            # Convert speed to m/s
            if self.speed_unit == 'kmh':
                self.cur_speed_ms = max(0.0, float(msg.speed) * (1000.0 / 3600.0))
            else:
                self.cur_speed_ms = max(0.0, float(msg.speed))
            
            self.last_status_time = self.get_clock().now()
            
        except (ValueError, TypeError) as e:
            self.get_logger().error(f"Status callback error: {e}")
            self.cur_speed_ms = 0.0
    
    def timer_callback(self):
        """Main control loop."""
        self._control_start_time = time.time()
        
        try:
            # Check data freshness
            if not self._is_data_fresh():
                if self.state != ControllerState.ERROR:
                    self.get_logger().warn("Stale data detected - stopping")
                    self.state = ControllerState.ERROR
                self._publish_stop()
                self._clear_lookahead_visuals()
                return
            
            # Reset from error state if data is fresh
            if self.state == ControllerState.ERROR and self._is_data_fresh():
                self.state = ControllerState.FOLLOWING_PATH
                self.get_logger().info("Recovered from error state")
            
            # Execute control logic
            if self.state in [ControllerState.FOLLOWING_PATH, ControllerState.APPROACHING_GOAL]:
                self._pure_pursuit_control()
            else:
                self._publish_stop()
                self._clear_lookahead_visuals()
                
        except Exception as e:
            self.get_logger().error(f"Control loop error: {e}")
            self.state = ControllerState.ERROR
            self._publish_stop()
            self._clear_lookahead_visuals()
    
    def _is_data_fresh(self) -> bool:
        """Check if received data is fresh enough."""
        if self.last_path_time is None or self.last_status_time is None:
            return False
        
        current_time = self.get_clock().now()
        path_age = (current_time - self.last_path_time).nanoseconds / 1e9
        status_age = (current_time - self.last_status_time).nanoseconds / 1e9
        
        return path_age < self.msg_timeout_s and status_age < self.msg_timeout_s
    
    def _transform_path_to_vehicle_frame(self, path: Path) -> Optional[Path]:
        """좌표 변환 with 더 나은 예외 처리."""
        max_retries = 3
        retry_delay = 0.05
        
        for attempt in range(max_retries):
            try:
                transform = self.tf_buffer.lookup_transform(
                    self.vehicle_frame,
                    path.header.frame_id,
                    rclpy.time.Time(),
                    timeout=rclpy.duration.Duration(seconds=0.1)
                )
                
                # 변환 수행
                transformed_path = Path()
                transformed_path.header.frame_id = self.vehicle_frame
                transformed_path.header.stamp = self.get_clock().now().to_msg()
                
                for pose_stamped in path.poses:
                    transformed_pose = tf2_geometry_msgs.do_transform_pose_stamped(pose_stamped, transform)
                    transformed_path.poses.append(transformed_pose)
                
                return transformed_path
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.get_logger().debug(f"Transform attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(retry_delay)
                else:
                    self.get_logger().error(f"Transform failed after {max_retries} attempts: {e}")
                    return None
        
        return None
    
    def _pure_pursuit_control(self):
        """Execute pure pursuit control algorithm."""
        # Get candidate poses
        poses = self._get_candidate_poses()
        if not poses:
            self.get_logger().warn("No candidate poses available")
            self._publish_stop()
            self._clear_lookahead_visuals()
            return
        
        # Calculate lookahead distance
        lfd = self.controller.calculate_lookahead_distance(self.cur_speed_ms)
        
        # Find lookahead point with curvature
        result = self.controller.find_lookahead_point_improved(poses, lfd)
        if result is None:
            self.get_logger().warn("No lookahead point found")
            self._publish_stop()
            self._clear_lookahead_visuals()
            return
        
        target_point, curvature = result
        self.current_curvature = curvature
        
        # Check if approaching goal
        distance_to_target = math.hypot(target_point.x, target_point.y)
        if distance_to_target < self.control_params.goal_tolerance:
            if self.state != ControllerState.APPROACHING_GOAL:
                self.get_logger().info("Approaching goal")
                self.state = ControllerState.APPROACHING_GOAL
            self._publish_stop()
            self._clear_lookahead_visuals()
            return
        
        # Calculate steering
        steer_deg = self.controller.calculate_steering_angle(target_point, self.cur_speed_ms)
        steer_deg_limited = self.controller.apply_rate_limit(steer_deg, self.control_dt)
        steer_cmd = self.controller.convert_to_command(steer_deg_limited)
        
        # Calculate adaptive speed command
        speed_cmd = self.controller.calculate_adaptive_speed(steer_deg_limited, curvature)
        
        # Publish commands and visuals
        self.forward_point = target_point
        theta = math.atan2(target_point.y, target_point.x)
        
        self._publish_cmd(steer_cmd, speed_cmd)
        self._publish_lookahead_visuals(theta)
        
        # Performance tracking
        control_time = time.time() - self._control_start_time
        
        # Control history for analysis
        control_data = {
            'timestamp': time.time(),
            'speed_ms': self.cur_speed_ms,
            'lfd': lfd,
            'steer_deg': steer_deg_limited,
            'curvature': curvature,
            'distance_to_target': distance_to_target,
            'control_time': control_time
        }
        self.control_history.append(control_data)
        
        # Debug logging
        self._log_control_metrics(control_data)
    
    def _get_candidate_poses(self) -> List[PoseStamped]:
        """Get candidate poses for lookahead calculation."""
        poses = self.path.poses
        if not poses:
            return []
        
        # Skip (0,0) starting point if configured
        if self.skip_prepend_current and len(poses) > 0:
            first_pose = poses[0].pose.position
            if is_near_zero(first_pose.x) and is_near_zero(first_pose.y):
                return poses[1:] if len(poses) > 1 else []
        
        return poses
    
    def _publish_cmd(self, steer_cmd: int, speed_cmd: int):
        """Publish control command."""
        msg = self._cmd_msg
        msg.steer = steer_cmd
        msg.speed = speed_cmd
        msg.gear = 0
        msg.brake = 0
        self.cmd_pub.publish(msg)
    
    def _publish_stop(self):
        """Publish stop command."""
        msg = self._cmd_msg
        msg.gear = 1
        msg.steer = 0
        msg.brake = 1
        msg.speed = 0
        self.cmd_pub.publish(msg)
    
    def _publish_lookahead_visuals(self, theta: float):
        """Publish lookahead visualization markers."""
        timestamp = self.get_clock().now().to_msg()
        
        # Publish marker
        marker = self._marker_msg
        marker.header.stamp = timestamp
        marker.pose.position.x = float(self.forward_point.x)
        marker.pose.position.y = float(self.forward_point.y)
        marker.pose.position.z = 0.0
        
        # 곡률에 따른 색상 변경 (높은 곡률 = 빨간색)
        curvature_normalized = min(self.current_curvature / 0.5, 1.0)  # 0.5 이상은 최대 빨간색
        marker.color.r = 0.2 + 0.8 * curvature_normalized
        marker.color.g = 0.8 * (1.0 - curvature_normalized)
        marker.color.b = 0.9 * (1.0 - curvature_normalized)
        
        self.lookahead_marker_pub.publish(marker)
        
        # Publish pose with direction
        pose_msg = self._pose_msg
        pose_msg.header.frame_id = self.vehicle_frame
        pose_msg.header.stamp = timestamp
        pose_msg.pose.position.x = float(self.forward_point.x)
        pose_msg.pose.position.y = float(self.forward_point.y)
        pose_msg.pose.position.z = 0.0
        
        q = quaternion_from_euler(0.0, 0.0, theta)
        pose_msg.pose.orientation.x = q[0]
        pose_msg.pose.orientation.y = q[1]
        pose_msg.pose.orientation.z = q[2]
        pose_msg.pose.orientation.w = q[3]
        
        self.lookahead_pose_pub.publish(pose_msg)
    
    def _clear_lookahead_visuals(self):
        """Clear lookahead visualization markers."""
        marker = Marker()
        marker.header.frame_id = self.vehicle_frame
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'lookahead'
        marker.id = 0
        marker.action = Marker.DELETE
        self.lookahead_marker_pub.publish(marker)
    
    def _log_control_metrics(self, metrics: Dict[str, float]):
        """성능 메트릭 로깅."""
        # Debug level로 자세한 정보
        self.get_logger().debug(
            f"Pure Pursuit Debug - "
            f"Speed: {metrics['speed_ms']:.2f}m/s, "
            f"LFD: {metrics['lfd']:.2f}m, "
            f"Target: ({self.forward_point.x:.2f}, {self.forward_point.y:.2f}), "
            f"Distance: {metrics['distance_to_target']:.2f}m, "
            f"Steer: {metrics['steer_deg']:.2f}°, "
            f"Curvature: {metrics['curvature']:.4f}, "
            f"Control Time: {metrics['control_time']*1000:.1f}ms, "
            f"State: {self.state.value}"
        )
        
        # 주기적 정보 로깅 (1초마다)
        current_time = self.get_clock().now()
        if (current_time - self._last_info_log).nanoseconds > 1e9:  # 1 second
            self._log_periodic_info(metrics)
            self._last_info_log = current_time
    
    def _log_periodic_info(self, metrics: Dict[str, float]):
        """주기적 제어 정보 로깅."""
        # 최근 제어 성능 통계
        if len(self.control_history) > 10:
            recent_controls = list(self.control_history)[-10:]
            avg_control_time = np.mean([c['control_time'] for c in recent_controls]) * 1000
            max_control_time = np.max([c['control_time'] for c in recent_controls]) * 1000
            avg_curvature = np.mean([c['curvature'] for c in recent_controls])
            
            self.get_logger().info(
                f"Control Stats: v={metrics['speed_ms']:.2f}m/s, "
                f"lfd={metrics['lfd']:.2f}m, steer={metrics['steer_deg']:.1f}°, "
                f"curv={avg_curvature:.4f}, state={self.state.value}, "
                f"ctrl_time: avg={avg_control_time:.1f}ms max={max_control_time:.1f}ms"
            )
        else:
            self.get_logger().info(
                f"Control: v={metrics['speed_ms']:.2f}m/s, "
                f"lfd={metrics['lfd']:.2f}m, steer={metrics['steer_deg']:.1f}°, "
                f"state={self.state.value}"
            )
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """성능 통계 반환 (디버깅/모니터링용)."""
        if not self.control_history:
            return {}
        
        controls = list(self.control_history)
        
        return {
            'total_controls': len(controls),
            'avg_control_time_ms': np.mean([c['control_time'] for c in controls]) * 1000,
            'max_control_time_ms': np.max([c['control_time'] for c in controls]) * 1000,
            'avg_speed_ms': np.mean([c['speed_ms'] for c in controls]),
            'avg_curvature': np.mean([c['curvature'] for c in controls]),
            'max_curvature': np.max([c['curvature'] for c in controls]),
            'avg_steering_deg': np.mean([abs(c['steer_deg']) for c in controls]),
            'max_steering_deg': np.max([abs(c['steer_deg']) for c in controls]),
            'current_state': self.state.value,
            'paths_received': len(self.path_history)
        }


def main(args=None):
    """Main entry point."""
    rclpy.init(args=args)
    
    try:
        node = PurePursuit()
        
        # 성능 모니터링을 위한 간단한 타이머 (선택사항)
        def print_stats():
            stats = node.get_performance_statistics()
            if stats:
                node.get_logger().info(f"Performance Summary: {stats}")
        
        # 10초마다 성능 통계 출력 (디버그 모드에서만)
        stats_timer = node.create_timer(10.0, print_stats)
        
        rclpy.spin(node)
        
    except KeyboardInterrupt:
        print("Shutting down Pure Pursuit controller...")
    except Exception as e:
        print(f"Node failed: {e}")
    finally:
        if 'node' in locals():
            # 최종 통계 출력
            try:
                final_stats = node.get_performance_statistics()
                if final_stats:
                    print(f"Final Performance Statistics:")
                    for key, value in final_stats.items():
                        print(f"  {key}: {value}")
            except:
                pass
            
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()