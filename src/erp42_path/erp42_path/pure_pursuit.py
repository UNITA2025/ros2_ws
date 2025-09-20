#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node

from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped
from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg

def quat_to_yaw(q):
    # z-w yaw
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

class PurePursuit(Node):
    def __init__(self):
        super().__init__('pure_pursuit')

        # params
        self.declare_parameter("lookahead", 2.0)
        self.declare_parameter("target_speed", 3.0)   # m/s
        self.declare_parameter("wheelbase", 1.04)     # ERP-42
        self.declare_parameter("use_status_speed", False)  # 현재속도를 status에서 읽어 적응제어 할지

        self.Ld = self.get_parameter("lookahead").value
        self.v_target = self.get_parameter("target_speed").value
        self.L = self.get_parameter("wheelbase").value
        self.use_status_speed = self.get_parameter("use_status_speed").value

        self.path: Path | None = None
        self.odom: Odometry | None = None
        self.curr_speed_ms: float = 0.0   # 현재 속도 (m/s, status에서 가져오면 변환)

        # subs
        self.create_subscription(Path, "/local_path", self.path_cb, 10)
        self.create_subscription(Odometry, "/odometry/local_enu", self.odom_cb, 10)
        # 선택: 현재 속도/기어 참고하려면 활성화
        self.create_subscription(ErpStatusMsg, "/erp42_status", self.status_cb, 10)

        # pub
        self.pub = self.create_publisher(ErpCmdMsg, "/erp42_ctrl_cmd", 10)

        self.timer = self.create_timer(0.05, self.on_timer)  # 20Hz

    def path_cb(self, msg: Path):
        self.path = msg

    def odom_cb(self, msg: Odometry):
        self.odom = msg

    def status_cb(self, msg: ErpStatusMsg):
        # 예: status가 km/h면 m/s로 변환 (필드명은 너희 패키지 정의에 맞춰 수정)
        # here assuming msg.speed_kmh 존재 가정
        try:
            v_kmh = getattr(msg, "speed_kmh", None)
            if v_kmh is not None:
                self.curr_speed_ms = float(v_kmh) / 3.6
            else:
                v_ms = getattr(msg, "speed", None)
                if v_ms is not None:
                    self.curr_speed_ms = float(v_ms)
        except Exception:
            pass

    def on_timer(self):
        if self.path is None or self.odom is None or not self.path.poses:
            return

        # pose & yaw from odom
        px = self.odom.pose.pose.position.x
        py = self.odom.pose.pose.position.y
        yaw = quat_to_yaw(self.odom.pose.pose.orientation)

        # lookahead target 찾기 (전방점 우선)
        target_b = None
        cos_y = math.cos(yaw); sin_y = math.sin(yaw)

        for ps in self.path.poses:
            dx = ps.pose.position.x - px
            dy = ps.pose.position.y - py
            # 월드→바디 회전 (R(-yaw))
            bx =  cos_y * dx + sin_y * dy
            by = -sin_y * dx + cos_y * dy
            dist = math.hypot(bx, by)
            if bx > 0.0 and dist >= self.Ld:  # 차량 전방 & Ld 이상
                target_b = (bx, by, dist)
                break

        if target_b is None:
            # 마지막 점이라도 사용 (전방이 없으면 조향 0으로 천천히)
            ps = self.path.poses[-1]
            dx = ps.pose.position.x - px
            dy = ps.pose.position.y - py
            bx =  cos_y * dx + sin_y * dy
            by = -sin_y * dx + cos_y * dy
            dist = max(1e-3, math.hypot(bx, by))
            target_b = (bx, by, dist)

        bx, by, ld = target_b

        # Pure Pursuit 조향 (바디 기준)
        steer_rad = math.atan2(2.0 * self.L * by, ld**2)
        steer_deg = math.degrees(steer_rad)

        # ERP-42 한계 각(예: ±28deg) 가드
        STEER_MAX = 2000.0
        steer_deg = max(-STEER_MAX, min(STEER_MAX, steer_deg))

        # 속도 결정
        if self.use_status_speed and self.curr_speed_ms > 0.01:
            v_cmd = self.curr_speed_ms  # or 간단한 lookahead 기반 가감속 로직
        else:
            v_cmd = self.v_target

        # cmd 패킹 (필드명은 실제 정의에 맞게)
        cmd = ErpCmdMsg()
        cmd.steer = int(steer_deg)             # (좌회전 +, 우회전 -) 방향은 차량 정의에 맞춰 필요시 부호 반전
        cmd.speed = int(v_cmd * 3.6  + 10)             # m/s 가정 (너희 드라이버가 km/h면 3.6 곱해줘)
        cmd.gear = 1                      # D
        cmd.brake = 0
        self.pub.publish(cmd)

def main():
    rclpy.init()
    node = PurePursuit()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
