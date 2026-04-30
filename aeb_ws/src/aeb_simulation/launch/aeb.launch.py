from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.actions import EmitEvent
from launch.events import Shutdown
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('aeb_simulation'),
        'config', 'params.yaml'
    )

    lidar_node = Node(
        package='aeb_simulation',
        executable='lidar_sim_node',
        name='lidar_sim_node',
        parameters=[config],
        output='screen',
    )

    vehicle_node = Node(
        package='aeb_simulation',
        executable='vehicle_state_node',
        name='vehicle_state_node',
        parameters=[config],
        output='screen',
    )

    decision_node = Node(
        package='aeb_simulation',
        executable='aeb_decision_node',
        name='aeb_decision_node',
        parameters=[config],
        output='screen',
    )

    brake_node = Node(
        package='aeb_simulation',
        executable='brake_actuator_node',
        name='brake_actuator_node',
        output='screen',
    )

    logger_node = Node(
        package='aeb_simulation',
        executable='logger_node',
        name='logger_node',
        output='screen',
    )

    shutdown_node = Node(
        package='aeb_simulation',
        executable='shutdown_node',
        name='shutdown_node',
        output='screen',
    )

    # when shutdown_node exits (sys.exit(0)) — tear down everything
    shutdown_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=shutdown_node,
            on_exit=[EmitEvent(event=Shutdown())]
        )
    )

    return LaunchDescription([
        lidar_node,
        vehicle_node,
        decision_node,
        brake_node,
        logger_node,
        shutdown_node,
        shutdown_handler,
    ])