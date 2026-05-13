import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from clock_interfaces.action import ClockSequence
from clock_interfaces.srv import MoveToHour


class SequenceActionServer(Node):
    def __init__(self):
        super().__init__("sequence_action_server")
        # 中文：Action 节点不直接碰电机，只通过 service 请求 motor_node 移动。
        # English: The action node does not touch hardware; it asks motor_node via service.
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
            # 中文：允许用户取消正在执行的 sequence。
            # English: Allow the user to cancel a running sequence.
            if goal_handle.is_cancel_requested:
                result.success = False
                result.message = "Canceled"
                goal_handle.canceled()
                return result

            # 中文：反馈当前执行到第几个钟点。
            # English: Report which hour mark is being executed.
            feedback = ClockSequence.Feedback()
            feedback.current_hour = int(hour)
            feedback.current_index = index
            goal_handle.publish_feedback(feedback)

            # 中文：每一步 sequence 都转成一次 /move_to_hour service 请求。
            # English: Each sequence step becomes one /move_to_hour service request.
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
