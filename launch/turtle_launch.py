"""
turtle_launch.py

Requirement 5: launches turtlesim_node + our controller node together.
Bonus 1: every parameter (ours AND turtlesim_node's) is exposed as a
launch argument, so nothing needs to be edited in code -- e.g.:

    ros2 launch turtle_controller turtle_launch.py \
        background_r:=255 background_g:=0 background_b:=0 \
        use_stamped_vel:=true global_teleop:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ---- turtlesim_node's own params, exposed for override (Bonus 1) ----
    background_r_arg = DeclareLaunchArgument('background_r', default_value='69')
    background_g_arg = DeclareLaunchArgument('background_g', default_value='86')
    background_b_arg = DeclareLaunchArgument('background_b', default_value='255')

    # ---- our controller node's params, exposed for override ----
    cmd_vel_topic_arg = DeclareLaunchArgument(
        'cmd_vel_topic', default_value='/turtle1/cmd_vel')
    color_topic_arg = DeclareLaunchArgument(
        'color_sensor_topic', default_value='/turtle1/color_sensor')
    dominant_topic_arg = DeclareLaunchArgument(
        'dominant_color_topic', default_value='/dominant_color')
    linear_speed_arg = DeclareLaunchArgument('linear_speed', default_value='2.0')
    angular_speed_arg = DeclareLaunchArgument('angular_speed', default_value='2.0')
    use_stamped_arg = DeclareLaunchArgument('use_stamped_vel', default_value='false')
    global_teleop_arg = DeclareLaunchArgument('global_teleop', default_value='false')

    turtlesim_node = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
        output='screen',
        parameters=[{
            'background_r': LaunchConfiguration('background_r'),
            'background_g': LaunchConfiguration('background_g'),
            'background_b': LaunchConfiguration('background_b'),
        }],
    )

    controller_node = Node(
        package='turtle_controller',
        executable='controller_node',
        name='turtle_controller_node',
        output='screen',
        emulate_tty=True,   # needed so raw-terminal key reading works
        parameters=[{
            'cmd_vel_topic': LaunchConfiguration('cmd_vel_topic'),
            'color_sensor_topic': LaunchConfiguration('color_sensor_topic'),
            'dominant_color_topic': LaunchConfiguration('dominant_color_topic'),
            'linear_speed': LaunchConfiguration('linear_speed'),
            'angular_speed': LaunchConfiguration('angular_speed'),
            'use_stamped_vel': LaunchConfiguration('use_stamped_vel'),
            'global_teleop': LaunchConfiguration('global_teleop'),
        }],
    )

    return LaunchDescription([
        background_r_arg, background_g_arg, background_b_arg,
        cmd_vel_topic_arg, color_topic_arg, dominant_topic_arg,
        linear_speed_arg, angular_speed_arg,
        use_stamped_arg, global_teleop_arg,
        turtlesim_node,
        controller_node,
    ])
