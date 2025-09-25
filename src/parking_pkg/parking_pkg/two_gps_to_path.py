#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from tf_transformations import quaternion_from_euler

R_EARTH = 6378137.0

def ll_to_local_xy(lat0, lon0, lat, lon):
    lat0r = math.radians(lat0)
    dx = math.radians(lon - lon0) * R_EARTH * math.cos(lat0r)
    dy = math.radians(lat - lat0) * R_EARTH
    return dx, dy

class TwoGpsToPath(Node):
    def __init__(self):
        super().__init__('two_gps_to_path')

        start_lat = 37.23923666666666
        start_lon = 126.77316
        goal_lat  = 37.23932833333333
        goal_lon  = 126.773285

        gx, gy = ll_to_local_xy(start_lat, start_lon, goal_lat, goal_lon)

        self.path = Path()
        self.path.header.frame_id = "odom"

        yaw = math.atan2(gy, gx)
        qx, qy, qz, qw = quaternion_from_euler(0, 0, yaw)

        num_points = 50
        for i in range(num_points+1):
            t = i / num_points
            px = t * gx
            py = t * gy

            ps = PoseStamped()
            ps.header.frame_id = "odom"
            ps.pose.position.x = px
            ps.pose.position.y = py
            ps.pose.orientation.x = qx
            ps.pose.orientation.y = qy
            ps.pose.orientation.z = qz
            ps.pose.orientation.w = qw
            self.path.poses.append(ps)

        self.pub = self.create_publisher(Path, "/waypoint_path", 10)
        self.timer = self.create_timer(0.2, self.on_timer)

    def on_timer(self):
        now = self.get_clock().now().to_msg()
        self.path.header.stamp = now
        for ps in self.path.poses:
            ps.header.stamp = now
        self.pub.publish(self.path)

def main():
    rclpy.init()
    node = TwoGpsToPath()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
