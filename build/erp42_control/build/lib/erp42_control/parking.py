#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

from std_msgs.msg import Bool
from interfaces_control_pkg.msg import ErpCmdMsg, ErpCmdMsg

class ParkingNode(Node):
    def __init__(self):
        super().__init__('parking_node')

        # 퍼블리셔: ERP42 제어 명령
        self.cmd_publisher = self.create_publisher(
            ErpCmdMsg,
            '/erp42_ctrl_cmd',
            10
        )

        # 구독자: /parking_ok (bool 메시지)
        self.parking_ok_subscriber = self.create_subscription(
            Bool,
            '/parking_ok',
            self.parking_ok_callback,
            10
        )

        self.parking_done = False  # ✅ 주차 수행 여부 플래그

        self.get_logger().info("🚗 Parking Node Started")

    def parking_ok_callback(self, msg: Bool):
        if msg.data and not self.parking_done:
            self.get_logger().info("🟢 Parking signal received. Executing parking maneuver...")
            self.execute_parking()
            self.parking_done = True  # ✅ 한 번만 실행되도록 설정
        elif msg.data and self.parking_done:
            self.get_logger().info("⚠️ Parking already completed. Ignoring signal.")
        else:
            self.get_logger().info("🔴 Parking signal is False. Waiting...")

    def execute_parking(self):
        for i in range(20):  # 20번 반복 (주차 거리 제어)
            cmd = ErpCmdMsg()
            cmd.e_stop = False
            cmd.gear = 2       # 후진
            cmd.speed = 10     # 느린 속도
            cmd.steer = 0      # 직진
            cmd.brake = 0

            self.cmd_publisher.publish(cmd)
            self.get_logger().info(f"[PARKING] Sent command {i+1}/20")

            self.sleep_ms(100)

        # 마지막에 브레이크
        cmd = ErpCmdMsg()
        cmd.e_stop = False
        cmd.gear = 2
        cmd.speed = 0
        cmd.steer = 0
        cmd.brake = 1
        self.cmd_publisher.publish(cmd)
        self.get_logger().info("✅ Parking complete.")

    def sleep_ms(self, ms: int):
        """ROS-safe sleep in milliseconds."""
        self.get_clock().sleep_for(Duration(nanoseconds=ms * 1_000_000))

def main(args=None):
    rclpy.init(args=args)
    node = ParkingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
