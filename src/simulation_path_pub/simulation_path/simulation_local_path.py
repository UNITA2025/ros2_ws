#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from math import sin, cos, atan2, tan
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped, TransformStamped, Quaternion
from visualization_msgs.msg import Marker
from tf_transformations import quaternion_from_euler
from tf2_ros import TransformBroadcaster


def quat_from_yaw(yaw: float) -> Quaternion:
    qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, yaw)
    q = Quaternion()
    q.x, q.y, q.z, q.w = qx, qy, qz, qw
    return q


def wrap_angle(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


class PathPubPurePursuit(Node):
    """
    /global_path(nav_msgs/Path)를 기준으로:
      - 차량 마커/TF를 Pure Pursuit로 로컬경로를 추종하게 시뮬레이션
      - /local_path는 '현재 차량 포즈 기준(vehicle_frame)'으로 생성
    GPS/IMU 없음.
    """
    def __init__(self):
        super().__init__('path_pub_pure_pursuit')

        # ===== 파라미터 =====
        self.declare_parameter('dt', 0.05)              # 시뮬 주기 [s]
        self.declare_parameter('sim_speed_mps', 6.0)    # 전진 속도 [m/s]
        self.declare_parameter('wheelbase', 1.82)       # L
        self.declare_parameter('max_steer_deg', 25.0)   # |delta| 제한
        self.declare_parameter('WRAP', False)           # 경로 래핑
        self.declare_parameter('stop_at_end', True)     # 끝에서 정지

        # Pure Pursuit 파라미터
        self.declare_parameter('lfd_mode', 'fixed')     # 'fixed' or 'speed_scaled'
        self.declare_parameter('lfd', 3.5)              # fixed 모드일 때 lookahead [m]
        self.declare_parameter('lfd_gain', 0.8)         # speed_scaled: lfd = clamp(gain*v, lfd_min, lfd_max)
        self.declare_parameter('lfd_min', 2.5)
        self.declare_parameter('lfd_max', 8.0)

        # 로컬경로
        self.declare_parameter('LOOKAHEAD_PTS', 300)
        self.declare_parameter('PREPEND_CURRENT', True)

        # 파라미터 적용
        self.dt   = float(self.get_parameter('dt').value)
        self.v    = float(self.get_parameter('sim_speed_mps').value)
        self.L    = float(self.get_parameter('wheelbase').value)
        self.delta_max = math.radians(float(self.get_parameter('max_steer_deg').value))
        self.WRAP = bool(self.get_parameter('WRAP').value)
        self.stop_at_end = bool(self.get_parameter('stop_at_end').value)

        self.lfd_mode = str(self.get_parameter('lfd_mode').value).lower()
        self.lfd_fix  = float(self.get_parameter('lfd').value)
        self.lfd_gain = float(self.get_parameter('lfd_gain').value)
        self.lfd_min  = float(self.get_parameter('lfd_min').value)
        self.lfd_max  = float(self.get_parameter('lfd_max').value)

        self.LOOKAHEAD_PTS   = int(self.get_parameter('LOOKAHEAD_PTS').value)
        self.PREPEND_CURRENT = bool(self.get_parameter('PREPEND_CURRENT').value)

        # ===== 토픽 IO =====
        self.create_subscription(Path, '/global_path', self.global_path_callback, 10)
        self.local_path_pub = self.create_publisher(Path, '/local_path', 10)
        self.marker_pub     = self.create_publisher(Marker, '/vehicle_marker', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # ===== 내부 상태 =====
        self.global_path_msg = Path()
        self.have_path = False
        self.sim_initialized = False
        self.sim_reached_end = False

        # 차량 상태
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.last_time: Optional[Time] = None

        # 타이머
        self.timer = self.create_timer(self.dt, self.timer_callback)
        self.get_logger().info('Pure Pursuit SIM started.')

    # --------- 콜백 ---------
    def global_path_callback(self, msg: Path):
        # 옵션 A: 처음 들어올 때만 초기화
        first_time = not self.have_path
        self.global_path_msg = msg
        self.have_path = True
        if first_time:
            self.sim_initialized = False
            self.sim_reached_end = False
            self.get_logger().info(f'Received global_path with {len(msg.poses)} points.')

    # --------- 타이머 루프 ---------
    def timer_callback(self):
        now = self.get_clock().now()
        if not self.have_path or not self.global_path_msg.poses:
            return

        if not self.sim_initialized:
            self._init_from_path()
            self.last_time = now
            self.sim_initialized = True

        # ===== Pure Pursuit 조향 계산 =====
        lfd = self._compute_lfd(self.v)
        tgt_idx, tgt = self._find_target_point(lfd)

        if tgt is None:
            # 경로 없음/이상 → 정지 출력만
            self._publish_tf_and_marker(now)
            self._publish_local_path(now)
            return

        # 차량 좌표계에서 타겟 좌표
        dx = tgt.x - self.x
        dy = tgt.y - self.y
        cos_m = cos(-self.yaw)
        sin_m = sin(-self.yaw)
        x_local = dx * cos_m - dy * sin_m
        y_local = dx * sin_m + dy * cos_m

        # 순수 추종: delta = atan2(2L * y_local / lfd^2, 1)
        ld2 = max(lfd * lfd, 1e-6)
        delta = atan2(2.0 * self.L * y_local, ld2)
        # 조향 한계
        delta = max(-self.delta_max, min(self.delta_max, delta))

        # ===== 상태 적분 =====
        self.x   += self.v * cos(self.yaw) * self.dt
        self.y   += self.v * sin(self.yaw) * self.dt
        self.yaw  = wrap_angle(self.yaw + (self.v / self.L) * tan(delta) * self.dt)

        # 끝 처리
        if (not self.WRAP) and self.stop_at_end and (tgt_idx >= len(self.global_path_msg.poses) - 1):
            dist = math.hypot(
                self.global_path_msg.poses[-1].pose.position.x - self.x,
                self.global_path_msg.poses[-1].pose.position.y - self.y
            )
            if dist < 0.5:
                self.sim_reached_end = True
                self.get_logger().info('Reached end of global_path. Stopping (PP SIM).')

        # ===== 퍼블리시 =====
        self._publish_tf_and_marker(now)
        self._publish_local_path(now)

    # --------- 유틸 ---------
    def _init_from_path(self):
        p0 = self.global_path_msg.poses[0].pose
        self.x = p0.position.x
        self.y = p0.position.y
        if len(self.global_path_msg.poses) >= 2:
            p1 = self.global_path_msg.poses[1].pose
            self.yaw = math.atan2(p1.position.y - self.y, p1.position.x - self.x)
        else:
            self.yaw = 0.0
        self.get_logger().info(f'Init pose: x={self.x:.2f}, y={self.y:.2f}, yaw={math.degrees(self.yaw):.1f}°')

    def _compute_lfd(self, v: float) -> float:
        if self.lfd_mode == 'speed_scaled':
            return max(self.lfd_min, min(self.lfd_gain * v, self.lfd_max))
        return self.lfd_fix

    def _closest_index(self, x: float, y: float) -> int:
        min_ds, idx = float('inf'), 0
        for i, wp in enumerate(self.global_path_msg.poses):
            dx = wp.pose.position.x - x
            dy = wp.pose.position.y - y
            ds = dx*dx + dy*dy
            if ds < min_ds:
                min_ds, idx = ds, i
        return idx

    def _find_target_point(self, lookahead: float):
        """현재 위치에서 누적호(arc) 거리로 lookahead 넘는 첫 점을 타겟으로"""
        poses = self.global_path_msg.poses
        N = len(poses)
        if N == 0:
            return None, None

        start_idx = self._closest_index(self.x, self.y)

        acc = 0.0
        last_x, last_y = self.x, self.y
        for k in range(self.LOOKAHEAD_PTS):
            i = (start_idx + k) % N if self.WRAP else min(start_idx + k, N - 1)
            wp = poses[i].pose.position
            ds = math.hypot(wp.x - last_x, wp.y - last_y)
            acc += ds
            last_x, last_y = wp.x, wp.y
            if acc >= lookahead:
                return i, wp

        # 못 찾으면 마지막 점 반환
        return (N - 1), poses[-1].pose.position

    # --------- 퍼블리시 ---------
    def _publish_tf_and_marker(self, now: Time):
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
        self.tf_broadcaster.sendTransform(t)

        # 차량 마커
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = t.header.stamp
        marker.ns = 'vehicle'
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = self.x
        marker.pose.position.y = self.y
        marker.pose.position.z = 0.0
        marker.scale.x = 0.9
        marker.scale.y = 0.5
        marker.scale.z = 0.3
        marker.color.a = 1.0
        marker.color.b = 1.0
        marker.pose.orientation = quat_from_yaw(self.yaw)
        self.marker_pub.publish(marker)

    def _publish_local_path(self, now: Time):
        """현재 차량 포즈 기준(vehicle_frame) 로컬경로 생성"""
        if not self.global_path_msg.poses:
            return

        idx = self._closest_index(self.x, self.y)
        poses = self.global_path_msg.poses
        N = len(poses)

        if self.WRAP:
            indices = [(idx + k) % N for k in range(min(self.LOOKAHEAD_PTS, N))]
        else:
            indices = list(range(idx, min(idx + self.LOOKAHEAD_PTS, N)))

        path = Path()
        path.header.frame_id = 'vehicle_frame'
        path.header.stamp = now.to_msg()

        cos_m, sin_m = cos(-self.yaw), sin(-self.yaw)

        # (옵션) 현재 위치를 맨 앞에 추가
        if self.PREPEND_CURRENT:
            p0 = PoseStamped()
            p0.header = path.header
            p0.pose.position.x = 0.0
            p0.pose.position.y = 0.0
            p0.pose.orientation.w = 1.0
            path.poses.append(p0)

        for i in indices:
            wp = poses[i].pose.position
            dx, dy = wp.x - self.x, wp.y - self.y
            lx = dx * cos_m - dy * sin_m
            ly = dx * sin_m + dy * cos_m
            ps = PoseStamped()
            ps.header = path.header
            ps.pose.position.x = lx
            ps.pose.position.y = ly
            ps.pose.orientation.w = 1.0
            path.poses.append(ps)

        self.local_path_pub.publish(path)


def main(args=None):
    rclpy.init(args=args)
    node = PathPubPurePursuit()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
