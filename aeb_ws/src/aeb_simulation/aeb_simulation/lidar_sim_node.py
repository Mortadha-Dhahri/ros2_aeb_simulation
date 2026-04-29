import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range


class LidarSimNode(Node):
    def __init__(self):
        super().__init__('lidar_sim_node')

        self.declare_parameter('initial_distance_m', 50.0)
        self.declare_parameter('closing_speed_mps', 5.0)
        self.declare_parameter('publish_rate_hz', 10.0)

        self._distance = self.get_parameter('initial_distance_m').value
        self._closing_speed = self.get_parameter('closing_speed_mps').value
        self._dt = 1.0 / self.get_parameter('publish_rate_hz').value

        self._pub = self.create_publisher(Range, '/lidar/range', 10)
        self.create_timer(self._dt, self._tick)

        self.get_logger().info(
            f'LiDAR sim started — '
            f'initial distance: {self._distance}m, '
            f'closing speed: {self._closing_speed}m/s'
        )

    def _tick(self):
        self._distance = max(0.0, self._distance - self._closing_speed * self._dt)

        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'lidar'
        msg.range = float(self._distance)
        msg.min_range = 0.0
        msg.max_range = 100.0

        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(LidarSimNode())
    rclpy.shutdown()