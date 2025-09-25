#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from interfaces_control_pkg.msg import ErpCmdMsg
import socket
import struct
import time

class EgoCtrlCmdSender:
    def __init__(self, ip='127.0.0.1', port=9091):
        self.ip = ip
        self.port = port
        self.socket = None

        # 헤더 구성
        message_name = '#MoraiCtrlCmd$'.encode()
        data_length = struct.pack('i', 23)
        aux_data = struct.pack('iii', 0, 0, 0)
        self.header = message_name + data_length + aux_data
        self.tail = '\r\n'.encode()

        self.connect()

    def connect(self):
        """UDP 소켓 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"UDP 소켓 생성 완료 - 목적지: {self.ip}:{self.port}")
        except Exception as e:
            print(f"소켓 생성 실패: {e}")

    def disconnect(self):
        """소켓 연결 해제"""
        if self.socket:
            self.socket.close()
            print("소켓 연결 해제")

    def format_data(self, gear=4, accel=0.0, brake=0.0, steering=0.0, cmd_type=1, velocity=0.0, acceleration=0.0):
        """
        제어 명령 데이터 포맷팅

        Args:
            accel: 가속 페달 (0.0 ~ 1.0)
            brake: 브레이크 페달 (0.0 ~ 1.0)
            steering: 조향각 (-1.0 ~ 1.0, 좌측이 음수)
            cmd_type: 명령 타입 (1: Throttle, 2: Velocity, 3: Acceleration)
            velocity: 목표 속도 (cmd_type=2일 때 사용)
            acceleration: 목표 가속도 (cmd_type=3일 때 사용)
        """
        mode = struct.pack('b', 2)  # 1: KeyBoard / 2: AutoMode
        gear = struct.pack('b', 4)  # 1: Parking / 2: Reverse / 3: Neutral / 4: Drive
        cmd_type_packed = struct.pack('b', cmd_type)  # 1: Throttle / 2: Velocity / 3: Acceleration
        velocity_packed = struct.pack('f', velocity)
        acceleration_packed = struct.pack('f', acceleration)
        accel_packed = struct.pack('f', accel)
        brake_packed = struct.pack('f', brake)
        steering_packed = struct.pack('f', steering)

        message = (mode + gear + cmd_type_packed + velocity_packed +
                  acceleration_packed + accel_packed + brake_packed + steering_packed)

        formatted_data = self.header + message + self.tail
        return formatted_data

    def send_command(self, gear=4, accel=0.0, brake=0.0, steering=0.0, cmd_type=1, velocity=0.0, acceleration=0.0):
        """
        제어 명령 전송

        Args:
            accel: 가속 페달 (0.0 ~ 1.0)
            brake: 브레이크 페달 (0.0 ~ 1.0)
            steering: 조향각 (-1.0 ~ 1.0)
            cmd_type: 1=Throttle, 2=Velocity, 3=Acceleration
            velocity: 목표 속도 (m/s)
            acceleration: 목표 가속도 (m/s²)
        """
        if not self.socket:
            print("소켓이 연결되지 않았습니다.")
            return False

        try:
            data = self.format_data(accel, gear, brake, steering, cmd_type, velocity, acceleration)
            self.socket.sendto(data, (self.ip, self.port))
            return True
        except Exception as e:
            print(f"데이터 전송 실패: {e}")
            return False

    def send_throttle_command(self, throttle=0.0, brake=0.0, steering=0.0, gear=4):
        """스로틀 모드로 명령 전송"""
        return self.send_command(gear=gear, accel=throttle, brake=brake, steering=steering, cmd_type=1)

    def send_velocity_command(self, target_velocity=0.0, steering=0.0,  get_brake=0.0, get_gear=1):
        """속도 제어 모드로 명령 전송"""
        return self.send_command(steering=steering, cmd_type=2, velocity=target_velocity,  brake=get_brake, gear=get_gear)

    def send_acceleration_command(self, target_acceleration=0.0, steering=0.0):
        """가속도 제어 모드로 명령 전송"""
        return self.send_command(steering=steering, cmd_type=3, acceleration=target_acceleration)

def map_range(x, in_min=-2000, in_max=2000, out_min=-1.0, out_max=1.0):
    """ERP42 조향(-2000~2000) → MORAI 조향(-1.0~1.0)"""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class Erp42CtrlToUdpVelocity(Node):
    def __init__(self):
        super().__init__('erp42_ctrl_to_udp_velocity')

        # 파라미터
        self.declare_parameter('udp_ip', '127.0.0.1')
        self.declare_parameter('udp_port', 9091)

        udp_ip = self.get_parameter('udp_ip').value
        udp_port = self.get_parameter('udp_port').value

        # UDP 송신기
        self.sender = EgoCtrlCmdSender(ip=udp_ip, port=udp_port)

        # ERP42 제어 명령 구독
        self.sub = self.create_subscription(
            ErpCmdMsg,
            '/erp42_ctrl_cmd',
            self.cmd_callback,
            10
        )

        self.get_logger().info(f"ERP42 CTRL_CMD → MORAI Velocity UDP 브리지 시작 ({udp_ip}:{udp_port})")

    def cmd_callback(self, msg: ErpCmdMsg):
        # ERP42 speed는 보통 0~200 (0.1 km/h 단위) → m/s로 변환
        # target_velocity_kmh = float(msg.speed)
        # target_velocity_mps = float(msg.speed) * (1000.0 / 3600.0) * 10
        target_velocity_mps = map_range(float(msg.speed), 0, 200, 0.0, 30.0)

        target_brake_mps = map_range(float(msg.brake), 0, 33, 0.0, 30.0)


        # 브레이크는 단순히 무시 (MORAI Velocity 모드에선 throttle/brake 직접 안 씀)
        steering = map_range(msg.steer, -2000, 2000, -1.0, 1.0)

        # Velocity 모드로 UDP 전송
        self.sender.send_throttle_command(
            throttle=target_velocity_mps,
            steering=steering,
            brake=target_brake_mps,
            gear= msg.gear
        )

        self.get_logger().info(
            f"UDP VelocityCmd 전송: target_velocity={target_velocity_mps:.2f} m/s, "
            f"steer_norm={steering:.3f}"
        )
 

def main(args=None):
    rclpy.init(args=args)
    node = Erp42CtrlToUdpVelocity()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sender.disconnect()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
