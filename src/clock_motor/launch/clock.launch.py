from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="clock_motor",
            executable="motor_node",
            output="screen",
        ),
        Node(
            package="clock_motor",
            executable="sequence_action_server",
            output="screen",
        ),
    ])
