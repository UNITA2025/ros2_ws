#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
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

# --- 소켓 수신/송신 클래스 (네가 준 구현 사용) ---
# from .receiver import Receiver
# from .sender import Sender
import struct
from abc import ABCMeta, abstractmethod
import socket
import threading


class Receiver(metaclass=ABCMeta):
    def __init__(self, ip, port, callback):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))

        self._callback = callback

        self._parsed_data = []

        threading.Thread(target=self._receive_data, daemon=True).start()

    def __del__(self):
        self.sock.close()

    @property
    def parsed_data(self):
        return self._parsed_data

    def _receive_data(self):
        while True:
            data_size = 65535
            raw_data, _ = self.sock.recvfrom(data_size)
            self._parse_data(raw_data)
            self._callback(self._parsed_data)

    @abstractmethod
    def _parse_data(self, raw_data):
        pass


class Sender(metaclass=ABCMeta):
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (ip, port)

    def send_data(self, data):
        formatted_data = self._format_data(data)
        self.sock.sendto(formatted_data, self.address)

    @abstractmethod
    def _format_data(self, data):
        pass

class EgoInfoReceiver(Receiver):
    def __init__(self, ip, port, callback):
        super().__init__(ip, port, callback)
        self.header = '#MoraiInfo$'
        self.data_length = 132 # 버전마다 다름
        

    def _parse_data(self, raw_data):
        if self.header == raw_data[0:11].decode() and self.data_length == struct.unpack('i', raw_data[11:15])[0]:
            secs = struct.unpack('f', raw_data[27:31])[0]
            nsecs = struct.unpack('f', raw_data[31:35])[0]
            ctrl_mode = struct.unpack('b', raw_data[35:36])[0]
            gear = struct.unpack('b', raw_data[36:37])[0]
            signed_vel = struct.unpack('f', raw_data[37:41])[0]   # km/h
            map_id = struct.unpack('i', raw_data[41:45])[0]
            accel = struct.unpack('f', raw_data[45:49])[0]
            brake = struct.unpack('f', raw_data[49:53])[0]
            size_x, size_y, size_z = struct.unpack('fff', raw_data[53:65])
            overhang, wheelbase, rear_overhang = struct.unpack('fff', raw_data[65:77])
            pos_x, pos_y, pos_z = struct.unpack('fff', raw_data[77:89])
            roll, pitch, yaw = struct.unpack('fff', raw_data[89:101])
            vel_x, vel_y, vel_z = struct.unpack('fff', raw_data[101:113])
            ang_vel_x, ang_vel_y, ang_vel_z = struct.unpack('fff', raw_data[113:125])
            acc_x, acc_y, acc_z = struct.unpack('fff', raw_data[125:137])
            steer = struct.unpack('f', raw_data[137:141])[0]
            link_id = raw_data[141:179].decode(errors='ignore')
            self._parsed_data = [
                ctrl_mode, gear, signed_vel, map_id, accel, brake, size_x, size_y, size_z, overhang, wheelbase,
                rear_overhang, pos_x, pos_y, pos_z, roll, pitch, yaw, vel_x, vel_y, vel_z, acc_x, acc_y, acc_z, steer
            ]
        else:
            self._parsed_data = []


