from setuptools import find_packages, setup

package_name = 'simulation_path'

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
    maintainer_email='junssong@student.42seoul.kr',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'simulation_global_path_node = simulation_path.simulation_global_path:main',
            'simulation_local_path_node = simulation_path.simulation_local_path:main',
            'simulation_control_node = simulation_path.simulation_control:main',
        ],
    },
)
