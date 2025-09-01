#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import math
import numpy as np
from math import sqrt, atan2, sin

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker
from tf_transformations import quaternion_from_euler

from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg


class PurePursuit(Node):
    def __init__(self):
        super().__init__('erp_control')

        # Publishers / Subscribers
        self.cmd_pub = self.create_publisher(ErpCmdMsg, '/erp42_ctrl_cmd', 10)
        self.create_subscription(Path, '/local_path', self.path_callback, 10)
        self.create_subscription(ErpStatusMsg, '/erp42_status', self.status_callback, 10)

        # NEW: visualization publishers
        self.lookahead_marker_pub = self.create_publisher(Marker, '/lookahead_marker', 10)
        self.lookahead_pose_pub   = self.create_publisher(PoseStamped, '/lookahead_pose', 10)

        # State
        self.is_path = False
        # self.is_status = False
        self.is_status = True
        self.forward_point = Point()
        self.vehicle_length = 1.82
        self.lfd = 3.5

        ### 추종할 점의 거리에 대한 gain
        self.lfd_gain = 2.0
        ###
        
        self.cur_speed = 0.0
        self.path = Path()
        self.erp_cmd_msg = ErpCmdMsg()

        self.timer = self.create_timer(0.1, self.timer_callback)

    def timer_callback(self):
        if self.is_path and self.is_status:
            self.pure_pursuit_control(slowdown=True)
        else:
            os.system('clear')
            if not self.is_path:
                self.get_logger().info("[1] '/local_path' x ")
            if not self.is_status:
                self.get_logger().info("[2] '/erp42_status' x")

    def pure_pursuit_control(self, slowdown=False):
        # demo: 고정 속도로 테스트
        # self.cur_speed = 30
        
        ### lfd 클수록 path상에서 멀리 있는 점 추종. ###
        # 즉, 1. 속도가 빠르거나  2. lfd_gain클수록 멀리있는 점 추종.(매끄럽게 주행)
        self.lfd = max(2.0, self.lfd_gain  * self.cur_speed)
        ##########################################

        self.is_look_forward_point = False

        # --- find look-ahead point (vehicle_frame 기준) ---
        for pose in self.path.poses:
            dx = pose.pose.position.x
            dy = pose.pose.position.y
            # IMPORTANT: >= 0 는 항상 참 -> lfd 사용
            dist = sqrt(dx*dx + dy*dy)
            self.get_logger().info(f"lfd : {self.lfd:.2f}, cur_speed : {self.cur_speed:.1f}, dist = {dist:.1f} ")
            
            if dist >= self.lfd:
                self.forward_point = pose.pose.position
                self.is_look_forward_point = True
                break

        if not self.is_look_forward_point:
            self.get_logger().warn("추종점 없음.")
            self.clear_lookahead_visuals()
            self.publish_stop()
            return

        # 방향각(차량 좌표계에서)
        theta = atan2(self.forward_point.y, self.forward_point.x)
        steer_rad = atan2(2 * self.vehicle_length * sin(theta), self.lfd)
        steer_rad = np.clip(steer_rad, math.radians(-20), math.radians(20))

        # --- publish visualization ---
        self.publish_lookahead_visuals(theta)

        # --- command ---
        if -5.0 <= math.degrees(steer_rad) <= 5.0:
            self.erp_cmd_msg.speed = 100
        else:
            self.erp_cmd_msg.speed = 50
        self.erp_cmd_msg.steer = -1 *(int((2000/20) * (math.degrees(steer_rad))))
        self.erp_cmd_msg.gear = 0
        self.erp_cmd_msg.brake = 0

        self.cmd_pub.publish(self.erp_cmd_msg)
        self.get_logger().info(f"theta={theta:.3f} rad, steer={math.degrees(steer_rad):.1f} deg")

    # ========================
    # Visualization helpers
    # ========================
    def publish_lookahead_visuals(self, theta: float):
        # Marker (sphere) in vehicle_frame
        m = Marker()
        m.header.frame_id = 'vehicle_frame'   # /local_path가 vehicle_frame 기준이므로 동일 프레임
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'lookahead'
        m.id = 0
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = float(self.forward_point.x)
        m.pose.position.y = float(self.forward_point.y)
        m.pose.position.z = 0.0
        m.pose.orientation.w = 1.0
        m.scale.x = 0.5   # diameter
        m.scale.y = 0.5
        m.scale.z = 0.5
        m.color.a = 1.0
        m.color.r = 0.2
        m.color.g = 0.0
        m.color.b = 0.9
        self.lookahead_marker_pub.publish(m)

        # PoseStamped (arrow) — RViz 'Pose' 디스플레이에서 확인
        ps = PoseStamped()
        ps.header.frame_id = 'vehicle_frame'
        ps.header.stamp = m.header.stamp
        ps.pose.position.x = float(self.forward_point.x)
        ps.pose.position.y = float(self.forward_point.y)
        ps.pose.position.z = 0.0
        q = quaternion_from_euler(0.0, 0.0, theta)
        ps.pose.orientation.x = q[0]
        ps.pose.orientation.y = q[1]
        ps.pose.orientation.z = q[2]
        ps.pose.orientation.w = q[3]
        self.lookahead_pose_pub.publish(ps)

    def clear_lookahead_visuals(self):
        m = Marker()
        m.header.frame_id = 'vehicle_frame'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'lookahead'
        m.id = 0
        m.action = Marker.DELETE
        self.lookahead_marker_pub.publish(m)
        # PoseStamped는 굳이 지울 필요 없음(새 값 나오면 갱신)

    def publish_stop(self):
        self.erp_cmd_msg.gear = 1
        self.erp_cmd_msg.steer = 0
        self.erp_cmd_msg.brake = 1
        self.cmd_pub.publish(self.erp_cmd_msg)

    def path_callback(self, msg):
        self.path = msg
        self.is_path = True

    def status_callback(self, msg):
        self.cur_speed = msg.speed
        self.is_status = True


def main(args=None):
    rclpy.init(args=args)
    node = PurePursuit()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

