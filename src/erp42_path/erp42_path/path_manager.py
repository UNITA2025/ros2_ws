#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from nav_msgs.msg import Path, Odometry
from std_msgs.msg import String

# --- (옵션) ERP42 명령 메시지: 없으면 모드 신호만 보냄 ---
ErpCmdMsg = None
try:
    from interfaces_control_pkg.msg import ErpCmdMsg as _ErpCmdMsg
    ErpCmdMsg = _ErpCmdMsg
except Exception:
    pass


class PathManager(Node):
    """위치 기반 자동 경로 전환 + 주차 완료 후 후진 복귀 FSM"""

    def __init__(self):
        super().__init__('path_manager')

        # ===== 상태 변수 =====
        self.current_mode = "normal"            # normal | parking | reverse_out
        self.current_position: Optional[Point] = None
        self.global_path: Optional[Path] = None
        self.parking_path: Optional[Path] = None
        self.parking_check = False
        self.mission_completed = False

        # 후진용 상태
        self._reverse_t0: Optional[float] = None

        # ===== 파라미터 선언 =====
        # 경로 전환 관련
        self.declare_parameter('parking_proximity_threshold', 3.0)   # 주차 경로 시작점 접근 거리
        self.declare_parameter('parking_complete_threshold', 1.0)    # 주차 경로 끝점 도달 판단 거리
        self.declare_parameter('mode_check_rate', 5.0)               # 메인 루프 Hz
        self.declare_parameter('enable_debug_logging', True)

        # 후진(Reverse-Out) 관련
        self.declare_parameter('enable_reverse_out', True)           # 주차 완료 후 후진 기능 on/off
        self.declare_parameter('reverse_duration_s', 5.0)            # 후진 지속 시간 [s]
        self.declare_parameter('reverse_speed', 30)                  # 후진 속도 (컨트롤러 단위에 맞춰 튜닝)
        self.declare_parameter('reverse_steer_deg', 0.0)             # 후진 조향 (deg)
        self.declare_parameter('reverse_brake', 0)                   # 보통 0 (자유롤링), 필요시 값 조정

        # 명령 퍼블리시 토픽
        self.declare_parameter('cmd_topic', '/path_manager/cmd')     # 충돌 피하려고 별도 토픽 권장
        self.declare_parameter('erp_cmd_topic_compat', '/erp42_ctrl_cmd')  # 호환용(비추천)

        # ===== 파라미터 로드 =====
        self._load_parameters()

        # ===== ROS 인터페이스 구성 =====
        self._setup_ros_interfaces()

        # ===== 메인 타이머 =====
        check_period = max(1e-3, 1.0 / float(self.mode_check_rate))
        self.main_timer = self.create_timer(check_period, self.main_loop)

        self.get_logger().info(
            f"Path Manager initialized | park_thr={self.parking_threshold:.2f} m, "
            f"done_thr={self.parking_complete_threshold:.2f} m, "
            f"reverse={self.enable_reverse_out} ({self.reverse_duration_s:.2f}s @ {self.reverse_speed})"
        )

    def _load_parameters(self):
        self.parking_threshold = float(self.get_parameter('parking_proximity_threshold').value)
        self.parking_complete_threshold = float(self.get_parameter('parking_complete_threshold').value)
        self.mode_check_rate = float(self.get_parameter('mode_check_rate').value)
        self.debug_logging = bool(self.get_parameter('enable_debug_logging').value)

        self.enable_reverse_out = bool(self.get_parameter('enable_reverse_out').value)
        self.reverse_duration_s = float(self.get_parameter('reverse_duration_s').value)
        self.reverse_speed = int(self.get_parameter('reverse_speed').value)
        self.reverse_steer_deg = float(self.get_parameter('reverse_steer_deg').value)
        self.reverse_brake = int(self.get_parameter('reverse_brake').value)

        self.cmd_topic = str(self.get_parameter('cmd_topic').value)
        self.erp_cmd_topic_compat = str(self.get_parameter('erp_cmd_topic_compat').value)

    def _setup_ros_interfaces(self):
        # === 구독 ===
        self.create_subscription(Odometry, '/odometry/local_enu', self.odometry_callback, 10)
        self.create_subscription(Path, '/global_path', self.global_path_callback, 10)
        self.create_subscription(Path, '/parking_path', self.parking_path_callback, 10)

        # === 발행 ===
        self.active_path_pub = self.create_publisher(Path, '/active_path', 10)
        self.controller_mode_pub = self.create_publisher(String, '/controller_mode', 10)
        self.system_status_pub = self.create_publisher(String, '/path_manager_status', 10)

        # ERP42 명령 퍼블리셔 (옵션)
        self.cmd_pub = None
        if ErpCmdMsg is not None:
            # 충돌 피하려면 cmd_topic 사용 권장
            self.cmd_pub = self.create_publisher(ErpCmdMsg, self.cmd_topic, 10)
            # 필요하다면 호환 토픽도 켤 수 있게 남겨둠 (비추천)
            if self.erp_cmd_topic_compat and self.erp_cmd_topic_compat != self.cmd_topic:
                self.cmd_pub_compat = self.create_publisher(ErpCmdMsg, self.erp_cmd_topic_compat, 10)
            else:
                self.cmd_pub_compat = None
        else:
            self.get_logger().warn(
                "interfaces_control_pkg/ErpCmdMsg 를 불러오지 못했습니다. "
                "후진 동안에는 모드 신호만 전송합니다(controller가 이 모드를 처리해야 함)."
            )

    # ========== 콜백 ==========
    def odometry_callback(self, msg: Odometry):
        self.current_position = msg.pose.pose.position
        if self.debug_logging:
            self.get_logger().debug(f"pos=({self.current_position.x:.2f},{self.current_position.y:.2f})")

    def global_path_callback(self, msg: Path):
        self.global_path = msg
        self.get_logger().info(f"Global path received: {len(msg.poses)} points")
        if self.current_mode == "normal":
            self._publish_active_path()

    def parking_path_callback(self, msg: Path):
        self.parking_path = msg
        self.get_logger().info(f"Parking path received: {len(msg.poses)} points")
        if self.current_mode == "parking":
            self._publish_active_path()

    # ========== 메인 루프 ==========
    def main_loop(self):
        if not self.current_position:
            return

        prev_mode = self.current_mode
        if self.current_mode == "normal":
            if (not self.mission_completed and 
                self._should_switch_to_parking() and 
                not self.parking_check):
                self.parking_check = True  # 주차 시도 플래그 설정
                self._change_mode_to("parking")

        elif self.current_mode == "parking":
            # 주차 완료 판단 → reverse_out 진입(옵션) 또는 normal 복귀
            if self._parking_completed():
                if self.enable_reverse_out:
                    self._start_reverse_out()

        elif self.current_mode == "reverse_out":
            if self._reverse_out_finished():
                self.mission_completed = True # 미션 완료 플래그 설정
                self.get_logger().info("↩ 후진 완료 → Global Path 합류 (normal)")
                self._change_mode_to("normal")

            # 후진 진행 중에는 명령 퍼블리시 (가능하면)
            self._publish_reverse_cmd()
            # 후진 상태에선 active_path를 굳이 바꾸지 않음(컨트롤러가 무시해도 되도록)

        # (reverse_out 제외) 활성 경로 발행
        if self.current_mode in ("normal", "parking"):
            self._publish_active_path()

        # 상태 발행
        self._publish_status()

        if prev_mode != self.current_mode:
            self.get_logger().info(f"Mode transition: {prev_mode} → {self.current_mode}")

    # ========== 전환 조건 ==========
    def _should_switch_to_parking(self) -> bool:
        if not self.parking_path or not self.parking_path.poses:
            return False
        start = self.parking_path.poses[0].pose.position
        d = self._dist(self.current_position, start)
        if d < self.parking_threshold:
            if self.debug_logging:
                self.get_logger().info(f"🚗 Parking mode 진입 (start까지 {d:.2f} m)")
            return True
        return False

    def _parking_completed(self) -> bool:
        if not self.parking_path or not self.parking_path.poses:
            return True  # 경로 없으면 정상주행 복귀
        end = self.parking_path.poses[-1].pose.position
        d = self._dist(self.current_position, end)
        done = d < self.parking_complete_threshold
        if self.debug_logging and done:
            self.get_logger().info(f"✅ Parking 완료 (end까지 {d:.2f} m)")
        return done

    # ========== 후진 제어 ==========
    def _start_reverse_out(self):
        self._reverse_t0 = time.time()
        self._change_mode_to("reverse_out")
        self.get_logger().info(
            f"↩ 후진 시작: {self.reverse_duration_s:.2f}s, speed={self.reverse_speed}, steer={self.reverse_steer_deg}deg"
        )

    def _reverse_out_finished(self) -> bool:
        if self._reverse_t0 is None:
            return True
        return (time.time() - self._reverse_t0) >= self.reverse_duration_s

    def _publish_reverse_cmd(self):
        """후진 중일 때 실제 ERP42 명령 퍼블리시(가능하면)."""
        # 모드 신호(항상)
        mode_msg = String()
        mode_msg.data = "reverse_out"
        self.controller_mode_pub.publish(mode_msg)

        if self.cmd_pub is None or ErpCmdMsg is None:
            return  # 명령 메시지 타입이 없으면 여기서 끝

        cmd = ErpCmdMsg()
        # 아래 필드명은 프로젝트 스키마에 맞게 조정해도 됨
        # (일반적인 ERP42 커스텀 메시지 스타일 가정)
        try:
            cmd.gear = 2               # 1: D, 2: R (프로젝트 정의에 맞게)
            cmd.speed = int(self.reverse_speed)
            # steer(deg) → 내부가 deg 혹은 raw인지 프로젝트 규격에 맞춰 조정
            if hasattr(cmd, 'steer_deg'):
                cmd.steer_deg = float(self.reverse_steer_deg)
            elif hasattr(cmd, 'steer'):
                # raw 스티어 값이면 컨트롤러에서 변환하도록 0으로 유지하거나 별도 파라미터 사용
                cmd.steer = 0
            cmd.brake = int(self.reverse_brake)
            if hasattr(cmd, 'e_stop'):
                cmd.e_stop = False
        except Exception as e:
            self.get_logger().warn(f"Reverse cmd field assign warn: {e}")

        self.cmd_pub.publish(cmd)
        # if hasattr(self, 'cmd_pub_compat') and self.cmd_pub_compat is not None:
        #     self.cmd_pub_compat.publish(cmd)  # (선택) 호환 토픽

    # ========== 모드/경로/상태 퍼블리시 ==========
    def _change_mode_to(self, new_mode: str):
        old_mode = self.current_mode
        self.current_mode = new_mode

        mode_msg = String()
        mode_msg.data = new_mode
        self.controller_mode_pub.publish(mode_msg)

        self.get_logger().info(f"Mode changed: {old_mode} → {new_mode}")

    def _publish_active_path(self):
        path: Optional[Path] = None
        if self.current_mode == "parking":
            path = self.parking_path
        elif self.current_mode == "normal":
            path = self.global_path

        if path and path.poses:
            path.header.stamp = self.get_clock().now().to_msg()
            self.active_path_pub.publish(path)
            if self.debug_logging:
                self.get_logger().debug(f"Published {self.current_mode} path: {len(path.poses)} pts")

    def _publish_status(self):
        status_msg = String()
        status_msg.data = (
            f"mode:{self.current_mode},"
            f"global:{self.global_path is not None},"
            f"parking:{self.parking_path is not None}"
        )
        self.system_status_pub.publish(status_msg)

    # ========== 유틸 ==========
    @staticmethod
    def _dist(p1: Point, p2: Point) -> float:
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def get_current_status(self) -> dict:
        st = {
            'current_mode': self.current_mode,
            'position': (
                {'x': self.current_position.x, 'y': self.current_position.y}
                if self.current_position else None
            ),
            'paths': {
                'global_available': self.global_path is not None,
                'global_points': len(self.global_path.poses) if self.global_path else 0,
                'parking_available': self.parking_path is not None,
                'parking_points': len(self.parking_path.poses) if self.parking_path else 0,
            }
        }
        if self.current_position and self.parking_path and self.parking_path.poses:
            s = self.parking_path.poses[0].pose.position
            e = self.parking_path.poses[-1].pose.position
            st['distances'] = {
                'to_parking_start': self._dist(self.current_position, s),
                'to_parking_end': self._dist(self.current_position, e)
            }
        return st


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = PathManager()

        if node.debug_logging:
            def print_status():
                node.get_logger().info(f"Status: {node.get_current_status()}")
            node.create_timer(10.0, print_status)

        node.get_logger().info("Path Manager started")
        rclpy.spin(node)

    except KeyboardInterrupt:
        print("Path Manager shutting down...")
    except Exception as e:
        print(f"Path Manager failed: {e}")
    finally:
        if node is not None:
            try:
                print(f"Final Status: {node.get_current_status()}")
            except Exception:
                pass
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
