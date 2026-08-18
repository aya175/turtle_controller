# turtle_controller

**MIA Robotics — Electrical Training 2026/27 — Task 7.1: Your First Robot Control**

A ROS2 (Jazzy) package that provides a single node combining keyboard teleoperation
and color-sensor perception for `turtlesim`.

## Overview

`controller_node` does two things simultaneously:

1. **Movement (publisher):** reads W/A/S/D or arrow-key input and publishes
   `geometry_msgs/msg/Twist` commands to `/turtle1/cmd_vel`, driving the turtle
   under **non-holonomic constraints** — only `linear.x` (forward/backward
   along the turtle's own heading) and `angular.z` (rotation about its own
   center) are ever set. `linear.y` is never touched, so the turtle can never
   strafe sideways, exactly like a car or a differential-drive robot.

2. **Perception (subscriber + publisher):** subscribes to
   `turtlesim/msg/Color` on `/turtle1/color_sensor`, determines which channel
   (R, G, or B) is dominant in the background the turtle is currently over,
   logs it via `get_logger()`, and republishes it as a `std_msgs/String` on
   `/dominant_color`.

## Package layout

```
turtle_controller/
├── turtle_controller/
│   ├── __init__.py
│   └── controller_node.py     # teleop + perception node
├── launch/
│   └── turtle_launch.py       # starts turtlesim_node + controller_node
├── package.xml
├── setup.py
└── setup.cfg
```

## Requirements met

| # | Requirement | Where |
|---|---|---|
| 1 | Package & node creation | `turtle_controller` package, single `controller_node` |
| 2 | Movement publisher (WASD/arrows → `/cmd_vel`, non-holonomic) | `publish_cmd()`, `_terminal_teleop_loop()` |
| 3 | Perception subscriber/publisher (major color, log + custom topic) | `color_callback()` |
| 4 | Parameters (no hardcoded topic names) | `declare_parameter()` calls in `__init__` |
| 5 | Launch file (turtlesim_node + controller together) | `launch/turtle_launch.py` |

## Bonus features

- **`use_stamped_vel`** (bool param): when `true`, dynamically switches the
  publisher to `geometry_msgs/msg/TwistStamped` with a real header timestamp
  (`self.get_clock().now().to_msg()`) instead of plain `Twist`.
- **Launch-time parameter overrides**: every parameter — ours *and*
  `turtlesim_node`'s own (`background_r/g/b`) — is exposed as a launch
  argument, so nothing needs to be edited in code.
- **`global_teleop`** (bool param): when `true`, uses `pynput` to capture
  keystrokes system-wide via the X11 session, so control works even when the
  terminal window isn't focused (instead of the default raw-terminal
  `termios`/`tty` reading, which does require the terminal to be active).

## Parameters

| Name | Default | Description |
|---|---|---|
| `cmd_vel_topic` | `/turtle1/cmd_vel` | Velocity command output topic |
| `color_sensor_topic` | `/turtle1/color_sensor` | Color sensor input topic |
| `dominant_color_topic` | `/dominant_color` | Computed dominant-color output topic |
| `linear_speed` | `2.0` | Forward/backward speed multiplier |
| `angular_speed` | `2.0` | Rotation speed multiplier |
| `use_stamped_vel` | `false` | Publish `TwistStamped` instead of `Twist` |
| `global_teleop` | `false` | Use global (pynput) key capture instead of terminal-only |

## Build & run

```bash
# from your workspace root
colcon build --packages-select turtle_controller
source install/setup.bash

# option A: launch everything together
ros2 launch turtle_controller turtle_launch.py

# option B: two terminals (recommended - avoids ros2 launch stdin quirks
# with raw keyboard reading)
ros2 run turtlesim turtlesim_node        # terminal 1
ros2 run turtle_controller controller_node   # terminal 2, click into this window
```

Control the turtle with **W / A / S / D** or the **arrow keys** in the
terminal running `controller_node`.

### Trying the bonuses

```bash
# TwistStamped messages
ros2 launch turtle_controller turtle_launch.py use_stamped_vel:=true

# override turtlesim's own background color at launch time
ros2 launch turtle_controller turtle_launch.py background_r:=255 background_g:=0 background_b:=0

# global teleop - works even if the terminal isn't the focused window
ros2 launch turtle_controller turtle_launch.py global_teleop:=true
```

### Inspecting topics/params while running

```bash
ros2 topic echo /dominant_color
ros2 topic echo /turtle1/cmd_vel
ros2 param list /turtle_controller_node
ros2 param get /turtle_controller_node use_stamped_vel
```

## Known limitation

`ros2 launch` does not reliably forward raw terminal keystrokes to a node's
`stdin` in every environment. If WASD input has no effect when using the
launch file, run `turtlesim_node` and `controller_node` in two separate
terminals instead (option B above) — this is standard, documented ROS2
behavior around keyboard-reading nodes, not a bug in this package.

## Author

Aya — M.I.A. Robotics, Electrical Team Training 2026/27
