# Motor Clock ROS2 Structure

This is a compact Python-only ROS2 structure for the motor clock task.

The motor is homed on startup. After homing, the driver moves to raw position
`0`, and raw `0` counts is treated as clock `6`. The measured calibration is:

- `+330752` counts = clockwise 90 degrees
- one full revolution = `1323008` counts
- one hour mark = `110250.666...` counts

## Build

```bash
cd ros2_ws
colcon build
source install/setup.bash
```

## Run

```bash
ros2 launch clock_description clock_ros2_control.launch.py
```

This starts the Python EtherCAT backend, `controller_manager`, the
`clock_hardware/ClockHardware` ros2_control hardware interface,
`joint_state_broadcaster`, `forward_command_controller`, and the sequence action
server.

## Test single movement

```bash
ros2 service call /move_to_hour clock_interfaces/srv/MoveToHour "{hour: 9}"
```

## Run a sequence

```bash
ros2 action send_goal /clock_sequence clock_interfaces/action/ClockSequence "{hours: [3, 6, 12, 9, 3], dwell_time: 1.0}" --feedback
```

The sequence action publishes position commands to:

```text
/clock_controller/commands
```

Those commands pass through `forward_command_controller`, then into the
ros2_control hardware interface, and finally to the existing Python motor
backend through `/move_to_counts`.

## Where to paste your existing motor code

The driver is now implemented in:

```text
src/clock_motor/clock_motor/motor_driver.py
```

It uses these CiA402 objects:

```text
0x6040 controlword
0x6041 statusword
0x6060 modes of operation
0x6061 modes of operation display
0x6064 actual position
0x607A target position
0x6081 profile velocity
0x6083 profile acceleration
0x6084 profile deceleration
0x6098 homing method
0x6099 homing speeds
0x609A homing acceleration
```

The public methods are:

```text
connect()
home()
move_to_counts(target_counts)
get_current_counts()
```
