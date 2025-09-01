#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from interfaces_control_pkg.msg import ErpCmdMsg

class SimpleDrive(Node):
    def __init__(self):
        super().__init__('simple_drive_node')
        self.publisher = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)

        # 1초마다 실행되는 타이머
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.counter = 0
        self.driving = True

        self.get_logger().info("🚗 Simple Drive Node Started")

    def timer_callback(self):
        cmd = ErpCmdMsg()

        if self.driving and self.counter < 5:  
            # 3초 동안 직진
            cmd.e_stop = False
            cmd.gear = 0     # 전진
            cmd.speed = 50   # 원하는 속도 (단위는 차량 세팅에 맞게)
            cmd.steer = 0
            cmd.brake = 0
            self.publisher.publish(cmd)
            self.get_logger().info(f"➡️ Driving forward... {self.counter+1}/5 sec")
            self.counter += 1

        elif self.driving and self.counter >= 5:
            # 브레이크
            cmd.e_stop = False
            cmd.gear = 1
            cmd.speed = 0
            cmd.steer = 0
            cmd.brake = 100
            self.publisher.publish(cmd)
            self.get_logger().info("🛑 Brake applied. Stopping.")
            self.driving = False

def main(args=None):
    rclpy.init(args=args)
    node = SimpleDrive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
