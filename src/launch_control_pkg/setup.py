from setuptools import find_packages, setup

package_name = 'launch_control_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/main.launch.py']),  # ← 추가
        ('share/' + package_name + '/launch', ['launch/parking_path_manger.launch.py']),  # ← 추가
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='unita',
    maintainer_email='unita159874@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        'global_path_pub = erp42_path.global_path_pub:main',
        'local_pub = erp42_path.local_pub:main',
        'erp_control = erp42_path.erp_control:main',
        'gps_map_pub = erp42_path.gps_map_pub:main',
   	    'marker_control_node = erp42_path.marker_control:main',
        'ErpSerialHandler_pub = erp42_control.ErpSerialHandler:main',
        ],
    },
)
