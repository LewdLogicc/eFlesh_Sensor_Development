#Shea Retallack
#Student number: 21511211
#Curtin University
#THE PURPOSE OF THIS FILE IS TO READ THE EFLESH SENSOR VALUES FROM SERIAL PORT AND PUBLISH TO /EFLESH/DATA ROS2 TOPIC

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import serial


class EFleshPublisher(Node):

    def __init__(self):
        super().__init__('eflesh_publisher')

        self.publisher_ = self.create_publisher(
            Float64MultiArray,
            '/eflesh/data',
            10
        )

        self.serial_port = serial.Serial(
            '/dev/ttyACM0',
            115200,
            timeout=0.1
        )

        
        #store latest reading from sensors M0, M1 and M2
        self.modules = {
            'M0': None,
            'M1': None,
            'M2': None
        }

        self.get_logger().info(
            'eFlesh connected on /dev/ttyACM0'
        )

        self.serial_port.reset_input_buffer()

        self.timer = self.create_timer(
            0.01,
            self.read_sensor
        )

    def read_sensor(self):

        while self.serial_port.in_waiting:

            line = self.serial_port.readline().decode(
                'utf-8',
                errors='ignore'
            ).strip()

            if not line:
                continue

            parts = line.split(',')

            module = parts[0]

            if module not in self.modules:
                continue

            try:
                values = [
                    float(value)
                    for value in parts[1:]
                ]

            except ValueError:
                self.get_logger().warning(
                    f'Could not parse: {line}'
                )
                continue

            #5 sensors return 3 values = 15 values total
            if len(values) != 15:
                self.get_logger().warning(
                    f'{module} contained {len(values)} values, expected 15'
                )
                continue

            self.modules[module] = values

            #publish values after receiving final sensor value M2 if M1 and M2 have already been established
            if (
                module == 'M2'
                and self.modules['M0'] is not None
                and self.modules['M1'] is not None
            ):

                combined = (
                    self.modules['M0']
                    + self.modules['M1']
                    + self.modules['M2']
                )

                msg = Float64MultiArray()
                msg.data = combined

                self.publisher_.publish(msg)

    def destroy_node(self):

        if self.serial_port.is_open:
            self.serial_port.close()

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = EFleshPublisher()

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
