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

# MORAI UDP 통신을 위한 import
from EgoInfoReceiver import EgoInfoReceiver
from CtrlCmdSender import CtrlCmdSender


def near_zero(x: float, eps: float = 1e-6) -> bool:
    return abs(x) < eps


class MoraiPurePursuit(Node):
    def __init__(self):
        super().__init__('morai_pure_pursuit')

        # ================= 파라미터 =================
        # UDP 통신 설정
        self.declare_parameter('ego_info_host', '127.0.0.1')
        self.declare_parameter('ego_info_port', 9097)
        self.declare_parameter('ctrl_cmd_host', '127.0.0.1')
        self.declare_parameter('ctrl_cmd_port', 9095)

        # 단위/샘플링
        self.declare_parameter('control_dt', 0.1)           # timer 주기 [s]

        # 차량/조향
        self.declare_parameter('wheelbase', 1.82)
        self.declare_parameter('max_steer_deg', 20.0)           # ±조향 한계
        self.declare_parameter('max_steer_rate_deg_s', 150.0)   # ±조향 속도 한계

        # lookahead (속도 스케일)
        self.declare_parameter('lfd_gain', 2.0)  # lfd = gain * v(m/s)
        self.declare_parameter('lfd_min', 2.0)
        self.declare_parameter('lfd_max', 15.0)

        # 속도 커맨드 간단 로직 (0.0~1.0 범위)
        self.declare_parameter('accel_straight', 0.3)  # 직선 주행시 가속 페달
        self.declare_parameter('accel_turn', 0.1)      # 회전시 가속 페달
        self.declare_parameter('brake_stop', 0.8)      # 정지시 브레이크
        self.declare_parameter('turn_deg_threshold', 5.0)

        # (0,0) 첫 점 스킵 여부
        self.declare_parameter('skip_prepend_current', True)

        # 파라미터 가져오기
        self.ego_host = str(self.get_parameter('ego_info_host').value)
        self.ego_port = int(self.get_parameter('ego_info_port').value)
        self.ctrl_host = str(self.get_parameter('ctrl_cmd_host').value)
        self.ctrl_port = int(self.get_parameter('ctrl_cmd_port').value)

        self.dt = float(self.get_parameter('control_dt').value)

        self.L = float(self.get_parameter('wheelbase').value)
        self.max_steer_deg = float(self.get_parameter('max_steer_deg').value)
        self.max_steer_rate_deg_s = float(self.get_parameter('max_steer_rate_deg_s').value)

        self.lfd_gain = float(self.get_parameter('lfd_gain').value)
        self.lfd_min = float(self.get_parameter('lfd_min').value)
        self.lfd_max = float(self.get_parameter('lfd_max').value)

        self.accel_straight = float(self.get_parameter('accel_straight').value)
        self.accel_turn = float(self.get_parameter('accel_turn').value)
        self.brake_stop = float(self.get_parameter('brake_stop').value)
        self.turn_deg_threshold = float(self.get_parameter('turn_deg_threshold').value)

        self.skip_prepend_current = bool(self.get_parameter('skip_prepend_current').value)

        # ================= UDP 통신 설정 =================
        try:
            # EgoInfo 수신기 초기화
            self.ego_receiver = EgoInfoReceiver(self.ego_host, self.ego_port, self.ego_data_callback)
            self.get_logger().info(f"EgoInfo UDP receiver started: {self.ego_host}:{self.ego_port}")

            # CtrlCmd 송신기 초기화
            self.ctrl_sender = CtrlCmdSender(self.ctrl_host, self.ctrl_port)
            self.get_logger().info(f"CtrlCmd UDP sender started: {self.ctrl_host}:{self.ctrl_port}")

        except Exception as e:
            self.get_logger().error(f"UDP setup failed: {e}")
            return

        # ================= ROS2 Pub/Sub =================
        # Path 구독은 ROS2로 유지
        self.create_subscription(Path, '/local_path', self.path_callback, 10)

        # visualization
        self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
        self.lookahead_pose_pub   = self.create_publisher(PoseStamped, '/lookahead_pose', 10)

        # ================= 상태 =================
        self.is_path = False
        self.is_ego_status = False
        self.path = Path()

        # EgoInfo 데이터 저장
        self.cur_speed_ms = 0.0      # m/s로 내부 통일 (km/h -> m/s 변환)
        self.cur_pos_x = 0.0         # 현재 위치
        self.cur_pos_y = 0.0
        self.cur_yaw = 0.0           # 현재 헤딩
        self.ego_data_count = 0

        self.vehicle_length = self.L
        self.forward_point = Point()
        self._last_steer_deg = 0.0  # 레이트 제한용 메모리

        # 타이머 루프
        self.timer = self.create_timer(self.dt, self.timer_callback)

        self.get_logger().info(
            f"MORAI PurePursuit started. dt={self.dt}, "
            f"L={self.L}, max_steer={self.max_steer_deg}deg, rate={self.max_steer_rate_deg_s}deg/s"
        )

    # ================= UDP 콜백 =================
    def ego_data_callback(self, parsed_data):
        """EgoInfo UDP 데이터 수신 콜백"""
        if parsed_data and len(parsed_data) >= 25:
            try:
                # EgoInfoReceiver의 _parsed_data 순서에 따라 파싱
                ctrl_mode, gear, signed_vel, map_id, accel, brake = parsed_data[0:6]
                size_x, size_y, size_z, overhang, wheelbase, rear_overhang = parsed_data[6:12]
                pos_x, pos_y, pos_z = parsed_data[12:15]
                roll, pitch, yaw = parsed_data[15:18]
                vel_x, vel_y, vel_z = parsed_data[18:21]
                acc_x, acc_y, acc_z = parsed_data[21:24]
                steer = parsed_data[24]

                # 필요한 데이터만 저장
                if signed_vel is not None:
                    self.cur_speed_ms = float(signed_vel) * (1000.0 / 3600.0)  # km/h -> m/s
                if pos_x is not None and pos_y is not None:
                    self.cur_pos_x = float(pos_x)
                    self.cur_pos_y = float(pos_y)
                if yaw is not None:
                    self.cur_yaw = float(yaw)

                self.ego_data_count += 1
                self.is_ego_status = True

            except Exception as e:
                self.get_logger().warn(f"EgoInfo parsing error: {e}")
        else:
            self.is_ego_status = False

    # ================= ROS2 콜백 =================
    def path_callback(self, msg: Path):
        self.path = msg
        self.is_path = True

    def timer_callback(self):
        if not self.is_path or not self.is_ego_status:
            if not self.is_path:
                self.get_logger().throttle(2000, "[local_path] not received.")
            if not self.is_ego_status:
                self.get_logger().throttle(2000, "[ego_info] not received via UDP.")
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
        steer_rad = math.atan2(2.0 * self.vehicle_length * sin(theta), lfd)
        steer_deg = math.degrees(steer_rad)

        # 조향 한계
        steer_deg = float(np.clip(steer_deg, -self.max_steer_deg, self.max_steer_deg))

        # 5) 조향 레이트 제한 (deg/s)
        rate_limit = self.max_steer_rate_deg_s * self.dt
        d_deg = float(np.clip(steer_deg - self._last_steer_deg, -rate_limit, rate_limit))
        steer_deg_limited = self._last_steer_deg + d_deg
        self._last_steer_deg = steer_deg_limited

        # 6) 가속/브레이크 명령 (0.0~1.0 범위)
        if abs(steer_deg_limited) <= self.turn_deg_threshold:
            accel_cmd = self.accel_straight
        else:
            accel_cmd = self.accel_turn

        brake_cmd = 0.0  # 정상 주행시에는 브레이크 0

        # 7) UDP로 제어 명령 전송
        self.send_ctrl_cmd(accel_cmd, brake_cmd, math.radians(steer_deg_limited))

        # 8) 시각화
        self.publish_lookahead_visuals(theta)

        # 적당한 주기로 로그
        self.get_logger().throttle(
            1000,
            f"v={v:.2f}m/s, lfd={lfd:.2f}m, theta={theta:.3f}rad, "
            f"steer={steer_deg_limited:.1f}deg, accel={accel_cmd:.2f}"
        )

    # ================= UDP 통신 =================
    def send_ctrl_cmd(self, accel: float, brake: float, steering_rad: float):
        """MORAI에 제어 명령 전송"""
        try:
            # CtrlCmdSender의 format_data는 [accel, brake, steering] 순서
            ctrl_data = [accel, brake, steering_rad]
            self.ctrl_sender.send(ctrl_data)
        except Exception as e:
            self.get_logger().warn(f"Failed to send ctrl command: {e}")

    def publish_stop(self):
        """정지 명령 전송"""
        try:
            # 정지: 가속 0, 브레이크 최대, 조향 0
            ctrl_data = [0.0, self.brake_stop, 0.0]
            self.ctrl_sender.send(ctrl_data)
        except Exception as e:
            self.get_logger().warn(f"Failed to send stop command: {e}")

    # ================= 시각화 =================
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

    def __del__(self):
        """소멸자에서 UDP 연결 정리"""
        try:
            if hasattr(self, 'ego_receiver'):
                del self.ego_receiver
            if hasattr(self, 'ctrl_sender'):
                del self.ctrl_sender
        except:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = MoraiPurePursuit()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
