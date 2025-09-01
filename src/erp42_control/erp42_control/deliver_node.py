#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##2025/08/26,27추가는 내가임의로 한거

import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from nav_msgs.msg import Path ##2025/08/26추가
from geometry_msgs.msg import PoseStamped, Point ##2025/08/26추가


# 사용자 정의 메시지(메모리 기준)
# ErpCmdMsg.msg:
#   bool e_stop
#   uint8 gear   # 0: 중립, 1: 전진, 2: 후진
#   uint8 speed  # 0 ~ 200
#   int32 steer  # ±2000
#   uint8 brake  # 0 ~ 33
from interfaces_control_pkg.msg import ErpCmdMsg ##2025/08/27 그냥 interface_pkg.msg -> erp42_interfaces_pkg.msg로 변경


class ERP42CtrlCmd(Node):
    def __init__(self):
        super().__init__('erp42_ctrl_cmd_node')

        # 퍼블리셔/서브스크라이버
        self.pub_cmd = self.create_publisher(ErpCmdMsg, '/ctrl_cmd', 10)
        self.sub_signal = self.create_subscription(Bool, '/control/signal', self.delivery_callback, 10)

        # 상태 플래그
        self.delivery_sign = False
        self.delivery_ing = False

        # 주기적으로 기본 주행 명령 퍼블리시(ROS1의 while+Rate 대체)
        self.timer = self.create_timer(0.1, self.control)  # 10 Hz

        # 재사용 메시지 버퍼
        self.cmd = ErpCmdMsg()

        self.get_logger().info('ERP42 delivery node (ROS2) started.')

    # /control/signal 수신 → True면 배달 시퀀스 실행
    def delivery_callback(self, msg: Bool):
        self.delivery_sign = msg.data
        if self.delivery_sign and not self.delivery_ing:
            self.delivery()

    # 배달 시퀀스(원본과 동일: 블로킹 while 루프로 시간 제어)
    def delivery(self):
        self.delivery_ing = True
        self.get_logger().info('delivery_ing')

        speed = 30
        steer = 1000
        turn_duration = 2.0
        straight_duration = 2.0
        stop_duration = 5.0

        # ① 시작 정지 2초
        end_time = time.time() + 2.0
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=0, speed=0, gear=0, e_stop=False, brake=1)

        # ② 좌회전(전진 의도) 2초  (원본 유지: gear=0)
        end_time = time.time() + turn_duration
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=steer, speed=speed, gear=0, e_stop=False, brake=0)

        # ③ 우회전(전진 의도) 2초  (원본 유지: gear=0)
        end_time = time.time() + turn_duration
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=-steer, speed=speed, gear=0, e_stop=False, brake=0)

        # ④ 정지 5초
        end_time = time.time() + stop_duration
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=0, speed=0, gear=0, e_stop=False, brake=1)

        # ⑤ 직진(후진기어) 2초 (원본 유지: gear=2)
        end_time = time.time() + straight_duration
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=0, speed=speed, gear=2, e_stop=False, brake=0)

        # ⑥ 우회전(전진 의도) 2초  (원본 유지: gear=0)
        end_time = time.time() + turn_duration
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=-steer, speed=speed, gear=0, e_stop=False, brake=0)

        # ⑦ 좌회전(전진 의도) 2초  (원본 유지: gear=0)
        end_time = time.time() + turn_duration
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=steer, speed=speed, gear=0, e_stop=False, brake=0)

        # ⑧ 직진(정리) 2초  (원본 유지: gear=0)
        end_time = time.time() + straight_duration
        while time.time() < end_time and rclpy.ok():
            self.fill_and_pub(steer=0, speed=speed, gear=0, e_stop=False, brake=0)

        self.delivery_ing = False
        self.get_logger().info('delivery finished')

    # 기본 주행(배달 중이 아닐 때만)
    def control(self):
        if self.delivery_ing:
            return
        # 원본 유지: gear=0(중립) + speed=50
        self.fill_and_pub(steer=0, speed=50, gear=0, e_stop=False, brake=0, log=True)

    # 편의 함수: 필드 채우고 퍼블리시
    def fill_and_pub(self, steer: int, speed: int, gear: int, e_stop: bool, brake: int, log: bool = False):
        self.cmd.steer = int(steer)
        self.cmd.speed = int(speed)
        self.cmd.gear = int(gear)
        self.cmd.e_stop = bool(e_stop)
        self.cmd.brake = int(brake)
        if log:
            self.get_logger().info(f'Speed={self.cmd.speed}, Steer={self.cmd.steer}, Gear={self.cmd.gear}, Brake={self.cmd.brake}')
        self.pub_cmd.publish(self.cmd)


def main():
    rclpy.init()
    node = ERP42CtrlCmd()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
