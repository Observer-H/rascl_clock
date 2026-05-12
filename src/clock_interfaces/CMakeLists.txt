cmake_minimum_required(VERSION 3.8)
project(clock_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/Home.srv"
  "srv/MoveToCounts.srv"
  "srv/MoveToHour.srv"
  "action/ClockSequence.action"
)

ament_package()
