#Shea Retallack
#Student number: 21511211
#Curtin University
#THE PURPOSE OF THIS FILE IS TO HANDLE THE COLLISION DETECTION BASED ON THE VALUES PUBLISHED TO /EFLESH/DATA
#IF A CONTACT IS DETECTED (DEPENDANT ON BASELINE VALUES) THIS NODE RETURNS WHETHER A CONTACT WITH THE EFLESH SENSORS HAS BEEN MADE OR NOT
#IF THE CHANGE EXCEEDS THE PRESET BASELINE VALUES, A COLLISION IS PUBLISHED TO /EFLESH/COLLISION

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, Bool
import math


class CollisionDetector(Node):

    def __init__(self):
        super().__init__('collision_detector')

        self.subscription = self.create_subscription(
            Float64MultiArray,
            '/eflesh/data',
            self.sensor_callback,
            10
        )

        self.collision_publisher = self.create_publisher(
            Bool,
            '/eflesh/collision',
            10
        )

        #detection settings
        self.COLLISION_THRESHOLD = 150.0
        self.RELEASE_THRESHOLD = 75.0

       
        self.baseline = None

        #contact detection active
        self.collision_active = False

        self.get_logger().info('Collision detector started')
        self.get_logger().info(
            f'Collision threshold: {self.COLLISION_THRESHOLD}'
        )

    def sensor_callback(self, msg):

        data = list(msg.data)

        # 3 modules * 5 sensors * 3 values (XYZ) = 45 values
        if len(data) != 45:
            self.get_logger().warning(
                f'Expected 45 values, received {len(data)}'
            )
            return

        #get baseline magnetometer values
        if self.baseline is None:
            self.baseline = data.copy()
            self.get_logger().info('Baseline established')
            return

        max_change = 0.0
        max_module = 0
        max_sensor = 0

        for sensor_index in range(15):

            base = sensor_index * 3

            dx = data[base]     - self.baseline[base]
            dy = data[base + 1] - self.baseline[base + 1]
            dz = data[base + 2] - self.baseline[base + 2]

            #calculate vector magnitude 
            change = math.sqrt(
                dx * dx +
                dy * dy +
                dz * dz
            )

            if change > max_change:
                max_change = change

                max_module = sensor_index // 5
                max_sensor = sensor_index % 5

        #contact initiated
        if (
            not self.collision_active
            and max_change >= self.COLLISION_THRESHOLD
        ):
            self.collision_active = True
            collision_msg = Bool()
            collision_msg.data = True
            self.collision_publisher.publish(collision_msg)
            self.get_logger().warning(
                f'COLLISION DETECTED | '
                f'Module M{max_module} | '
                f'Sensor {max_sensor} | '
                f'Magnitude {max_change:.2f}'
            )
        #contact released
        elif (
            self.collision_active
            and max_change <= self.RELEASE_THRESHOLD
        ):
            self.collision_active = False
            collision_msg = Bool()
            collision_msg.data = False
            self.collision_publisher.publish(collision_msg)
            self.get_logger().info(
                'COLLISION CLEARED'
            )
        self.get_logger().info(
            f'Max magnetic field change: {max_change:.2f}',
            throttle_duration_sec=1.0
        )        

def main(args=None):

    rclpy.init(args=args)

    node = CollisionDetector()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
