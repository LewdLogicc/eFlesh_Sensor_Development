#!/usr/bin/env python3

import subprocess
import time

# Joint positions
JOINTS = [
    'shoulder_pan_joint',
    'shoulder_lift_joint',
    'elbow_joint',
    'wrist_1_joint',
    'wrist_2_joint',
    'wrist_3_joint'
]


POSITIONS = [0.2618, -0.2618]

OTHER_JOINTS = [-1.57077, -0.00011, -1.57087, -0.00014, 0.000036]

def move_robot(angle):

    positions = [angle] + OTHER_JOINTS

    command = f"""
    {{trajectory: {{
      joint_names: {JOINTS},
      points: [{{
        positions: {positions},
        time_from_start: {{sec: 5}}
      }}]
    }}}}
    """

    result = subprocess.run([
        "ros2", "action", "send_goal",
        "/scaled_joint_trajectory_controller/follow_joint_trajectory",
        "control_msgs/action/FollowJointTrajectory",
        command
    ], capture_output=True, text=True)

    output = result.stdout + result.stderr

    if result.returncode != 0 or "SUCCEEDED" not in output:
        print("Movement did not complete successfully.")
        print(output)
        return False

    return True


print("Starting UR5 movement loop.")
print("Press Ctrl+C to stop.")

try:
    while True:
        for angle in POSITIONS:
            print(f"Moving shoulder pan to {angle:.4f} rad")

            if not move_robot(angle):
                raise RuntimeError("Stopping loop due to unsuccessful movement.")

except KeyboardInterrupt:
    print("\nMovement loop stopped.")

except RuntimeError as error:
    print(error)
