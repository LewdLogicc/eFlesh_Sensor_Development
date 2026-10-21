import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import csv
import time


class EFleshRecorder(Node):

    def __init__(self):
        super().__init__('eflesh_recorder')

        self.file = open('eflesh_data.csv', 'w', newline='')
        self.writer = csv.writer(self.file)

        header = ['time_s']

        for module in range(3):
            for sensor in range(5):
                for axis in ['Bx', 'By', 'Bz']:
                    header.append(f'M{module}_S{sensor}_{axis}')

        self.writer.writerow(header)

        self.start_time = time.monotonic()

        self.subscription = self.create_subscription(
            Float64MultiArray,
            '/eflesh/data',
            self.record,
            10
        )

        print('Recording eFlesh data... Press Ctrl+C to stop.')

    def record(self, msg):

        if len(msg.data) != 45:
            return

        elapsed = time.monotonic() - self.start_time

        self.writer.writerow([elapsed] + list(msg.data))

    def destroy_node(self):
        self.file.close()
        super().destroy_node()


def main():

    rclpy.init()
    node = EFleshRecorder()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()