#include "clock_hardware/clock_system.hpp"

#include <cmath>
#include <chrono>
#include <limits>
#include <stdexcept>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace clock_hardware
{

hardware_interface::CallbackReturn ClockHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  if (info_.joints.size() != 1) {
    RCLCPP_ERROR(rclcpp::get_logger("ClockHardware"), "Expected exactly one joint.");
    return hardware_interface::CallbackReturn::ERROR;
  }

  joint_name_ = info_.joints[0].name;
  move_service_name_ = info_.hardware_parameters.count("move_service")
    ? info_.hardware_parameters["move_service"]
    : "/move_to_counts";

  if (info_.hardware_parameters.count("counts_per_rev")) {
    counts_per_rev_ = std::stod(info_.hardware_parameters["counts_per_rev"]);
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ClockHardware::on_configure(
  const rclcpp_lifecycle::State &)
{
  // 中文：hardware interface 里创建一个小 ROS client，调用现有 Python 电机后端。
  // English: Create a small ROS client inside the hardware interface for the Python motor backend.
  node_ = rclcpp::Node::make_shared("clock_hardware_client");
  move_client_ = node_->create_client<clock_interfaces::srv::MoveToCounts>(move_service_name_);
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ClockHardware::on_activate(
  const rclcpp_lifecycle::State &)
{
  command_position_ = state_position_;
  first_write_ = true;
  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> ClockHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> interfaces;
  interfaces.emplace_back(joint_name_, hardware_interface::HW_IF_POSITION, &state_position_);
  interfaces.emplace_back(joint_name_, hardware_interface::HW_IF_VELOCITY, &state_velocity_);
  return interfaces;
}

std::vector<hardware_interface::CommandInterface> ClockHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> interfaces;
  interfaces.emplace_back(joint_name_, hardware_interface::HW_IF_POSITION, &command_position_);
  return interfaces;
}

hardware_interface::return_type ClockHardware::read(
  const rclcpp::Time &, const rclcpp::Duration &)
{
  // 中文：当前后端没有 position service；先把状态跟随最后命令，满足 joint_state_broadcaster。
  // English: The backend has no position service yet; mirror the last command for joint_state_broadcaster.
  state_position_ = command_position_;
  state_velocity_ = 0.0;
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type ClockHardware::write(
  const rclcpp::Time &, const rclcpp::Duration &)
{
  const int counts = radians_to_counts(command_position_);
  if (!first_write_ && counts == last_counts_) {
    return hardware_interface::return_type::OK;
  }

  if (!send_counts(counts)) {
    return hardware_interface::return_type::ERROR;
  }

  first_write_ = false;
  last_counts_ = counts;
  return hardware_interface::return_type::OK;
}

int ClockHardware::radians_to_counts(double radians) const
{
  constexpr double pi = 3.14159265358979323846;
  return static_cast<int>(std::llround((radians / (2.0 * pi)) * counts_per_rev_));
}

bool ClockHardware::send_counts(int counts)
{
  if (!move_client_->wait_for_service(std::chrono::milliseconds(500))) {
    RCLCPP_ERROR(node_->get_logger(), "Service %s is not available.", move_service_name_.c_str());
    return false;
  }

  auto request = std::make_shared<clock_interfaces::srv::MoveToCounts::Request>();
  request->counts = counts;
  auto future = move_client_->async_send_request(request);
  const auto result = rclcpp::spin_until_future_complete(node_, future, std::chrono::seconds(30));
  if (result != rclcpp::FutureReturnCode::SUCCESS) {
    RCLCPP_ERROR(node_->get_logger(), "Timed out sending target counts %d.", counts);
    return false;
  }

  const auto response = future.get();
  if (!response->success) {
    RCLCPP_ERROR(node_->get_logger(), "Motor backend rejected %d: %s", counts, response->message.c_str());
    return false;
  }
  return true;
}

}  // namespace clock_hardware

PLUGINLIB_EXPORT_CLASS(clock_hardware::ClockHardware, hardware_interface::SystemInterface)
