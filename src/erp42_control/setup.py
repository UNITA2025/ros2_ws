from setuptools import find_packages, setup

package_name = 'erp42_control'

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
    maintainer='jjm',
    maintainer_email='whwoals159874@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'erp_status_node = erp42_control.erp_status:main',
            'spin_test_node = erp42_control.spin_test:main',
            'ByteHandler_node = erp42_control.ByteHandler:main',
            'ErpSerialHandler_node = erp42_control.ErpSerialHandler:main',
            'parking_node = erp42_control.parking:main',
            'publish_parking_signal = erp42_control.publish_parking_signal:main',
            'parking_detecter_node = erp42_control.parking_detecter:main',
            'deliver_node = erp42_control.deliver_node:main',
            'brake_test_node = erp42_control.brake_test:main',
        ],
    },
)
