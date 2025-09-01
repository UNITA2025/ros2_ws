#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from pyproj import Proj, transform
from std_msgs.msg import Float32MultiArray
from nav_msgs.msg import Path, Odometry
from sensor_msgs.msg import NavSatFix
import os

class GPSMapPublisher(Node):
    def __init__(self):
        super().__init__('gps_to_utm_node')


        self.wgs84 = Proj(init='epsg:4326')
        self.utm52n = Proj(init='epsg:32652')



        self.gps_pub = self.create_publisher(Float32MultiArray, '/gps_map', 10)
        self.gps_sub = self.create_subscription(NavSatFix, '/gps/fix', self.gps_callback, 10) # odom 으로 바꿔줘야 할 수 도 있음

        # self.proj_UTM = Proj(proj='utm', zone=52, ellps='WGS84', preserve_units=False)

        self.utm_msg = Float32MultiArray()
        # 0. morai offset #
        # self.east_offset = 302473.63549866696
        # self.north_offset = 4123735.79407826

        self.east_offset = 290352.7758552486
        self.north_offset = 4139032.2486522812


        # 2. k-city highway offset #
        # self.east_offset = 302453.66136490076
        # self.north_offset = 4123699.2930204067



        self.is_gps_data = False

        self.create_timer(1.0, self.check_gps_status)

        self.get_logger().info("GPS to UTM node initialized.")

    def gps_callback(self, gps_msg):
        self.is_gps_data = True

        latitude = gps_msg.latitude
        longitude = gps_msg.longitude
        altitude = gps_msg.altitude




        # utm_y, utm_x = self.proj_UTM(longitude, latitude)  # pyprojëŠ” (lon, lat) ìˆœì„œ
        utm_x, utm_y = transform(self.wgs84,self.utm52n, longitude ,latitude)
        map_x = utm_x - self.east_offset
        map_y = utm_y - self.north_offset


        self.utm_msg.data = [map_x, map_y]
        self.gps_pub.publish(self.utm_msg)

        # os.system('clear')
        # print(f''' 
        # ----------------[ GPS data ]----------------
        #     latitude    : {latitude}
        #     longitude   : {longitude}
        #     altitude    : {altitude}

        #                      |
        #                      | apply Projection (utm 52 zone)
        #                      V

        # ------------------[ utm ]-------------------
        #       utm_x     : {utm_x}
        #       utm_y     : {utm_y}

        #                      |
        #                      | apply offset (east and north)
        #                      V
              
        # ------------------[ map ]-------------------
        # simulator map_x : {map_x}
        # simulator map_y : {map_y}
        # ''')

    def check_gps_status(self):
        if not self.is_gps_data:
            # os.system('clear')
            print("[1] can't subscribe '/gps/fix' topic... \n    please check your GPS sensor connection")
        self.is_gps_data = False


def main(args=None):
    rclpy.init(args=args)
    node = GPSMapPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

