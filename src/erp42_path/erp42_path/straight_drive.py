#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
import socket
import struct


class StraightDriveUDP(Node):
    def __init__(self):
        super().__init__('straight_drive_udp')

        # 파라미터 (IP/Port, throttle 값)
        self.declare_parameter('udp_ip', '127.0.0.1')
        self.declare_parameter('udp_port', 9091)
        self.declare_parameter('throttle', 0.5)   # 0.0~1.0 사이

        self.ip = self.get_parameter('udp_ip').value
        self.port = self.get_parameter('udp_port').value
        self.throttle = float(self.get_parameter('throttle').value)

        # UDP 소켓 준비
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 헤더/테일 구성
        message_name = "#MoraiCtrlCmd$".encode()
        data_length = struct.pack("<i", 23)
        aux_data = struct.pack("<iii", 0, 0, 0)
        self.header = message_name + data_length + aux_data
        self.tail = "\r\n".encode()

        # 타이머 (0.1초마다 전송)
        self.timer = self.create_timer(0.1, self.timer_callback)

        self.get_logger().info(
            f"Straight UDP Drive 시작 → {self.ip}:{self.port}, throttle={self.throttle}"
        )

    def make_packet(self, throttle=0.0, brake=0.0, steering=0.0):
        """MORAI Control 패킷 구성"""
        mode = struct.pack("<b", 2)   # AutoMode
        gear = struct.pack("<b", 4)   # Drive
        cmd_type = struct.pack("<b", 2)  # Throttle 모드
        velocity = struct.pack("<f", 19.0)
        acceleration = struct.pack("<f", 0.0)

        accel = struct.pack("<f", throttle)
        brake = struct.pack("<f", brake)
        steering = struct.pack("<f", steering)

        return self.header + mode + gear + cmd_type + velocity + acceleration + accel + brake + steering + self.tail

    def timer_callback(self):
        """주기적으로 직진 명령 전송"""
        packet = self.make_packet(throttle=self.throttle, brake=0.0, steering=0.0)
        self.sock.sendto(packet, (self.ip, self.port))
        self.get_logger().info(f"송신: throttle={self.throttle:.2f}, steering=0.0")


def main(args=None):
    rclpy.init(args=args)
    node = StraightDriveUDP()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("종료합니다.")
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
