from setuptools import find_packages, setup

package_name = 'parking_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
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
            'global_path_pub_node = parking_pkg.global_path_pub:main',
            'parking_path_pub_node = parking_pkg.parking_path_pub:main',
            'gps_map_pub_node = parking_pkg.gps_map_pub:main',
            'local_pub_node = parking_pkg.local_pub:main',
            'erp42_control_node = parking_pkg.erp42_control:main',
            'marker_control_node = parking_pkg.marker_control:main',
            'udp_control_node = parking_pkg.udp_control:main',
            'pure_pursuit_udp_node = parking_pkg.pure_pursuit_udp:main',
            'straight_drive_node = parking_pkg.straight_drive:main',
            'morai_udp_erp = parking_pkg.morai_udp_erp:main',
            'erp_ctrl_cmd_to_udp = parking_pkg.epr_ctrl_cmd_to_udp:main',
            'erp42_status_to_cmd = parking_pkg.erp42_status_to_cmd:main',
            'two_gps_to_path = parking_pkg.two_gps_to_path:main',
            'pure_pursuit = parking_pkg.pure_pursuit:main',
            'path_manager = parking_pkg.path_manager:main',
            'parking_diagonal_sequence = parking_pkg.parking_diagonal_sequence:main',
            'parking_parallel_sequence = parking_pkg.parking_parallel_sequence:main',
            'plusspeedpark1 = parking_pkg.plusspeedpark1:main',
        ],
    },
)
