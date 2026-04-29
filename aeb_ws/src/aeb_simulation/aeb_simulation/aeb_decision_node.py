import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32
from sensor_msgs.msg import Range


class AebDecisionNode(Node):
    def __init__(self):
        super().__init__('aeb_decision_node')

        self.declare_parameter('ttc_threshold', 2.0)
        self.declare_parameter('publish_rate_hz', 10.0)

        self._threshold = self.get_parameter('ttc_threshold').value
        self._dt = 1.0 / self.get_parameter('publish_rate_hz').value

        self._distance = None
        self._speed = None

        self.create_subscription(Range,   '/lidar/range',   self._on_range, 10)
        self.create_subscription(Float32, '/vehicle/speed', self._on_speed, 10)

        self._pub = self.create_publisher(Bool, '/aeb/command', 10)

        self.create_timer(self._dt, self._decide)

        self.get_logger().info(
            f'AEB decision node started — TTC threshold: {self._threshold}s'
        )

    def _on_range(self, msg):
        self._distance = msg.range

    def _on_speed(self, msg):
        self._speed = msg.data

    def _decide(self):
        if self._distance is None or self._speed is None:
            self.get_logger().warn(
                'Waiting for sensor data...',
                throttle_duration_sec=2.0
            )
            return

        if self._speed < 0.01:
            ttc = float('inf')
        else:
            ttc = self._distance / self._speed

        brake = ttc < self._threshold

        msg = Bool()
        msg.data = brake
        self._pub.publish(msg)

        if brake:
            self.get_logger().warn(
                f'BRAKE — TTC={ttc:.2f}s | '
                f'dist={self._distance:.1f}m | '
                f'speed={self._speed:.1f}m/s'
            )
        else:
            self.get_logger().info(
                f'CLEAR — TTC={ttc:.2f}s | dist={self._distance:.1f}m',
                throttle_duration_sec=1.0
            )


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(AebDecisionNode())
    rclpy.shutdown()