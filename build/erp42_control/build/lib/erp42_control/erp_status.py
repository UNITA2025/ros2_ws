import rclpy
from rclpy.node import Node
from interfaces_control_pkg.msg import ErpStatusMsg
from erp42_control.ErpSerialHandler import ERPHandler  # 시리얼 핸들러 모듈

class ERP42StatusNode(Node):
    def __init__(self):
        super().__init__('erp42_status_node')
        self.publisher_ = self.create_publisher(ErpStatusMsg, 'erp42_status', 10)

        # 시리얼 핸들러 인스턴스 생성
        self.handler = ERPHandler(port='/dev/ttyUSB1', baudrate=115200)
        self.get_logger().info("ERP42 Status Node Started")

        # 주기적으로 상태 읽어오기 (20Hz)
        self.timer = self.create_timer(0.05, self.read_status)

    def read_status(self):
        msg = self.handler.read_status()
        if msg:
            self.publisher_.publish(msg)
            self.get_logger().info(
                f"[STATUS] speed={msg.speed}, steer={msg.steer}, brake={msg.brake}, gear={msg.gear}"
            )

def main(args=None):
    rclpy.init(args=args)
    node = ERP42StatusNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
