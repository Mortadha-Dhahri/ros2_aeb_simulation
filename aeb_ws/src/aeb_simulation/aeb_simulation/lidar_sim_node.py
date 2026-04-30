import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import Float32, Bool


class LidarSimNode(Node):
    def __init__(self):
        super().__init__('lidar_sim_node')

        self.declare_parameter('initial_distance_m', 50.0)
        self.declare_parameter('publish_rate_hz', 10.0)

        self._distance = self.get_parameter('initial_distance_m').value
        self._dt = 1.0 / self.get_parameter('publish_rate_hz').value

        self._vehicle_speed = 0.0
        self._active = True

        self._range_pub = self.create_publisher(Range, '/lidar/range', 10)
        self._ttc_pub = self.create_publisher(Float32, '/ttc', 10)

        self.create_subscription(Float32, '/vehicle/speed', self._on_speed, 10)
        self.create_subscription(Bool, '/simulation/shutdown', self._on_shutdown, 10)

        self.create_timer(self._dt, self._tick)

        self.get_logger().info(
            f'LiDAR sim started — '
            f'initial distance: {self._distance}m | '
            f'stationary obstacle')

    def _on_speed(self, msg):
        self._vehicle_speed = msg.data

    def _on_shutdown(self, msg):
        if msg.data:
            self._active = False

    def _tick(self):
        if not self._active:
            return

        # gap closes at vehicle speed — obstacle is stationary
        self._distance = max(0.0, self._distance - self._vehicle_speed * self._dt)

        # publish range
        range_msg = Range()
        range_msg.header.stamp = self.get_clock().now().to_msg()
        range_msg.header.frame_id = 'lidar'
        range_msg.range = float(self._distance)
        range_msg.min_range = 0.0
        range_msg.max_range = 100.0
        self._range_pub.publish(range_msg)

        # TTC = distance / vehicle_speed — stationary obstacle, ego vehicle closing
        if self._vehicle_speed > 0.01:
            ttc = self._distance / self._vehicle_speed
        else:
            ttc = 999.0

        ttc_msg = Float32()
        ttc_msg.data = float(ttc)
        self._ttc_pub.publish(ttc_msg)

        self.get_logger().info(
            f'dist={self._distance:.1f}m | '
            f'speed={self._vehicle_speed:.1f}m/s | '
            f'TTC={ttc:.2f}s',
            throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = LidarSimNode()
    while rclpy.ok() and node._active:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()