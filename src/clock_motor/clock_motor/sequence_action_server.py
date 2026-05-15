import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

from clock_interfaces.action import ClockSequence
from .clock_mapping import hour_to_radians


class SequenceActionServer(Node):
    def __init__(self):
        super().__init__("sequence_action_server")
        # 中文：sequence 现在通过 feed-forward controller 发命令，不再直接调用电机 service。
        # English: The sequence now commands the feed-forward controller, not the motor service directly.
        self.publisher = self.create_publisher(
            Float64MultiArray,
            "/clock_controller/commands",
            10,
        )
        self.server = ActionServer(
            self,
            ClockSequence,
            "clock_sequence",
            self.execute_cb,
        )

    def execute_cb(self, goal_handle):
        result = ClockSequence.Result()

        for index, hour in enumerate(goal_handle.request.hours):
            if goal_handle.is_cancel_requested:
                result.success = False
                result.message = "Canceled"
                goal_handle.canceled()
                return result

            feedback = ClockSequence.Feedback()
            feedback.current_hour = int(hour)
            feedback.current_index = index
            goal_handle.publish_feedback(feedback)

            msg = Float64MultiArray()
            msg.data = [hour_to_radians(int(hour))]
            self.publisher.publish(msg)
            self.get_logger().info(f"Published hour {hour} as {msg.data[0]:.3f} rad")

            time.sleep(max(0.0, goal_handle.request.dwell_time))

        result.success = True
        result.message = "Sequence completed"
        goal_handle.succeed()
        return result


def main():
    rclpy.init()
    node = SequenceActionServer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
