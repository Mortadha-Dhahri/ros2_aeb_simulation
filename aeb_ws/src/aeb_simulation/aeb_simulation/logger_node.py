import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from datetime import datetime


class LoggerNode(Node):

    CLEAR = 'CLEAR'
    BRAKE = 'BRAKE'

    def __init__(self):
        super().__init__('logger_node')

        self._last_state = None
        self._event_count = 0
        self._session_start = datetime.now()

        self.create_subscription(Bool, '/aeb/command', self._on_command, 10)

        self.get_logger().info(
            f'Logger node ready — session started at '
            f'{self._session_start.strftime("%H:%M:%S")}')

    def _on_command(self, msg):
        current_state = self.BRAKE if msg.data else self.CLEAR

        if current_state == self._last_state:
            return

        self._event_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        elapsed = (datetime.now() - self._session_start).total_seconds()

        if current_state == self.BRAKE:
            self.get_logger().warn(
                f'[Event {self._event_count}] [{timestamp}] '
                f'[+{elapsed:.1f}s] CLEAR → BRAKE')
        else:
            self.get_logger().info(
                f'[Event {self._event_count}] [{timestamp}] '
                f'[+{elapsed:.1f}s] BRAKE → CLEAR')

        self._last_state = current_state


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(LoggerNode())
    rclpy.shutdown()