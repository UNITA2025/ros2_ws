#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from struct import pack
import serial
import numpy as np

from interfaces_control_pkg.msg import ErpStatusMsg, ErpCmdMsg  # 메시지 타입 확인
from erp42_control.ByteHandler import ErpMsg2Packet, Packet2ErpMsg

START_BITS = "535458"


class ERPHandler(Node):
    def __init__(self):
        super().__init__("erp_base")

        # Declare and get parameters
        self.declare_parameter("port", "/dev/ttyUSB1")
        self.declare_parameter("baudrate", 115200)
        port = self.get_parameter("port").get_parameter_value().string_value
        baudrate = self.get_parameter("baudrate").get_parameter_value().integer_value

        self.get_logger().info(f"Serial Port: {port}")
        self.get_logger().info(f"Baudrate: {baudrate}")

        self.serial = serial.Serial(port=port, baudrate=baudrate)
        self.get_logger().info(f"Serial {port} connected.")

        self.alive = 0
        self.packet = ErpCmdMsg()
        self.packet.gear = 0
        self.packet.e_stop = False
        self.packet.brake = 1

        # ROS2 Publisher & Subscriber
        self.erpMotionMsg_pub = self.create_publisher(ErpStatusMsg, "/erp42_status", 3)
        self.create_subscription(ErpCmdMsg, "/erp42_ctrl_cmd", self.sendPacket, 10)

        # Timer (40Hz)
        self.create_timer(1.0 / 40.0, self.timer_callback) 

    def recvPacket(self):
        try:
            packet = self.serial.read(18)
            hex_data = packet.hex()

            # START_BITS 검사
            if not hex_data.startswith(START_BITS):
                self.get_logger().warn(f"Invalid START_BITS: {hex_data}")
                return

            # 파싱 시도
            try:
                msg = Packet2ErpMsg(packet)
                self.erpMotionMsg_pub.publish(msg)
            except Exception as inner_e:
                self.get_logger().warn(f"Packet2ErpMsg Error: {inner_e} | raw: {hex_data}")

        except Exception as e:
            self.get_logger().warn(f"recvPacket Error: {e}")

    def sendPacket(self, _data: ErpCmdMsg):
        self.packet = _data

    def serialSend(self):
        try:
            packet = ErpMsg2Packet(self.packet, self.alive)
            self.serial.write(packet)
            self.alive = (self.alive + 1) % 256
        except Exception as e:
            self.get_logger().warn(f"serialSend Error: {e}")

    def timer_callback(self):
        self.recvPacket()
        self.serialSend()


def main(args=None):
    rclpy.init(args=args)
    node = ERPHandler()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
