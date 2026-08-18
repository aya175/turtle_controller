#!/usr/bin/env python3
"""
controller_node.py

Task 7.1 - Your First Robot Control

Single ROS2 node that:
  1. Reads keyboard input (WASD / Arrow keys) and publishes velocity
     commands to drive turtlesim's turtle under NON-HOLONOMIC
     constraints: only linear.x (forward/backward along the turtle's
     own heading) and angular.z (rotation about its own center) are
     ever published. linear.y is never touched -> the turtle can
     never strafe sideways, exactly like a car or differential-drive
     robot.
  2. Subscribes to the turtle's color sensor topic, computes the
     dominant ("major") color channel (Red, Green or Blue) of the
     background the turtle is currently over, logs it, and
     republishes it on a custom topic.

Bonus features implemented:
  - use_stamped_vel (bool param): dynamically switch between
    geometry_msgs/Twist and geometry_msgs/TwistStamped (with a real
    header timestamp from the node's clock).
  - global_teleop (bool param): if True, uses pynput to capture
    keystrokes system-wide (terminal does not need to be focused).
    If False (default), uses classic raw-terminal reading, which
    DOES require the terminal window to be the active/focused
    window.

Author: Aya
"""

import sys
import threading
import termios
import tty

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, TwistStamped
from turtlesim.msg import Color
from std_msgs.msg import String


# ---------------------------------------------------------------------------
# key -> (linear.x multiplier, angular.z multiplier)
# ---------------------------------------------------------------------------
MOVE_BINDINGS = {
    'w': (1.0, 0.0),
    's': (-1.0, 0.0),
    'a': (0.0, 1.0),
    'd': (0.0, -1.0),
    'UP': (1.0, 0.0),
    'DOWN': (-1.0, 0.0),
    'LEFT': (0.0, 1.0),
    'RIGHT': (0.0, -1.0),
}


