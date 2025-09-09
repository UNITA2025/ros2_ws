#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from math import atan2, sin
from typing import List

import numpy as np
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker
from tf_transformations import quaternion_from_euler

from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg


def near_zero(x: float, eps: float = 1e-6) -> bool:
    return abs(x) < eps


class PurePursuit(Node):
    def __init__(self):
        super().__init__('erp_control')

        # ================= 파라미터 =================
        # 단위/샘플링
        self.declare_parameter('status_speed_unit', 'kmh')  # 'kmh' or 'ms'
        self.declare_parameter('control_dt', 0.1)           # timer 주기 [s]

        # 차량/조향
        self.declare_parameter('wheelbase', 1.82)
        self.declare_parameter('max_steer_deg', 20.0)           # ±조향 한계
        self.declare_parameter('max_steer_rate_deg_s', 150.0)   # ±조향 속도 한계

        # lookahead (속도 스케일)
        self.declare_parameter('lfd_gain', 2.0)  # lfd = gain * v(m/s)
        self.declare_parameter('lfd_min', 2.0)
        self.declare_parameter('lfd_max', 15.0)

        # 조향 명령 매핑 (ERP42 등)
        self.declare_parameter('steer_scale_per_deg', 2000.0 / 20.0)  # 20deg -> 2000
        self.declare_parameter('steer_invert', False)  # 좌/우 반전 필요하면 True

        # 속도 커맨드 간단 로직
        self.declare_parameter('speed_cmd_straight', 100)
        self.declare_parameter('speed_cmd_turn', 50)
        self.declare_parameter('turn_deg_threshold', 5.0)

        # (0,0) 첫 점 스킵 여부
        self.declare_parameter('skip_prepend_current', True)

        # 파라미터 가져오기
        self.speed_unit = str(self.get_parameter('status_speed_unit').value).lower()
        self.dt = float(self.get_parameter('control_dt').value)

        self.L = float(self.get_parameter('wheelbase').value)
        self.max_steer_deg = float(self.get_parameter('max_steer_deg').value)
        self.max_steer_rate_deg_s = float(self.get_parameter('max_steer_rate_deg_s').value)

        self.lfd_gain = float(self.get_parameter('lfd_gain').value)
        self.lfd_min = float(self.get_parameter('lfd_min').value)
        self.lfd_max = float(self.get_parameter('lfd_max').value)

        self.steer_scale_per_deg = float(self.get_parameter('steer_scale_per_deg').value)
        self.steer_invert = bool(self.get_parameter('steer_invert').value)

        self.speed_cmd_straight = int(self.get_parameter('speed_cmd_straight').value)
        self.speed_cmd_turn = int(self.get_parameter('speed_cmd_turn').value)
        self.turn_deg_threshold = float(self.get_parameter('turn_deg_threshold').value)

        self.skip_prepend_current = bool(self.get_parameter('skip_prepend_current').value)

        # ================= Pub/Sub =================
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
        self.create_subscription(Path, '/local_path', self.path_callback, 10)
        self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)

        # visualization
        self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
        self.lookahead_pose_pub   = self.create_publisher(PoseStamped, '/lookahead_pose', 10)

        # ================= 상태 =================
        self.is_path = False
        self.is_status = False
        self.path = Path()

        self.cur_speed_ms = 0.0  # m/s로 내부 통일
        self.vehicle_length = self.L

        self.forward_point = Point()
        self._last_steer_deg = 0.0  # 레이트 제한용 메모리

        self.erp_cmd_msg = ErpCmdMsg()

        # 타이머 루프
        self.timer = self.create_timer(self.dt, self.timer_callback)

        self.get_logger().info(
            f"PurePursuit started. unit={self.speed_unit}, dt={self.dt}, "
            f"L={self.L}, max_steer={self.max_steer_deg}deg, rate={self.max_steer_rate_deg_s}deg/s"
        )

    # ================= 콜백 =================
    def path_callback(self, msg: Path):
        self.path = msg
        self.is_path = True

    def status_callback(self, msg: ErpStatusMsg):
        # 속도 단위 변환
        if self.speed_unit == 'kmh':
            self.cur_speed_ms = float(msg.speed) * (1000.0 / 3600.0)
        else:
            self.cur_speed_ms = float(msg.speed)
        self.is_status = True

    def timer_callback(self):
        if not self.is_path or not self.is_status:
            if not self.is_path:
                self.get_logger().throttle(2000, "[local_path] not received.")
            if not self.is_status:
                self.get_logger().throttle(2000, "[erp42_status] not received.")
            return

        self.pure_pursuit_control()

    # ================= 제어 로직 =================
    def pure_pursuit_control(self):
        # 1) lookahead 계산 (속도 스케일)
        v = max(0.0, self.cur_speed_ms)  # m/s
        lfd = float(np.clip(self.lfd_gain * v, self.lfd_min, self.lfd_max))

        # 2) 후보 점 집합 (vehicle_frame 기준)
        poses: List[PoseStamped] = self.path.poses
        if len(poses) == 0:
            self.get_logger().warn("Empty /local_path")
            self.publish_stop()
            self.clear_lookahead_visuals()
            return

        # (0,0) 선두점 스킵 (PREPEND_CURRENT를 쓰는 경우)
        if self.skip_prepend_current and len(poses) > 0:
            p0 = poses[0].pose.position
            if near_zero(p0.x) and near_zero(p0.y):
                poses_iter = poses[1:]
            else:
                poses_iter = poses
        else:
            poses_iter = poses

        if len(poses_iter) == 0:
            self.get_logger().warn("No candidate points after skipping (0,0).")
            self.publish_stop()
            self.clear_lookahead_visuals()
            return

        # 3) 호길이(arc length) 기반 lookahead 타깃 선택
        acc = 0.0
        last_x, last_y = 0.0, 0.0  # vehicle_frame에서 현재 위치는 (0,0)
        target_found = False
        for pose in poses_iter:
            dx = pose.pose.position.x - last_x
            dy = pose.pose.position.y - last_y
            acc += math.hypot(dx, dy)
            last_x, last_y = pose.pose.position.x, pose.pose.position.y
            if acc >= lfd:
                self.forward_point = pose.pose.position
                target_found = True
                break

        if not target_found:
            # 끝점 근접 → 정지
            end = poses_iter[-1].pose.position
            if math.hypot(end.x, end.y) < 0.7:
                self.get_logger().info("Reached end of path → stop.")
            else:
                self.get_logger().warn("Lookahead not found → stop.")
            self.publish_stop()
            self.clear_lookahead_visuals()
            return

        # 4) 조향 계산 (Pure Pursuit)
        theta = atan2(self.forward_point.y, self.forward_point.x)  # 차량좌표계 각도
        # steer_rad = atan2(2 * L * sin(theta), lfd)
        steer_rad = math.atan2(2.0 * self.vehicle_length * sin(theta), lfd)
        steer_deg = math.degrees(steer_rad)

        # 조향 한계
        steer_deg = float(np.clip(steer_deg, -self.max_steer_deg, self.max_steer_deg))

        # 5) 조향 레이트 제한 (deg/s)
        rate_limit = self.max_steer_rate_deg_s * self.dt
        d_deg = float(np.clip(steer_deg - self._last_steer_deg, -rate_limit, rate_limit))
        steer_deg_limited = self._last_steer_deg + d_deg
        self._last_steer_deg = steer_deg_limited

        # 6) 조향 명령 매핑
        steer_cmd = int(self.steer_scale_per_deg * steer_deg_limited)
        if self.steer_invert:
            steer_cmd *= -1

        # 7) 속도 명령(간단)
        speed_cmd = self.speed_cmd_straight if abs(steer_deg_limited) <= self.turn_deg_threshold else self.speed_cmd_turn

        # 8) 시각화 & 커맨드 퍼블리시
        self.publish_lookahead_visuals(theta)
        self.publish_cmd(steer_cmd, speed_cmd)

        # 적당한 주기로 로그
        self.get_logger().throttle(
            1000,
            f"v={v:.2f}m/s, lfd={lfd:.2f}m, theta={theta:.3f}rad, "
            f"steer={steer_deg_limited:.1f}deg (cmd={steer_cmd})"
        )

    # ================= 퍼블리시/헬퍼 =================
    def publish_cmd(self, steer_cmd: int, speed_cmd: int):
        msg = self.erp_cmd_msg
        msg.steer = steer_cmd
        msg.speed = speed_cmd
        msg.gear = 0
        msg.brake = 0
        self.cmd_pub.publish(msg)

    def publish_stop(self):
        msg = self.erp_cmd_msg
        msg.gear = 1
        msg.steer = 0
        msg.brake = 1
        self.cmd_pub.publish(msg)

    def publish_lookahead_visuals(self, theta: float):
        # marker
        m = Marker()
        m.header.frame_id = 'vehicle_frame'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'lookahead'
        m.id = 0
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = float(self.forward_point.x)
        m.pose.position.y = float(self.forward_point.y)
        m.pose.position.z = 0.0
        m.pose.orientation.w = 1.0
        m.scale.x = 0.5
        m.scale.y = 0.5
        m.scale.z = 0.5
        m.color.a = 1.0
        m.color.r = 0.2
        m.color.g = 0.0
        m.color.b = 0.9
        self.lookahead_marker_pub.publish(m)

        # pose arrow
        ps = PoseStamped()
        ps.header.frame_id = 'vehicle_frame'
        ps.header.stamp = m.header.stamp
        ps.pose.position.x = float(self.forward_point.x)
        ps.pose.position.y = float(self.forward_point.y)
        ps.pose.position.z = 0.0
        q = quaternion_from_euler(0.0, 0.0, theta)
        ps.pose.orientation.x = q[0]
        ps.pose.orientation.y = q[1]
        ps.pose.orientation.z = q[2]
        ps.pose.orientation.w = q[3]
        self.lookahead_pose_pub.publish(ps)

    def clear_lookahead_visuals(self):
        m = Marker()
        m.header.frame_id = 'vehicle_frame'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'lookahead'
        m.id = 0
        m.action = Marker.DELETE
        self.lookahead_marker_pub.publish(m)


