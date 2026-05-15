from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    description_share = Path(get_package_share_directory("clock_description"))
    robot_description = (description_share / "urdf" / "clock.urdf").read_text()
    controllers = str(description_share / "config" / "ros2_controllers.yaml")

    return LaunchDescription([
        Node(
            package="clock_motor",
            executable="motor_node",
            output="screen",
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),
        Node(
            package="controller_manager",
            executable="ros2_control_node",
            output="screen",
            parameters=[{"robot_description": robot_description}, controllers],
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
            output="screen",
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["clock_controller", "--controller-manager", "/controller_manager"],
            output="screen",
        ),
        Node(
            package="clock_motor",
            executable="sequence_action_server",
            output="screen",
        ),
    ])
