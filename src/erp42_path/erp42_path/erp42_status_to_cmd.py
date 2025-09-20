#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg
# 실제 메시지 타입으로 변경하세요
# from erp42_msgs.msg import Erp42Status, Erp42CmdCtrl

class ERP42StatusToCmdBridge(Node):
    def __init__(self):
        super().__init__('erp42_status_to_cmd_bridge')

        # 상태 구독자
        self.status_subscription = self.create_subscription(
            # Erp42Status,  # 실제 메시지 타입으로 변경
            ErpStatusMsg,
            '/erp42_status',
            self.status_callback,
            10
        )

        # 제어 명령 발행자
        self.cmd_publisher = self.create_publisher(
            # Erp42CmdCtrl,  # 실제 메시지 타입으로 변경
            ErpCmdMsg,
            '/erp42_ctrl_cmd',
            10
        )

        self.get_logger().info('ERP42 Status to Cmd Bridge started')

    def status_callback(self, status_msg):
        """ERP42 상태를 받아서 그대로 제어 명령으로 발행"""

        # Erp42CmdCtrl 메시지 생성
        cmd_msg = ErpCmdMsg()  # 실제로는 Erp42CmdCtrl()

        # status에서 cmd로 동일한 필드들 복사
        cmd_msg.e_stop = status_msg.e_stop
        cmd_msg.gear = status_msg.gear
        cmd_msg.speed = status_msg.speed * 10
        cmd_msg.steer = -status_msg.steer
        cmd_msg.brake = status_msg.brake

        # 제어 명령 발행
        self.cmd_publisher.publish(cmd_msg)

        # 로깅 (선택적)
        self.get_logger().info(
            f'Bridged - Speed: {cmd_msg.speed}, Steer: {cmd_msg.steer}, '
            f'Gear: {cmd_msg.gear}, E-Stop: {cmd_msg.e_stop}, Brake: {cmd_msg.brake}'
        )


def main(args=None):
    rclpy.init(args=args)

    bridge_node = ERP42StatusToCmdBridge()

    try:
        rclpy.spin(bridge_node)
    except KeyboardInterrupt:
        bridge_node.get_logger().info('Bridge stopped by user')
    finally:
        bridge_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
