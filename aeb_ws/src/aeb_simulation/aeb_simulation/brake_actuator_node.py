import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


class BrakeActuatorNode(Node):

    NORMAL = 'NORMAL'
    BRAKING = 'BRAKING'
    STOPPED = 'STOPPED'

    def __init__(self):
        super().__init__('brake_actuator_node')

        self._state = self.NORMAL
        self._stop_counter = 0
        self._stop_threshold = 10

        self.create_subscription(Bool, '/aeb/command', self._on_command, 10)

        self.get_logger().info('Brake actuator ready — state: NORMAL')

    def _on_command(self, msg):

        if self._state == self.STOPPED:
            return

        if self._state == self.NORMAL and msg.data:
            self._state = self.BRAKING
            self.get_logger().warn('>>> BRAKES APPLIED — state: BRAKING <<<')

        elif self._state == self.BRAKING and msg.data:
            self._stop_counter += 1
            if self._stop_counter >= self._stop_threshold:
                self._state = self.STOPPED
                self.get_logger().warn('>>> VEHICLE STOPPED — state: STOPPED <<<')

        elif self._state == self.BRAKING and not msg.data:
            self._state = self.NORMAL
            self._stop_counter = 0
            self.get_logger().info('Brakes released — state: NORMAL')


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(BrakeActuatorNode())
    rclpy.shutdown()