class TurtleControllerNode(Node):

    def __init__(self):
        super().__init__('turtle_controller_node')

        # ------------------------------------------------------------
        # Requirement 4: Parameters (never hardcode topic names)
        # ------------------------------------------------------------
        self.declare_parameter('cmd_vel_topic', '/turtle1/cmd_vel')
        self.declare_parameter('color_sensor_topic', '/turtle1/color_sensor')
        self.declare_parameter('dominant_color_topic', '/dominant_color')
        self.declare_parameter('linear_speed', 2.0)
        self.declare_parameter('angular_speed', 2.0)
        self.declare_parameter('use_stamped_vel', False)   # Bonus 2
        self.declare_parameter('global_teleop', False)     # Bonus 3

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.color_topic = self.get_parameter('color_sensor_topic').value
        self.dominant_topic = self.get_parameter('dominant_color_topic').value
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.use_stamped_vel = self.get_parameter('use_stamped_vel').value
        self.global_teleop = self.get_parameter('global_teleop').value

        # ------------------------------------------------------------
        # Publishers
        # ------------------------------------------------------------
        msg_type = TwistStamped if self.use_stamped_vel else Twist
        self.cmd_vel_pub = self.create_publisher(msg_type, self.cmd_vel_topic, 10)
        self.dominant_color_pub = self.create_publisher(String, self.dominant_topic, 10)

        # ------------------------------------------------------------
        # Requirement 3: Perception subscriber
        # ------------------------------------------------------------
        self.color_sub = self.create_subscription(
            Color, self.color_topic, self.color_callback, 10)

        self.get_logger().info(
            "Controller started with:\n"
            f"  cmd_vel_topic        = {self.cmd_vel_topic}\n"
            f"  color_sensor_topic   = {self.color_topic}\n"
            f"  dominant_color_topic = {self.dominant_topic}\n"
            f"  use_stamped_vel      = {self.use_stamped_vel}\n"
            f"  global_teleop        = {self.global_teleop}"
        )

        # ------------------------------------------------------------
        # Start the appropriate keyboard-reading thread
        # ------------------------------------------------------------
        self._stop_flag = False
        if self.global_teleop:
            self._start_global_listener()
        else:
            self._teleop_thread = threading.Thread(
                target=self._terminal_teleop_loop, daemon=True)
            self._teleop_thread.start()

    # ------------------------------------------------------------
    # Requirement 3 callback: compute + log + publish dominant color
    # ------------------------------------------------------------
    def color_callback(self, msg: Color):
        channels = {'Red': msg.r, 'Green': msg.g, 'Blue': msg.b}
        major_color = max(channels, key=channels.get)

        # Action 1: log via standard ROS2 logging tools
        self.get_logger().info(
            f"Major color: {major_color}  (R={msg.r}, G={msg.g}, B={msg.b})"
        )

        # Action 2: publish to custom topic
        out = String()
        out.data = major_color
        self.dominant_color_pub.publish(out)

    # ------------------------------------------------------------
    # Requirement 2: publish movement command (non-holonomic:
    # only linear.x and angular.z are ever set)
    # ------------------------------------------------------------
    def publish_cmd(self, linear_x: float, angular_z: float):
        if self.use_stamped_vel:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist.linear.x = linear_x
            msg.twist.angular.z = angular_z
        else:
            msg = Twist()
            msg.linear.x = linear_x
            msg.angular.z = angular_z
        self.cmd_vel_pub.publish(msg)

    # ------------------------------------------------------------
    # Default teleop: raw terminal reading (requires terminal focus)
    # ------------------------------------------------------------
    def _get_key(self, settings):
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        if key == '\x1b':  # start of an arrow-key escape sequence
            key += sys.stdin.read(2)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

    def _terminal_teleop_loop(self):
        settings = termios.tcgetattr(sys.stdin)
        self.get_logger().info(
            "Terminal teleop active. Use W/A/S/D or Arrow keys. CTRL+C to quit."
        )
        try:
            while rclpy.ok() and not self._stop_flag:
                key = self._get_key(settings)

                if key == '\x1b[A':
                    lin, ang = MOVE_BINDINGS['UP']
                elif key == '\x1b[B':
                    lin, ang = MOVE_BINDINGS['DOWN']
                elif key == '\x1b[C':
                    lin, ang = MOVE_BINDINGS['RIGHT']
                elif key == '\x1b[D':
                    lin, ang = MOVE_BINDINGS['LEFT']
                elif key.lower() in ('w', 'a', 's', 'd'):
                    lin, ang = MOVE_BINDINGS[key.lower()]
                elif key == '\x03':  # CTRL+C
                    break
                else:
                    lin, ang = 0.0, 0.0

                self.publish_cmd(lin * self.linear_speed, ang * self.angular_speed)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

    # ------------------------------------------------------------
    # Bonus 3: global teleop using pynput (works without terminal focus)
    # ------------------------------------------------------------
    def _start_global_listener(self):
        try:
            from pynput import keyboard
        except ImportError:
            self.get_logger().error(
                "pynput is not installed. Run: "
                "pip install pynput --break-system-packages"
            )
            return

        self.get_logger().info(
            "Global teleop active (pynput). Works even if the terminal "
            "window is not focused."
        )

        def on_press(key):
            try:
                k = key.char.lower()
                if k in ('w', 'a', 's', 'd'):
                    lin, ang = MOVE_BINDINGS[k]
                    self.publish_cmd(lin * self.linear_speed, ang * self.angular_speed)
            except AttributeError:
                mapping = {
                    keyboard.Key.up: 'UP',
                    keyboard.Key.down: 'DOWN',
                    keyboard.Key.left: 'LEFT',
                    keyboard.Key.right: 'RIGHT',
                }
                if key in mapping:
                    lin, ang = MOVE_BINDINGS[mapping[key]]
                    self.publish_cmd(lin * self.linear_speed, ang * self.angular_speed)

        def on_release(key):
            # stop the turtle the moment the key is released
            self.publish_cmd(0.0, 0.0)

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()

    def destroy_node(self):
        self._stop_flag = True
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TurtleControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
