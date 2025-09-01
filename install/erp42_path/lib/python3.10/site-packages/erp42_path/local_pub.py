#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from math import cos, sin
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped, TransformStamped
from visualization_msgs.msg import Marker
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from tf2_ros import TransformBroadcaster


class PathPublisher(Node):
    def __init__(self):
        super().__init__('path_pub')

        # === 설정 ===
        self.LOOKAHEAD_PTS = 300      # 현재 위치에서 앞으로 뽑을 점 개수
        self.LATERAL_LIMIT = 10.0     # 좌우 제한 (옵션)
        self.WRAP = False             # 경로 끝에서 처음으로 래핑할지
        self.PREPEND_CURRENT = True   # 로컬 경로 첫 점에 "현재 위치"를 넣을지
        ###



        # 구독/퍼블리시
        self.create_subscription(Path, '/global_path', self.global_path_callback, 10)
        self.create_subscription(Odometry, '/odometry/local_enu', self.odom_callback, 10)

        self.local_path_pub = self.create_publisher(Path, '/local_path', 10)
        self.current_pos_marker_pub = self.create_publisher(Marker, '/current_position_marker', 10)

        self.tf_broadcaster = TransformBroadcaster(self)

        # 상태
        self.global_path_msg = Path()
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.is_status = False

        self.last_log_time = self.get_clock().now()

        # 20 Hz
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info('Path Publisher Node started.')

    # -------------------- 콜백 --------------------
    def timer_callback(self):
        if self.is_status:
            self.process_local_path()

    def global_path_callback(self, msg: Path):
        self.global_path_msg = msg
        self.is_status = True

    def odom_callback(self, msg: Odometry):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.yaw = yaw
        self.is_status = True

    # -------------------- 핵심 로직 --------------------
    def process_local_path(self):
        if not self.global_path_msg.poses:
            return

        x, y, yaw = self.x, self.y, self.yaw

        # (map -> vehicle_frame) TF 브로드캐스트
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

        # 현재 위치 마커
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = t.header.stamp
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
        marker.pose.orientation.x = quat[0]
        marker.pose.orientation.y = quat[1]
        marker.pose.orientation.z = quat[2]
        marker.pose.orientation.w = quat[3]
        self.current_pos_marker_pub.publish(marker)

        # 가장 가까운 글로벌 경로 인덱스
        start_idx = self.find_closest_index(x, y)
        poses = self.global_path_msg.poses
        N = len(poses)

        # 인덱스 목록 구성
        if self.WRAP:
            indices = [ (start_idx + k) % N for k in range(min(self.LOOKAHEAD_PTS, N)) ]
        else:
            end_idx = min(start_idx + self.LOOKAHEAD_PTS, N)
            indices = list(range(start_idx, end_idx))

        # 로컬 경로(차량 좌표계)
        local_path = Path()
        local_path.header.frame_id = 'vehicle_frame'
        local_path.header.stamp = t.header.stamp

        cos_m = cos(-yaw)
        sin_m = sin(-yaw)

        # 1) 첫 점을 "현재 위치"로 추가 -> RViz에서 현재 위치에서 경로가 시작
        if self.PREPEND_CURRENT:
            p0 = PoseStamped()
            p0.header.frame_id = local_path.header.frame_id
            p0.header.stamp = local_path.header.stamp
            p0.pose.position.x = 0.0  # vehicle_frame 기준 현재 위치
            p0.pose.position.y = 0.0
            p0.pose.position.z = 0.0
            p0.pose.orientation.w = 1.0
            local_path.poses.append(p0)

        # 2) 이후 점들은 글로벌 경로의 점들을 vehicle_frame으로 변환하여 추가
        for i in indices:
            wp = poses[i]
            dx = wp.pose.position.x - x
            dy = wp.pose.position.y - y

            # map -> vehicle_frame
            local_x = dx * cos_m - dy * sin_m
            local_y = dx * sin_m + dy * cos_m

            # 필요 시 필터
            # if local_x < 0.0: continue
            # if abs(local_y) > self.LATERAL_LIMIT: continue

            p = PoseStamped()
            p.header.frame_id = local_path.header.frame_id
            p.header.stamp = local_path.header.stamp
            p.pose.position.x = local_x
            p.pose.position.y = local_y
            p.pose.position.z = 0.0
            p.pose.orientation.w = 1.0
            local_path.poses.append(p)

        self.local_path_pub.publish(local_path)

    def find_closest_index(self, x: float, y: float) -> int:
        """현재 (x, y)에서 가장 가까운 글로벌 경로 인덱스"""
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


def main(args=None):
    rclpy.init(args=args)
    path_publisher = PathPublisher()
    try:
        rclpy.spin(path_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        path_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

