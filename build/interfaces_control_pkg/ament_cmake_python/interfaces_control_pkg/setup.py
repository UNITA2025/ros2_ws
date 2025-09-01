from setuptools import find_packages
from setuptools import setup

setup(
    name='interfaces_control_pkg',
    version='0.0.0',
    packages=find_packages(
        include=('interfaces_control_pkg', 'interfaces_control_pkg.*')),
)
