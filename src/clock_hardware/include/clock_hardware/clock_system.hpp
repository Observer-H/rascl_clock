#pragma once

#include <memory>
#include <string>
#include <vector>

#include "clock_interfaces/srv/move_to_counts.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/state.hpp"

namespace clock_hardware
{

class ClockHardware : public hardware_interface::SystemInterface
{
public:
  hardware_interface::CallbackReturn on_init(const hardware_interface::HardwareInfo & info) override;
  hardware_interface::CallbackReturn on_configure(const rclcpp_lifecycle::State & previous_state) override;
  hardware_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State & previous_state) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  hardware_interface::return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override;
  hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  int radians_to_counts(double radians) const;
  bool send_counts(int counts);

  std::string joint_name_;
  std::string move_service_name_;
  double counts_per_rev_{1323008.0};
  double command_position_{0.0};
  double state_position_{0.0};
  double state_velocity_{0.0};
  int last_counts_{0};
  bool first_write_{true};

  rclcpp::Node::SharedPtr node_;
  rclcpp::Client<clock_interfaces::srv::MoveToCounts>::SharedPtr move_client_;
};

}  // namespace clock_hardware