def main(args=None):
    rclpy.init(args=args)
    node = PurePursuit()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()



# 0. 기존 코드 
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import os
# import math
# import numpy as np
# from math import sqrt, atan2, sin

# import rclpy
# from rclpy.node import Node

# from geometry_msgs.msg import Point, PoseStamped
# from nav_msgs.msg import Path
# from visualization_msgs.msg import Marker
# from tf_transformations import quaternion_from_euler

# from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg


# class PurePursuit(Node):
#     def __init__(self):
#         super().__init__('erp_control')

#         # Publishers / Subscribers
#         self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
#         self.create_subscription(Path, '/local_path', self.path_callback, 10)
#         self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)

#         # NEW: visualization publishers
#         self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
#         self.lookahead_pose_pub   = self.create_publisher(PoseStamped, '/lookahead_pose', 10)

#         # State
#         self.is_path = False
#         # self.is_status = False
#         self.is_status = True
#         self.forward_point = Point()
#         self.vehicle_length = 1.82
#         self.lfd = 3.5

#         ### 추종할 점의 거리에 대한 gain
#         self.lfd_gain = 2.0
#         ###
        
#         self.cur_speed = 0.0
#         self.path = Path()
#         self.erp_cmd_msg = ErpCmdMsg()

#         self.timer = self.create_timer(0.1, self.timer_callback)

