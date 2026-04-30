from setuptools import setup
import os
from glob import glob

package_name = 'aeb_simulation'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mortadha Dhahri',
    maintainer_email='mortatha.dhahri@enicar.ucar.tn',
    description='Autonomous Emergency Braking simulation using ROS2 nodes',
    license='MIT',
    entry_points={
        'console_scripts': [
            'lidar_sim_node     = aeb_simulation.lidar_sim_node:main',
            'vehicle_state_node = aeb_simulation.vehicle_state_node:main',
            'aeb_decision_node  = aeb_simulation.aeb_decision_node:main',
            'logger_node = aeb_simulation.logger_node:main',
            'brake_actuator_node=aeb_simulation.brake_actuator_node:main',
            'shutdown_node = aeb_simulation.shutdown_node:main'
        ],
    },
)