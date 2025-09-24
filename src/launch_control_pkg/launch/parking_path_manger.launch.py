
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    global_path_node = Node (
        package='erp42_path',
        executable='global_path_pub_node',
        name='global_path',
        output='screen'
    )

    local_path_node = Node(
        package='erp42_path',
        executable='local_pub_node',
        name='local_path',
        output='screen'
    )

    parking_path_node = Node (
        package='erp42_path',
        executable='parking_path_pub_node',
        name='parking_path',
        output='screen'
    )

    path_manager_node = Node (
        package='erp42_path',
        executable='path_manager',
        name='parking_path',
        output='screen'
    )

    return LaunchDescription([
        global_path_node,
        parking_path_node,
        path_manager_node,
        local_path_node,
    ])