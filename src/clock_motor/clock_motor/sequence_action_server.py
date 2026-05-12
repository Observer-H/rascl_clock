import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from clock_interfaces.action import ClockSequence
from clock_interfaces.srv import MoveToHour


class SequenceActionServer(Node):
    def __init__(self):
        super().__init__("sequence_action_server")
        self.client = self.create_client(MoveToHour, "move_to_hour")
        self.server = ActionServer(
            self,
            ClockSequence,
            "clock_sequence",
            self.execute_cb,
        )

    def execute_cb(self, goal_handle):
        result = ClockSequence.Result()

        if not self.client.wait_for_service(timeout_sec=5.0):
            result.success = False
            result.message = "move_to_hour service not available"
            goal_handle.abort()
            return result

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

            request = MoveToHour.Request()
            request.hour = int(hour)
            future = self.client.call_async(request)
            rclpy.spin_until_future_complete(self, future)

            response = future.result()
            if response is None or not response.success:
                result.success = False
                result.message = response.message if response else "Service call failed"
                goal_handle.abort()
                return result

            time.sleep(max(0.0, goal_handle.request.dwell_time))

        result.success = True
        result.message = "Sequence completed"
        goal_handle.succeed()
        return result


def main():
    rclpy.init()
    node = SequenceActionServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
