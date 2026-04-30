import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32, Bool


class BrakeActuatorNode(Node):

    def __init__(self):
        super().__init__('brake_actuator_node')

        self._brake_pressure = 0.0   # 0.0 = no braking, 1.0 = full braking
        self._target_pressure = 0.0
        self._active = True

        # pressure ramp rate — how fast brakes engage (per tick at 10Hz)
        # 0.2 per tick = 100ms to reach 50% pressure = realistic hydraulic response
        self._ramp_rate = 0.2

        self.create_subscription(String, '/brake_cmd', self._on_brake_cmd, 10)
        self.create_subscription(Bool, '/simulation/shutdown', self._on_shutdown, 10)

        self._pressure_pub = self.create_publisher(Float32, '/brake/pressure', 10)

        self.create_timer(0.1, self._tick)

        self.get_logger().info('Brake actuator ready — pressure: 0.0')

    def _on_brake_cmd(self, msg):
        if not self._active:
            return

        if msg.data == 'FULL_BRAKE':
            self._target_pressure = 1.0
            self.get_logger().warn('FULL_BRAKE command received — ramping pressure')
        elif msg.data == 'CLEAR':
            self._target_pressure = 0.0

    def _on_shutdown(self, msg):
        if msg.data:
            self._active = False
            self.get_logger().warn(
                f'Shutdown received — final brake pressure: {self._brake_pressure:.2f}')

    def _tick(self):
        if not self._active:
            return

        # ramp pressure toward target — simulates hydraulic actuator lag
        if self._brake_pressure < self._target_pressure:
            self._brake_pressure = min(
                self._target_pressure,
                self._brake_pressure + self._ramp_rate)
        elif self._brake_pressure > self._target_pressure:
            self._brake_pressure = max(
                self._target_pressure,
                self._brake_pressure - self._ramp_rate)

        msg = Float32()
        msg.data = float(self._brake_pressure)
        self._pressure_pub.publish(msg)

        if self._brake_pressure > 0.0:
            self.get_logger().info(
                f'Brake pressure: {self._brake_pressure * 100:.0f}%',
                throttle_duration_sec=0.5)


def main(args=None):
    rclpy.init(args=args)
    node = BrakeActuatorNode()
    while rclpy.ok() and node._active:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()