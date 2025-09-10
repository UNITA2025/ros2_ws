#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from math import atan2, sin
from typing import List
import struct
import socket

import numpy as np
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker
from tf_transformations import quaternion_from_euler

from interfaces_control_pkg.msg import ErpStatusMsg


def near_zero(x: float, eps: float = 1e-6) -> bool:
    return abs(x) < eps


class PurePursuitUDP(Node):
    def __init__(self):
        super().__init__('pure_pursuit_udp')

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

        # (0,0) 첫 점 스킵 여부
        self.declare_parameter('skip_prepend_current', True)

        # UDP 제어 명령 전송 설정
        self.declare_parameter('udp_control_host', '127.0.0.1')
        self.declare_parameter('udp_control_port', 9091)

        # 속도 제어 설정
        self.declare_parameter('throttle_straight', 0.3)    # 직진 시 throttle (0.0~1.0)
        self.declare_parameter('throttle_turn', 0.2)        # 회전 시 throttle (0.0~1.0)
        self.declare_parameter('turn_deg_threshold', 5.0)   # 회전 판단 임계값 [deg]

        # 파라미터 가져오기
        self.speed_unit = str(self.get_parameter('status_speed_unit').value).lower()
        self.dt = float(self.get_parameter('control_dt').value)

        self.L = float(self.get_parameter('wheelbase').value)
        self.max_steer_deg = float(self.get_parameter('max_steer_deg').value)
        self.max_steer_rate_deg_s = float(self.get_parameter('max_steer_rate_deg_s').value)

        self.lfd_gain = float(self.get_parameter('lfd_gain').value)
        self.lfd_min = float(self.get_parameter('lfd_min').value)
        self.lfd_max = float(self.get_parameter('lfd_max').value)

        self.skip_prepend_current = bool(self.get_parameter('skip_prepend_current').value)

        # UDP 설정
        self.udp_host = str(self.get_parameter('udp_control_host').value)
        self.udp_port = int(self.get_parameter('udp_control_port').value)

        # 속도 제어 설정
        self.throttle_straight = float(self.get_parameter('throttle_straight').value)
        self.throttle_turn = float(self.get_parameter('throttle_turn').value)
        self.turn_deg_threshold = float(self.get_parameter('turn_deg_threshold').value)

        # ================= Pub/Sub =================
        # ROS2 토픽 발행 제거 - 구독만 유지
        self.create_subscription(Path, '/local_path', self.path_callback, 10)
        self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)

        # visualization (옵션 - 필요시 제거 가능)
        self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
        self.lookahead_pose_pub   = self.create_publisher(PoseStamped, '/lookahead_pose', 10)

        # ================= UDP 제어 설정 =================
        self.setup_udp_control()

        # ================= 상태 =================
        self.is_path = False
        self.is_status = False
        self.path = Path()

        self.cur_speed_ms = 0.0  # m/s로 내부 통일
        self.vehicle_length = self.L

        self.forward_point = Point()
        self._last_steer_deg = 0.0  # 레이트 제한용 메모리

        # 타이머 루프
        self.timer = self.create_timer(self.dt, self.timer_callback)

        self.get_logger().info(
            f"PurePursuit UDP Control started. dt={self.dt}, "
            f"L={self.L}, max_steer={self.max_steer_deg}deg, "
            f"UDP: {self.udp_host}:{self.udp_port}"
        )

    def setup_udp_control(self):
        """UDP 제어 명령 전송 설정"""
        try:
            # UDP 소켓 생성
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # MORAI 제어 명령 헤더 설정
            message_name = '#MoraiCtrlCmd$'.encode()
            data_length = struct.pack('i', 23)
            aux_data = struct.pack('iii', 0, 0, 0)
            self.ctrl_header = message_name + data_length + aux_data
            self.ctrl_tail = '\r\n'.encode()
            
            self.get_logger().info("UDP control socket initialized")
        except Exception as e:
            self.get_logger().error(f"Failed to setup UDP control: {e}")
            raise

    def send_udp_control(self, throttle=0.0, brake=0.0, steering=0.0, cmd_type=1, velocity=0.0, acceleration=0.0):
        """UDP로 제어 명령 전송"""
        try:
            # 제어 데이터 패킹
            mode = struct.pack('b', 2)  # AutoMode
            gear = struct.pack('b', 4)  # Drive
            cmd_type_packed = struct.pack('b', cmd_type)
            velocity_packed = struct.pack('f', velocity)
            acceleration_packed = struct.pack('f', acceleration)
            throttle_packed = struct.pack('f', throttle)
            brake_packed = struct.pack('f', brake)
            steering_packed = struct.pack('f', steering)
            
            message = (mode + gear + cmd_type_packed + velocity_packed + 
                      acceleration_packed + throttle_packed + brake_packed + steering_packed)
            
            formatted_data = self.ctrl_header + message + self.ctrl_tail
            
            # UDP 전송
            self.udp_socket.sendto(formatted_data, (self.udp_host, self.udp_port))
            return True
            
        except Exception as e:
            self.get_logger().error(f"UDP control send failed: {e}")
            return False

    def send_stop_command(self):
        """정지 명령 전송"""
        return self.send_udp_control(
            throttle=0.0,
            brake=1.0,
            steering=0.0,
            cmd_type=1
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
            self.send_stop_command()
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
            self.send_stop_command()
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
            self.send_stop_command()
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

        # 6) 제어 명령 계산
        # 조향: -1.0 ~ 1.0 범위로 정규화
        steering_normalized = steer_deg_limited / self.max_steer_deg
        steering_normalized = float(np.clip(steering_normalized, -1.0, 1.0))
        
        # 속도: 조향각에 따라 throttle 결정
        if abs(steer_deg_limited) <= self.turn_deg_threshold:
            throttle = self.throttle_straight
        else:
            throttle = self.throttle_turn

        # 7) UDP 제어 명령 전송
        success = self.send_udp_control(
            throttle=throttle,
            brake=0.0,
            steering=steering_normalized,
            cmd_type=1  # Throttle mode
        )

        # 8) 시각화 (옵션)
        self.publish_lookahead_visuals(theta)

        # 로그 출력
        if success:
            self.get_logger().throttle(
                1000,
                f"v={v:.2f}m/s, lfd={lfd:.2f}m, theta={theta:.3f}rad, "
                f"steer={steer_deg_limited:.1f}deg, throttle={throttle:.2f}, "
                f"steering_cmd={steering_normalized:.3f}"
            )
        else:
            self.get_logger().warn("UDP command send failed")

    # ================= 시각화 (옵션) =================
    def publish_lookahead_visuals(self, theta: float):
        """lookahead 목표점 시각화 (필요시 제거 가능)"""
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

    def destroy_node(self):
        """노드 종료 시 UDP 소켓 정리"""
        if hasattr(self, 'udp_socket'):
            self.udp_socket.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PurePursuitUDP()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()