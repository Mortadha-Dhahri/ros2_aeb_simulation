import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, Bool


class VehicleStateNode(Node):
    def __init__(self):
        super().__init__('vehicle_state_node')

        self.declare_parameter('initial_speed_mps', 15.0)
        self.declare_parameter('normal_decel_mps2', 0.5)
        self.declare_parameter('aeb_decel_mps2', 9.0)
        self.declare_parameter('publish_rate_hz', 10.0)

        self._speed = self.get_parameter('initial_speed_mps').value
        self._normal_decel = self.get_parameter('normal_decel_mps2').value
        self._aeb_decel = self.get_parameter('aeb_decel_mps2').value
        self._dt = 1.0 / self.get_parameter('publish_rate_hz').value

        self._brake_cmd = 'CLEAR'
        self._active = True

        self._speed_pub = self.create_publisher(Float32, '/vehicle/speed', 10)

        self.create_subscription(String, '/brake_cmd', self._on_brake_cmd, 10)
        self.create_subscription(Bool, '/simulation/shutdown', self._on_shutdown, 10)

        self.create_timer(self._dt, self._tick)

        self.get_logger().info(
            f'Vehicle state node started — '
            f'speed: {self._speed}m/s, '
            f'AEB decel: {self._aeb_decel}m/s²')

    def _on_brake_cmd(self, msg):
        self._brake_cmd = msg.data

    def _on_shutdown(self, msg):
        if msg.data:
            self._active = False

    def _tick(self):
        if not self._active:
            return

        if self._brake_cmd == 'FULL_BRAKE':
            self._speed = max(0.0, self._speed - self._aeb_decel * self._dt)
        else:
            # natural deceleration — driver coasting
            self._speed = max(0.0, self._speed - self._normal_decel * self._dt)

        msg = Float32()
        msg.data = float(self._speed)
        self._speed_pub.publish(msg)

        if self._speed == 0.0 and self._brake_cmd == 'FULL_BRAKE':
            self.get_logger().info('Vehicle fully stopped')


def main(args=None):
    rclpy.init(args=args)
    node = VehicleStateNode()
    while rclpy.ok() and node._active:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()