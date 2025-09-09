from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='erp42_path',
            executable='global_path_pub_node',
            name='global_path_pub',
            output='screen'
        ),
        Node(
            package='erp42_path',
            executable='local_pub_node',
            name='local_pub',
            output='screen'
        ),
        # Node(
        #     package='erp42_path',
        #     executable='erp42_control_node',
        #     name='erp_control',
        #     output='screen'
        # ),        
        Node(
            package='erp42_path',
            executable='marker_control_node',
            name='marker_control',
            output='screen'
        ),
        # Node(
        #     package='erp42_path',
        #     executable='gps_map_pub_node',
        #     name='gps_map_pub',
        #     output='screen'
        # ),
        # Node(
        #     package='erp42_control',
        #     executable='ErpSerialHandler_node',  # 빌드 후 실행파일 이름
        #     name='ErpSerialHandler_pub',
        #     output='screen'
        # ),
    ])


if __name__ == '__main__':
    main()
