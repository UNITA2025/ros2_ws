
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

import struct
import socket
import threading
from typing import Optional, Tuple

import rclpy
from rclpy.node import Node

# 네 패키지의 메시지 타입 (필드 정의 맞춰야 함)
from interfaces_control_pkg.msg import ErpStatusMsg  

def map_range(x, in_min=-35, in_max=35, out_min=-2000, out_max=2000):
    #"""[-35, 35] → [-2000, 2000] 범위 맵핑"""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


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



class EgoInfoReceiver(Receiver):
    def __init__(self, ip, port, callback):
        super().__init__(ip, port, callback)
        self.header = '#MoraiInfo$'
        self.data_length = 132
        # self.data_length = 152

    def _parse_data(self, raw_data):
        if self.header == raw_data[0:11].decode() or self.data_length == struct.unpack('i', raw_data[11:15])[0]:
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
            link_id = raw_data[141:179].decode()
            self._parsed_data = [
                ctrl_mode, gear, signed_vel, map_id, accel, brake, size_x, size_y, size_z, overhang, wheelbase,
                rear_overhang, pos_x, pos_y, pos_z, roll, pitch, yaw, vel_x, vel_y, vel_z, acc_x, acc_y, acc_z, steer
            ]
        else:
            self._parsed_data = []
        # print(self.parsed_data)


class EgoInfoNode(Node):
    def __init__(self):
        super().__init__('ego_info_node')

        self.declare_parameter('bind_ip', '127.0.0.1')
        self.declare_parameter('bind_port', 9094)

        ip = self.get_parameter('bind_ip').value
        port = self.get_parameter('bind_port').value

        self.pub = self.create_publisher(ErpStatusMsg, '/erp42_status', 10)

        self.last_data: Optional[List] = None
        self.data_count = 0

        self.receiver = EgoInfoReceiver(ip, port, self._on_rx)

        self.timer = self.create_timer(1.0, self._on_timer)

        self.get_logger().info(f"Listening MORAI EgoInfo {ip}:{port} → /erp42_status")

    def _on_rx(self, data: List):
        self.last_data = data
        self.data_count += 1

        # 토픽 발행
        msg = ErpStatusMsg()
        msg.speed = int(data[2])   # km/h
        msg.steer = int(map_range(data[24]))  # deg (MORAI 출력 단위 확인!) 
        msg.gear = int(data[1])
        msg.brake = int(data[5])
        self.pub.publish(msg)

    def _on_timer(self):
        now = time.strftime('%H:%M:%S')
        if not self.last_data:
            self.get_logger().warn(f"[{now}] 데이터 없음 (count={self.data_count})")
            return

        d = self.last_data
        ctrl_mode, gear, signed_vel, map_id, accel, brake = d[0:6]
        size_x, size_y, size_z, overhang, wheelbase, rear_overhang = d[6:12]
        pos_x, pos_y, pos_z = d[12:15]
        roll, pitch, yaw = d[15:18]
        vel_x, vel_y, vel_z = d[18:21]
        acc_x, acc_y, acc_z = d[21:24]
        steer = d[24]

        print("=" * 120)
        print(f"[{now}] EgoInfo 데이터 현황 (수신 횟수: {self.data_count})")
        print("📊 차량 기본 정보:")
        print(f"   제어 모드={ctrl_mode}, 기어={gear}, 속도={signed_vel:.2f} km/h, accel={accel:.3f}, brake={brake:.3f}, steer={steer:.3f}")
        print("📍 위치 및 자세:")
        print(f"   위치=({pos_x:.2f},{pos_y:.2f},{pos_z:.2f}), 자세(deg) R={roll:.2f}, P={pitch:.2f}, Y={yaw:.2f}")
        print("🏃 속도 벡터:", f"({vel_x:.3f},{vel_y:.3f},{vel_z:.3f}) m/s")
        print("⚡ 가속도:", f"({acc_x:.3f},{acc_y:.3f},{acc_z:.3f}) m/s²")
        print("📐 크기:", f"{size_x:.2f} x {size_y:.2f} x {size_z:.2f}, WB={wheelbase:.2f}")


def main(args=None):
    rclpy.init(args=args)
    node = EgoInfoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
