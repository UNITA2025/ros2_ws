#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from math import atan2, sin, cos
from typing import List, Optional, Dict

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.time import Time

from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped, TransformStamped, Quaternion
from visualization_msgs.msg import Marker
from std_msgs.msg import Float32
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from tf2_ros import TransformBroadcaster


def quat_from_yaw(yaw: float) -> Quaternion:
    qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, yaw)
    q = Quaternion()
    q.x, q.y, q.z, q.w = qx, qy, qz, qw
    return q


def near_zero(x: float, eps: float = 1e-6) -> bool:
    return abs(x) < eps


class MarkerControl(Node):
    """
    /odometry/local_enu 로 현재 포즈를 받고,
    /local_path(vehicle_frame) 를 따라갈 순수추종(Pure Pursuit) 조향각을 계산.
    ERP 명령 발행 없음. TF/마커/룩어헤드 시각화 + 디버그 토픽만 퍼블리시.
    """

    def __init__(self):
        super().__init__('marker_control')

        # ===== 파라미터 =====
        self.declare_parameter('wheelbase', 1.82)
        self.declare_parameter('max_steer_deg', 20.0)
        self.declare_parameter('lfd_gain', 2.0)     # lfd = gain * v(m/s)
        self.declare_parameter('lfd_min', 2.0)
        self.declare_parameter('lfd_max', 15.0)
        self.declare_parameter('use_odom_speed', True)
        self.declare_parameter('fixed_speed_mps', 5.0)
        self.declare_parameter('skip_prepend_current', True)

        self.L = float(self.get_parameter('wheelbase').value)
        self.max_steer_deg = float(self.get_parameter('max_steer_deg').value)
        self.lfd_gain = float(self.get_parameter('lfd_gain').value)
        self.lfd_min = float(self.get_parameter('lfd_min').value)
        self.lfd_max = float(self.get_parameter('lfd_max').value)
        self.use_odom_speed = bool(self.get_parameter('use_odom_speed').value)
        self.fixed_speed_mps = float(self.get_parameter('fixed_speed_mps').value)
        self.skip_prepend_current = bool(self.get_parameter('skip_prepend_current').value)

        # ===== 구독/퍼블리시 =====
        self.create_subscription(Odometry, '/odometry/local_enu', self.odom_cb, 10)
        self.create_subscription(Path, '/local_path', self.path_cb, 10)

        self.tf_brd = TransformBroadcaster(self)
        self.marker_pub = self.create_publisher(Marker, '/marker_control/vehicle_marker', 10)
        self.heading_pub = self.create_publisher(Marker, '/marker_control/heading_arrow', 10)
        self.lookahead_marker_pub = self.create_publisher(Marker, '/marker_control/lookahead_marker', 10)
        self.lookahead_pose_pub = self.create_publisher(PoseStamped, '/marker_control/lookahead_pose', 10)
        self.steer_deg_pub = self.create_publisher(Float32, '/marker_control/steer_deg', 10)
        self.lfd_pub = self.create_publisher(Float32, '/marker_control/lfd', 10)

        # ===== 내부 상태 =====
        self.have_odom = False
        self.have_path = False
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.vx = 0.0  # m/s
        self.path: Path = Path()
        self.forward_point = None  # vehicle_frame 좌표계

        # logger throttle용
        self._last_log_ns: Dict[str, int] = {}

        # 타이머
        self.timer = self.create_timer(0.05, self.timer_cb)
        self.get_logger().info("marker_control started.")

    # ===== 쓰로틀 로깅 (rclpy에는 throttle 없음) =====
    def _log_throttle(self, key: str, period_sec: float, level: str, msg: str):
        now_ns = self.get_clock().now().nanoseconds
        last = self._last_log_ns.get(key, 0)
        if now_ns - last >= int(period_sec * 1e9):
            if level == 'warn':
                self.get_logger().warn(msg)
            elif level == 'error':
                self.get_logger().error(msg)
            else:
                self.get_logger().info(msg)
            self._last_log_ns[key] = now_ns

    # ===== 콜백 =====
    def odom_cb(self, msg: Odometry):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.get_logger().info(f"self.x : {self.x}.")
        q = msg.pose.pose.orientation
        _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.yaw = yaw
        self.vx = float(msg.twist.twist.linear.x) if self.use_odom_speed else self.fixed_speed_mps
        self.have_odom = True

    def path_cb(self, msg: Path):
        self.path = msg
        self.have_path = True

    # ===== 메인 루프 =====
    def timer_cb(self):
        if not self.have_odom:
            self._log_throttle("no_odom", 2.0, 'warn', "[odom] not received.")
            return
        if not self.have_path or not self.path.poses:
            self._log_throttle("no_path", 2.0, 'warn', "[local_path] not received or empty.")
            # 그래도 현재 포즈는 시각화
            now = self.get_clock().now()
            self.publish_tf_and_vehicle(now)
            return

        now = self.get_clock().now()
        self.publish_tf_and_vehicle(now)

        # lookahead
        v = max(0.0, float(self.vx))
        lfd = float(np.clip(self.lfd_gain * v, self.lfd_min, self.lfd_max))
        self.lfd_pub.publish(Float32(data=lfd))

        # 후보 경로 (vehicle_frame)
        poses_iter: List[PoseStamped] = self.path.poses
        if self.skip_prepend_current and len(poses_iter) > 0:
            p0 = poses_iter[0].pose.position
            if near_zero(p0.x) and near_zero(p0.y):
                poses_iter = poses_iter[1:]

        target = self.find_target_by_arclength(poses_iter, lfd)
        if target is None:
            self.clear_lookahead_visuals()
            self._log_throttle("no_lookahead", 1.5, 'warn', "Lookahead not found.")
            return

        self.forward_point = target

        # 조향각(시각화/로그만)
        theta = math.atan2(self.forward_point.y, self.forward_point.x)
        steer_rad = math.atan2(2.0 * self.L * math.sin(theta), lfd)
        steer_deg = float(np.clip(math.degrees(steer_rad), -self.max_steer_deg, self.max_steer_deg))
        self.steer_deg_pub.publish(Float32(data=steer_deg))

        self.publish_lookahead_visuals(now, theta)
        self._log_throttle("status", 1.0, 'info',
                           f"v={v:.2f} m/s, lfd={lfd:.2f} m, theta={theta:.3f} rad, steer={steer_deg:.1f} deg")

    # ===== 유틸 =====
    def find_target_by_arclength(self, poses: List[PoseStamped], lfd: float):
        if not poses:
            return None
        acc = 0.0
        last_x, last_y = 0.0, 0.0  # vehicle_frame에서 현재 위치는 (0,0)
        for ps in poses:
            dx = ps.pose.position.x - last_x
            dy = ps.pose.position.y - last_y
            acc += math.hypot(dx, dy)
            last_x, last_y = ps.pose.position.x, ps.pose.position.y
            if acc >= lfd:
                return ps.pose.position
        return None

    def publish_tf_and_vehicle(self, now: Time):
        # TF map->vehicle_frame
        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'vehicle_frame'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, self.yaw)
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_brd.sendTransform(t)

        # 차량 마커 (map)
        m = Marker()
        m.header.frame_id = 'map'
        m.header.stamp = t.header.stamp
        m.ns = 'vehicle'
        m.id = 0
        m.type = Marker.CUBE
        m.action = Marker.ADD
        m.pose.position.x = self.x
        m.pose.position.y = self.y
        m.pose.position.z = 0.0
        m.pose.orientation = quat_from_yaw(self.yaw)
        m.scale.x = 0.9
        m.scale.y = 0.5
        m.scale.z = 0.3
        m.color.a = 1.0
        m.color.b = 1.0
        self.marker_pub.publish(m)

        # 진행 화살표 (map)
        arrow = Marker()
        arrow.header.frame_id = 'map'
        arrow.header.stamp = t.header.stamp
        arrow.ns = 'heading'
        arrow.id = 1
        arrow.type = Marker.ARROW
        arrow.action = Marker.ADD
        arrow.pose.position.x = self.x
        arrow.pose.position.y = self.y
        arrow.pose.position.z = 0.1
        arrow.pose.orientation = quat_from_yaw(self.yaw)
        arrow.scale.x = 1.2
        arrow.scale.y = 0.12
        arrow.scale.z = 0.12
        arrow.color.a = 0.9
        arrow.color.r = 1.0
        arrow.color.g = 0.5
        arrow.color.b = 0.0
        self.heading_pub.publish(arrow)

    def publish_lookahead_visuals(self, now: Time, theta: float):
        if self.forward_point is None:
            self.clear_lookahead_visuals()
            return

        m = Marker()
        m.header.frame_id = 'vehicle_frame'
        m.header.stamp = now.to_msg()
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
    node = MarkerControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
