#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from erp42_msgs.msg import ErpStatusMsg, ErpCmdMsg


class rp42RelayNode(Node):
    def __init__(self):
        super().__init__('erp42status_to_cmdctrl')

        # Publisher 생성
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)

        # Subscriber 생성
        self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)

        self.get_logger().info('ERP42 Relay Node started')

    def status_callback(self, status_msg):
        """
        ErpStatusMsg를 받아서 ErpCmdMsg로 변환하여 발행
        """
        # ErpCmdMsg 생성
        cmd_msg = ErpCmdMsg()

        # 공통 필드 복사 (ErpStatusMsg -> ErpCmdMsg)
        cmd_msg.e_stop = status_msg.e_stop
        cmd_msg.gear = status_msg.gear
        cmd_msg.speed = status_msg.speed
        cmd_msg.steer = status_msg.steer
        cmd_msg.brake = status_msg.brake

        # 명령 발행
        self.cmd_pub.publish(cmd_msg)

        # 로그 출력 (선택사항)
        self.get_logger().info(f'Relayed: gear={cmd_msg.gear}, speed={cmd_msg.speed}, steer={cmd_msg.steer}')


def main(args=None):
    rclpy.init(args=args)

    node = Erp42RelayNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