class CtrlCmdSender(Sender):
    """네가 준 그대로 (cmd_type=1 Throttle 모드)"""
    def __init__(self, ip, port):
        super().__init__(ip, port)
        message_name = '#MoraiCtrlCmd$'.encode()
        data_length = struct.pack('i', 23)
        aux_data = struct.pack('iii', 0, 0, 0)
        self.header = message_name + data_length + aux_data
        self.tail = '\r\n'.encode()

    def _format_data(self, data):
        # data: [accel, brake, steering]
        mode = struct.pack('b', 2)      # 1: KeyBoard / 2: AutoMode
        gear = struct.pack('b', 4)      # 1: Parking / 2: Reverse / 3: Neutral / 4: Drive
        cmd_type = struct.pack('b', 1)  # 1: Throttle  /  2: Velocity  /  3: Acceleration
        velocity = struct.pack('f', 0.0)      # cmd_type=2 때 사용 km/h
        acceleration = struct.pack('f', 0.0)  # cmd_type=3 때 사용 km/h

        accel = struct.pack('f', float(data[0])) #0 ~ 1 cmd_type=1 때 사용
        brake = struct.pack('f', float(data[1])) #0 ~ 1
        steering = struct.pack('f', float(data[2]))  # 일반적으로 -1.0~1.0 정규화
        message = mode + gear + cmd_type + velocity + acceleration + accel + brake + steering
        formatted_data = self.header + message + self.tail
        return formatted_data


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

        # UDP 엔드포인트
        self.declare_parameter('udp_status_host', '127.0.0.1')  # MORAI → 나(수신)
        self.declare_parameter('udp_status_port', 9094)
        self.declare_parameter('udp_control_host', '127.0.0.1')  # 나(송신) → MORAI
        self.declare_parameter('udp_control_port', 9091)

        # 스로틀 간단 로직
        self.declare_parameter('throttle_straight', 0.30)  # 0~1
        self.declare_parameter('throttle_turn', 0.20)
        self.declare_parameter('turn_deg_threshold', 5.0)  # [deg]

        # -------- 파라미터 로드 --------
        self.speed_unit = str(self.get_parameter('status_speed_unit').value).lower()
        self.dt = float(self.get_parameter('control_dt').value)

        self.L = float(self.get_parameter('wheelbase').value)
        self.max_steer_deg = float(self.get_parameter('max_steer_deg').value)
        self.max_steer_rate_deg_s = float(self.get_parameter('max_steer_rate_deg_s').value)

        self.lfd_gain = float(self.get_parameter('lfd_gain').value)
        self.lfd_min = float(self.get_parameter('lfd_min').value)
        self.lfd_max = float(self.get_parameter('lfd_max').value)

        self.skip_prepend_current = bool(self.get_parameter('skip_prepend_current').value)

        self.udp_status_host = str(self.get_parameter('udp_status_host').value)
        self.udp_status_port = int(self.get_parameter('udp_status_port').value)
        self.udp_control_host = str(self.get_parameter('udp_control_host').value)
        self.udp_control_port = int(self.get_parameter('udp_control_port').value)

        self.throttle_straight = float(self.get_parameter('throttle_straight').value)
        self.throttle_turn = float(self.get_parameter('throttle_turn').value)
        self.turn_deg_threshold = float(self.get_parameter('turn_deg_threshold').value)

        # ================= Pub/Sub =================
        self.create_subscription(Path, '/local_path', self.path_callback, 10)

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

        # 로그 쓰로틀용
        self._last_log_sec = 0.0

        # ================= UDP 설정 =================
        # 상태 수신기
        self.ego_info_receiver = EgoInfoReceiver(
            self.udp_status_host,
            self.udp_status_port,
            self.ego_info_callback
        )
        if hasattr(self.ego_info_receiver, 'start'):
            self.ego_info_receiver.start()

        # 제어 송신기
        self.ctrl_sender = CtrlCmdSender(
            self.udp_control_host,
            self.udp_control_port
        )

        # 타이머 루프
        self.timer = self.create_timer(self.dt, self.timer_callback)

        self.get_logger().info(
            f"PurePursuit UDP started. dt={self.dt:.3f}, L={self.L}, "
            f"status UDP bind {self.udp_status_host}:{self.udp_status_port}, "
            f"control UDP dst {self.udp_control_host}:{self.udp_control_port}"
        )

    # ================= 콜백 =================
    def path_callback(self, msg: Path):
        self.path = msg
        self.is_path = True

    def ego_info_callback(self, parsed_list):
        """EgoInfoReceiver → 속도 업데이트"""
        if len(parsed_list) >= 3:
            speed_kmh = float(parsed_list[2])  # index 2 = signed_vel(km/h)
            self.cur_speed_ms = speed_kmh * (1000.0 / 3600.0) if self.speed_unit == 'kmh' else float(parsed_list[2])
            self.is_status = True

    # ================= 타이머 =================
    def timer_callback(self):
        # 소켓 수신 한 번 (non-blocking)
        if hasattr(self.ego_info_receiver, 'receive_once'):
            self.ego_info_receiver.receive_once()

        if not self.is_path or not self.is_status:
            # 상태/경로 둘 중 하나라도 없으면 대기
            return

        self.pure_pursuit_control()

    # ================= 제어 로직 =================
    def pure_pursuit_control(self):
        v = max(0.0, self.cur_speed_ms)  # m/s
        lfd = float(np.clip(self.lfd_gain * v, self.lfd_min, self.lfd_max))

        poses: List[PoseStamped] = self.path.poses
        if len(poses) == 0:
            self.publish_stop()
            self.clear_lookahead_visuals()
            return

        # (0,0) 첫 점 스킵
        if self.skip_prepend_current and len(poses) > 0:
            p0 = poses[0].pose.position
            poses_iter = poses[1:] if near_zero(p0.x) and near_zero(p0.y) else poses
        else:
            poses_iter = poses

        if len(poses_iter) == 0:
            self.publish_stop()
            self.clear_lookahead_visuals()
            return

        # 호길이 기반 lookahead
        acc_len = 0.0
        last_x, last_y = 0.0, 0.0
        target_found = False
        for pose in poses_iter:
            dx = pose.pose.position.x - last_x
            dy = pose.pose.position.y - last_y
            acc_len += math.hypot(dx, dy)
            last_x, last_y = pose.pose.position.x, pose.pose.position.y
            if acc_len >= lfd:
                self.forward_point = pose.pose.position
                target_found = True
                break

        if not target_found:
            end = poses_iter[-1].pose.position
            close_enough = math.hypot(end.x, end.y) < 0.7
            if close_enough:
                self._log_throttled("Reached end of path → stop.")
            else:
                self._log_throttled("Lookahead not found → stop.")
            self.publish_stop()
            self.clear_lookahead_visuals()
            return

        # Pure Pursuit 조향
        theta = atan2(self.forward_point.y, self.forward_point.x)
        steer_rad = math.atan2(2.0 * self.vehicle_length * sin(theta), lfd)
        steer_deg = math.degrees(steer_rad)
        steer_deg = float(np.clip(steer_deg, -self.max_steer_deg, self.max_steer_deg))

        # 레이트 제한
        rate_limit = self.max_steer_rate_deg_s * self.dt
        d_deg = float(np.clip(steer_deg - self._last_steer_deg, -rate_limit, rate_limit))
        steer_deg_limited = self._last_steer_deg + d_deg
        self._last_steer_deg = steer_deg_limited

        # UDP 조향: -1.0 ~ 1.0 정규화
        steering_cmd = float(np.clip(steer_deg_limited / self.max_steer_deg, -1.0, 1.0))

        # 스로틀 결정
        throttle = self.throttle_straight if abs(steer_deg_limited) <= self.turn_deg_threshold else self.throttle_turn
        brake = 0.0

        # 전송
        self.send_udp_control(throttle, brake, steering_cmd)

        # 시각화
        self.publish_lookahead_visuals(theta)

        self._log_throttled(
            f"v={v:.2f}m/s, lfd={lfd:.2f}m, theta={theta:.3f}rad, "
            f"steer={steer_deg_limited:.1f}deg, throttle={throttle:.2f}, steering_cmd={steering_cmd:.3f}"
        )

    # ================= UDP 전송/정지 =================
    def send_udp_control(self, throttle: float, brake: float, steering_norm: float):
        try:
            # Sender는 내부에서 _format_data 호출한다고 가정
            self.ctrl_sender.send([throttle, brake, steering_norm])
        except Exception as e:
            self._log_throttled(f"UDP control send failed: {e}")

    def publish_stop(self):
        try:
            self.ctrl_sender.send([0.0, 1.0, 0.0])  # full brake
        except Exception:
            pass

    # ================= 시각화 =================
    def publish_lookahead_visuals(self, theta: float):
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
        m.scale.x = m.scale.y = m.scale.z = 0.5
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
        ps.pose.orientation.x, ps.pose.orientation.y, ps.pose.orientation.z, ps.pose.orientation.w = q
        self.lookahead_pose_pub.publish(ps)

    def clear_lookahead_visuals(self):
        m = Marker()
        m.header.frame_id = 'vehicle_frame'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'lookahead'
        m.id = 0
        m.action = Marker.DELETE
        self.lookahead_marker_pub.publish(m)

    # ================= 유틸 =================
    def _log_throttled(self, msg: str, interval_sec: float = 1.0):
        now = time.time()
        if now - self._last_log_sec >= interval_sec:
            self.get_logger().info(msg)
            self._last_log_sec = now


def main(args=None):
    rclpy.init(args=args)
    node = PurePursuitUDP()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 소켓 정리
        if hasattr(node, 'ego_info_receiver'):
            try:
                node.ego_info_receiver.stop()
            except Exception:
                pass
        rclpy.shutdown()


if __name__ == '__main__':
    main()
