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
    maintainer='songsong',
    maintainer_email='whwoals159874@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'global_path_pub_node = erp42_path.global_path_pub:main',
            'gps_map_pub_node = erp42_path.gps_map_pub:main',
            'local_pub_node = erp42_path.local_pub:main',
            'erp42_control_node = erp42_path.erp42_control:main',
            'marker_control_node = erp42_path.marker_control:main',
            'udp_control_node = erp42_path.udp_control:main',
            'erp42status_to_cmdctrl_node = erp42_path.erp42status_to_cmdctrl:main',
        ],
    },
)
