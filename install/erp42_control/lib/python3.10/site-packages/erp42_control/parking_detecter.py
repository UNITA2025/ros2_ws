import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from interfaces_control_pkg.msg import ConeInfo, ConeInfoArray 
import math


class ParkingDetecter(Node):
    def __init__(self):
        super().__init__('parking_detecter')

        # cluster_centroids 토픽 구독 (CneInfoArray 타입)
        self.subscription = self.create_subscription(
            ConeInfoArray,  # 메시지 타입. 임의로 배열 메시지 타입 예시로 사용
            '/cones/cone_info_down',
            self.listener_callback,
            10)
        self.subscription

        # parking_ok 토픽 Bool 메시지 발행
        self.pub_parking_ok = self.create_publisher(Bool, 'parking_ok', 10)

        # 가장 가까운 2개 콘 간 최소 거리 저장 변수 (초기값 설정)
        self.closest_distance = None  # float, None이면 아직 계산된 적 없음

        # (필요시) 가장 가까운 2개 콘 인덱스도 저장 가능
        self.closest_pair = None  # tuple (i, j)


    def listener_callback(self, msg):
        centroids = msg.cones  # ConeInfo 배열 필드명은 메시지 정의에 따라 변경 필요

        n = len(centroids)
        if n < 2:
            # 2개 미만은 parking_ok False 발행 및 거리 초기화
            self.closest_distance = None
            self.closest_pair = None
            self.publish_parking_ok(False)
            return

        min_dist = float('inf')
        closest_pair = (None, None)

        for i in range(n):
            for j in range(i + 1, n):
                dx = centroids[i].x - centroids[j].x
                dy = centroids[i].y - centroids[j].y
                dz = centroids[i].z - centroids[j].z
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist < min_dist:
                    min_dist = dist
                    closest_pair = (i, j)

        # 계산된 가장 가까운 2개 거리 저장
        self.closest_distance = min_dist
        self.closest_pair = closest_pair

        # 로그 출력: 가장 가까운 두 콘의 거리와 인덱스
        self.get_logger().info(
            f'Closest cones indices: {closest_pair[0]} and {closest_pair[1]}, distance: {min_dist:.3f} m'
        )

        parking_status = (min_dist > 2.0)
        self.publish_parking_ok(parking_status)


    def publish_parking_ok(self, status: bool):
        msg = Bool()
        msg.data = status
        self.pub_parking_ok.publish(msg)
        self.get_logger().info(f'Published parking_ok: {status}')


def main(args=None):
    rclpy.init(args=args)
    node = ParkingDetecter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
