import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
import time



class ParkingStatusPublisher(Node):
    def __init__(self):
        super().__init__('parking_status_publisher')
        self.publisher_ = self.create_publisher(Bool, 'parking_ok', 10)
        self.status = True
        self.timer = self.create_timer(5.0, self.timer_callback)  # 5초 간격

    def timer_callback(self):
        msg = Bool()
        msg.data = self.status
        self.publisher_.publish(msg)
        self.get_logger().info(f'🚗 Published: parking_ok = {msg.data}')
        self.status = not self.status  # True <-> False 토글

def main(args=None):
    rclpy.init(args=args)
    node = ParkingStatusPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
