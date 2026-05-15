cmake_minimum_required(VERSION 3.8)
project(clock_hardware)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(clock_interfaces REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

add_library(clock_hardware SHARED
  src/clock_system.cpp
)
target_compile_features(clock_hardware PUBLIC cxx_std_17)
target_include_directories(clock_hardware PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(clock_hardware
  clock_interfaces
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
)

pluginlib_export_plugin_description_file(hardware_interface clock_hardware.xml)

install(
  DIRECTORY include/
  DESTINATION include
)
install(
  TARGETS clock_hardware
  EXPORT export_clock_hardware
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(
  FILES clock_hardware.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_export_targets(export_clock_hardware HAS_LIBRARY_TARGET)
ament_export_dependencies(hardware_interface pluginlib rclcpp rclcpp_lifecycle clock_interfaces)
ament_package()