#     def timer_callback(self):
#         if self.is_path and self.is_status:
#             self.pure_pursuit_control(slowdown=True)
#         else:
#             os.system('clear')
#             if not self.is_path:
#                 self.get_logger().info("[1] '/local_path' x ")
#             if not self.is_status:
#                 self.get_logger().info("[2] '/erp42_status' x")

#     def pure_pursuit_control(self, slowdown=False):
#         # demo: 고정 속도로 테스트
#         # self.cur_speed = 30
        
#         ### lfd 클수록 path상에서 멀리 있는 점 추종. ###
#         # 즉, 1. 속도가 빠르거나  2. lfd_gain클수록 멀리있는 점 추종.(매끄럽게 주행)
#         self.lfd = max(2.0, self.lfd_gain  * self.cur_speed)
#         ##########################################

#         self.is_look_forward_point = False

#         # --- find look-ahead point (vehicle_frame 기준) ---
#         for pose in self.path.poses:
#             dx = pose.pose.position.x
#             dy = pose.pose.position.y
#             # IMPORTANT: >= 0 는 항상 참 -> lfd 사용
#             dist = sqrt(dx*dx + dy*dy)
#             self.get_logger().info(f"lfd : {self.lfd:.2f}, cur_speed : {self.cur_speed:.1f}, dist = {dist:.1f} ")
            
