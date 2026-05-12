import rclpy
from rclpy.node import Node

from clock_interfaces.srv import Home, MoveToCounts, MoveToHour

from .clock_mapping import hour_to_counts, nearest_equivalent_target
from .motor_driver import MotorDriver


class MotorNode(Node):
    def __init__(self):
        super().__init__("motor_node")
        self.driver = MotorDriver()
        self.driver.connect()
        self.driver.home()

        self.create_service(Home, "home", self.home_cb)
        self.create_service(MoveToCounts, "move_to_counts", self.move_to_counts_cb)
        self.create_service(MoveToHour, "move_to_hour", self.move_to_hour_cb)
        self.get_logger().info("Motor ready: homed position is clock 6.")

    def home_cb(self, request, response):
        del request
        self.driver.home()
        response.success = True
        response.message = "Homed. Logical zero is clock 6."
        return response

    def move_to_counts_cb(self, request, response):
        return self._move_to_counts(request.counts, response)

    def move_to_hour_cb(self, request, response):
        current = self.driver.get_current_counts()
        raw_target = hour_to_counts(request.hour)
        target = nearest_equivalent_target(current, raw_target)
        return self._move_to_counts(target, response)

    def _move_to_counts(self, target_counts, response):
        try:
            self.driver.move_to_counts(target_counts)
            response.success = True
            response.message = "OK"
            response.target_counts = int(target_counts)
        except Exception as exc:
            response.success = False
            response.message = str(exc)
            response.target_counts = int(target_counts)
        return response


def main():
    rclpy.init()
    node = MotorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
