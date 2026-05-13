import rclpy
from rclpy.node import Node

from clock_interfaces.srv import Home, MoveToCounts, MoveToHour

from .clock_mapping import hour_to_counts, nearest_equivalent_target
from .motor_driver import MotorDriver


class MotorNode(Node):
    def __init__(self):
        super().__init__("motor_node")
        # 中文：这里集中保存底层驱动默认配置，launch 文件保持最简。
        # English: Keep low-level driver defaults here and keep the launch file minimal.
        self.declare_parameter("ifname", "eth0")
        self.declare_parameter("slave_index", 0)
        self.declare_parameter("homing_method", 19)
        self.declare_parameter("homing_speed_switch", 400)
        self.declare_parameter("homing_speed_zero", 100)
        self.declare_parameter("homing_acceleration", 50)
        self.declare_parameter("profile_velocity", 400)
        self.declare_parameter("profile_acceleration", 100)
        self.declare_parameter("profile_deceleration", 100)
        self.declare_parameter("move_timeout", 20.0)
        self.declare_parameter("home_timeout", 30.0)
        self.declare_parameter("position_tolerance", 200)
        self.declare_parameter("move_to_zero_after_homing", True)

        self.driver = MotorDriver(
            ifname=self.get_parameter("ifname").value,
            slave_index=self.get_parameter("slave_index").value,
            homing_method=self.get_parameter("homing_method").value,
            homing_speed_switch=self.get_parameter("homing_speed_switch").value,
            homing_speed_zero=self.get_parameter("homing_speed_zero").value,
            homing_acceleration=self.get_parameter("homing_acceleration").value,
            profile_velocity=self.get_parameter("profile_velocity").value,
            profile_acceleration=self.get_parameter("profile_acceleration").value,
            profile_deceleration=self.get_parameter("profile_deceleration").value,
            move_timeout=self.get_parameter("move_timeout").value,
            home_timeout=self.get_parameter("home_timeout").value,
            position_tolerance=self.get_parameter("position_tolerance").value,
            move_to_zero_after_homing=self.get_parameter("move_to_zero_after_homing").value,
        )
        self.get_logger().info("Connecting EtherCAT motor...")
        self.driver.connect()
        self.get_logger().info("Running homing...")
        self.driver.home()

        self.create_service(Home, "home", self.home_cb)
        self.create_service(MoveToCounts, "move_to_counts", self.move_to_counts_cb)
        self.create_service(MoveToHour, "move_to_hour", self.move_to_hour_cb)
        self.get_logger().info("Motor ready: raw position 0 is clock 6.")

    def home_cb(self, request, response):
        del request
        try:
            self.driver.home()
            response.success = True
            response.message = "Homed. Raw position 0 is clock 6."
        except Exception as exc:
            response.success = False
            response.message = str(exc)
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
    try:
        rclpy.spin(node)
    finally:
        node.driver.close()
        node.destroy_node()
        rclpy.shutdown()