#             if dist >= self.lfd:
#                 self.forward_point = pose.pose.position
#                 self.is_look_forward_point = True
#                 break

#         if not self.is_look_forward_point:
#             self.get_logger().warn("추종점 없음.")
#             self.clear_lookahead_visuals()
#             self.publish_stop()
#             return

#         # 방향각(차량 좌표계에서)
#         theta = atan2(self.forward_point.y, self.forward_point.x)
#         steer_rad = atan2(2 * self.vehicle_length * sin(theta), self.lfd)
#         steer_rad = np.clip(steer_rad, math.radians(-20), math.radians(20))

#         # --- publish visualization ---
#         self.publish_lookahead_visuals(theta)

#         # --- command ---
#         if -5.0 <= math.degrees(steer_rad) <= 5.0:
#             self.erp_cmd_msg.speed = 100
#         else:
#             self.erp_cmd_msg.speed = 50
#         self.erp_cmd_msg.steer = -1 *(int((2000/20) * (math.degrees(steer_rad))))
#         self.erp_cmd_msg.gear = 0
#         self.erp_cmd_msg.brake = 0

#         self.cmd_pub.publish(self.erp_cmd_msg)
#         self.get_logger().info(f"theta={theta:.3f} rad, steer={math.degrees(steer_rad):.1f} deg")

#     # ========================
#     # Visualization helpers
#     # ========================
#     def publish_lookahead_visuals(self, theta: float):
#         # Marker (sphere) in vehicle_frame
#         m = Marker()
#         m.header.frame_id = 'vehicle_frame'   # /local_path가 vehicle_frame 기준이므로 동일 프레임
#         m.header.stamp = self.get_clock().now().to_msg()
#         m.ns = 'lookahead'
#         m.id = 0
#         m.type = Marker.SPHERE
#         m.action = Marker.ADD
#         m.pose.position.x = float(self.forward_point.x)
#         m.pose.position.y = float(self.forward_point.y)
#         m.pose.position.z = 0.0
#         m.pose.orientation.w = 1.0
#         m.scale.x = 0.5   # diameter
#         m.scale.y = 0.5
#         m.scale.z = 0.5
#         m.color.a = 1.0
#         m.color.r = 0.2
#         m.color.g = 0.0
#         m.color.b = 0.9
#         self.lookahead_marker_pub.publish(m)

#         # PoseStamped (arrow) — RViz 'Pose' 디스플레이에서 확인
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
#         # PoseStamped는 굳이 지울 필요 없음(새 값 나오면 갱신)

#     def publish_stop(self):
#         self.erp_cmd_msg.gear = 1
#         self.erp_cmd_msg.steer = 0
#         self.erp_cmd_msg.brake = 1
#         self.cmd_pub.publish(self.erp_cmd_msg)

#     def path_callback(self, msg):
#         self.path = msg
#         self.is_path = True

#     def status_callback(self, msg):
#         self.cur_speed = msg.speed
#         self.is_status = True


# def main(args=None):
#     rclpy.init(args=args)
#     node = PurePursuit()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()


# if __name__ == '__main__':
#     main()

