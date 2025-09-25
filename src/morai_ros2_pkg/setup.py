from setuptools import find_packages, setup

package_name = 'morai_ros2_pkg'

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
            'morai_to_erp42_status = morai_ros2_pkg.morai_to_erp42_status:main',
            'erp_ctrl_cmd_to_udp = morai_ros2_pkg.epr_ctrl_cmd_to_udp:main',
        ],
    },
)
