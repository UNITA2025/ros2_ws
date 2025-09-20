from setuptools import find_packages, setup

package_name = 'erp42_path'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='unita',
    maintainer_email='whwoals159874@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'global_path_pub_node = erp42_path.global_path_pub:main',
            'parking_path_pub_node = erp42_path.parking_path_pub:main',
            'gps_map_pub_node = erp42_path.gps_map_pub:main',
            'local_pub_node = erp42_path.local_pub:main',
            'erp42_control_node = erp42_path.erp42_control:main',
            'marker_control_node = erp42_path.marker_control:main',
            'udp_control_node = erp42_path.udp_control:main',
            'pure_pursuit_udp_node = erp42_path.pure_pursuit_udp:main',
            'straight_drive_node = erp42_path.straight_drive:main',
            'morai_udp_erp = erp42_path.morai_udp_erp:main',
            'erp_ctrl_cmd_to_udp = erp42_path.epr_ctrl_cmd_to_udp:main',
            'erp42_status_to_cmd = erp42_path.erp42_status_to_cmd:main',
            'two_gps_to_path = erp42_path.two_gps_to_path:main',
            'pure_pursuit = erp42_path.pure_pursuit:main',
        ],
    },
)
