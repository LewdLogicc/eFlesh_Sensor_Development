#Shea Retallack
#Student number: 21511211
#Curtin University
#THE PURPOSE OF THIS FILE IS TO LAUNCH THE UR5 DRIVER AND ALL OF THE NODES AT THE SAME TIME RATHER THAN INDIVIDUALLY

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    
    ur5_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ur_robot_driver'),
                'launch',
                'ur_control.launch.py'
            )
        ),
        launch_arguments={
            'ur_type': 'ur5',
            'robot_ip': '192.168.56.101',
            'kinematics_params_file': '/home/shea/ur5_calibration.yaml',
            'launch_rviz': 'false'
        }.items()
    )

    eflesh_publisher = Node(
        package='eflesh_sensor',
        executable='eflesh_publisher',
        name='eflesh_publisher',
        output='screen'
    )

    collision_detector = Node(
        package='eflesh_sensor',
        executable='collision_detector',
        name='collision_detector',
        output='screen'
    )

    ur5_collision_monitor = Node(
        package='eflesh_sensor',
        executable='ur5_collision_monitor',
        name='ur5_collision_monitor',
        output='screen'
    )

    return LaunchDescription([
        ur5_driver,
        eflesh_publisher,
        collision_detector,
        ur5_collision_monitor
    ])