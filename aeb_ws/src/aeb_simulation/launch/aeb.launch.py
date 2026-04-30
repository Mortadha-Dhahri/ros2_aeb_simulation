from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('aeb_simulation'),
        'config',
        'params.yaml'
    )

    return LaunchDescription([

        Node(
            package='aeb_simulation',
            executable='lidar_sim_node',
            name='lidar_sim_node',
            parameters=[config],
            output='screen',
        ),

        Node(
            package='aeb_simulation',
            executable='vehicle_state_node',
            name='vehicle_state_node',
            parameters=[config],
            output='screen',
        ),

        Node(
            package='aeb_simulation',
            executable='aeb_decision_node',
            name='aeb_decision_node',
            parameters=[config],
            output='screen',
        ),
        Node(
            package='aeb_simulation',
            executable='logger_node',
            name='logger_node',
            parameters=[config],
            output='screen',
        ),
        Node(
            package='aeb_simulation',
            executable='brake_actuator_node',
            name='brake_actuator_node',
            parameters=[config],
            output='screen',
        ),
    ])