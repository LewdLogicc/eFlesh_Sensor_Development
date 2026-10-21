#Shea Retallack
#Student number: 21511211
#Curtin University
#THE PURPOSE OF THIS FILE IS TO PAUSE/RESUME MOVEMENT BASED IF CONTACT/COLLISION IS DETECTED OR RELEASED

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

class UR5CollisionMonitor(Node):

    def __init__(self):
        super().__init__('ur5_collision_monitor')
        self.TEST_MODE = False
        self.pause_client = self.create_client(
            Trigger,
            '/dashboard_client/pause'
        )

        self.play_client = self.create_client(
            Trigger,
            '/dashboard_client/play'
        )     

        self.subscription = self.create_subscription(
            Bool,
            '/eflesh/collision',
            self.collision_callback,
            10
        )

        self.get_logger().info('UR5 collision monitor started')
        self.get_logger().info('Waiting for eFlesh collision signal')

    def collision_callback(self, msg):

        if msg.data:
            self.get_logger().warning(
                'EFLESH COLLISION RECEIVED - UR5 PAUSE REQUESTED'
            )

            self.pause_robot()

        else:
            self.get_logger().info(
                'eFlesh contact cleared - UR5 RESUME REQUESTED'
            )

            self.resume_robot()

    def pause_robot(self):

        if not self.pause_client.service_is_ready():
            self.get_logger().error(
                'UR5 pause service is not available'
            )
            return

        self.get_logger().warning(
            'Sending UR5 pause command'
        )

        request = Trigger.Request()
        self.pause_client.call_async(request)


    def resume_robot(self):

        if not self.play_client.service_is_ready():
            self.get_logger().error(
                'UR5 play service is not available'
            )
            return

        self.get_logger().info(
            'Sending UR5 resume command'
        )

        request = Trigger.Request()
        self.play_client.call_async(request)

def main(args=None):

    rclpy.init(args=args)

    node = UR5CollisionMonitor()

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
