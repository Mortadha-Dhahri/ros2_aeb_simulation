import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, Bool


class AebDecisionNode(Node):

    IDLE = 'IDLE'
    WARNING = 'WARNING'
    BRAKING = 'BRAKING'
    STOPPED = 'STOPPED'

    # TTC thresholds in seconds
    TTC_WARN = 3.0
    TTC_BRAKE = 1.5

    def __init__(self):
        super().__init__('aeb_decision_node')

        self._state = self.IDLE
        self._current_ttc = 999.0
        self._current_speed = 0.0
        self._active = True
        self._shutdown_published = False

        self.create_subscription(Float32, '/ttc', self._on_ttc, 10)
        self.create_subscription(Float32, '/vehicle/speed', self._on_speed, 10)

        self._brake_pub = self.create_publisher(String, '/brake_cmd', 10)
        self._shutdown_pub = self.create_publisher(Bool, '/simulation/shutdown', 10)

        self.get_logger().info(
            f'AEB decision node started — '
            f'warn threshold: {self.TTC_WARN}s, '
            f'brake threshold: {self.TTC_BRAKE}s')

    def _on_speed(self, msg):
        self._current_speed = msg.data

        # vehicle has stopped — end simulation
        if (self._state == self.BRAKING
                and self._current_speed <= 0.0
                and not self._shutdown_published):
            self._transition(self.STOPPED)
            self._publish_shutdown()

    def _on_ttc(self, msg):
        if not self._active:
            return

        self._current_ttc = msg.data

        if self._state == self.IDLE:
            if self._current_ttc < self.TTC_WARN:
                self._transition(self.WARNING)

        elif self._state == self.WARNING:
            if self._current_ttc < self.TTC_BRAKE:
                self._transition(self.BRAKING)
                self._publish_brake('FULL_BRAKE')
            elif self._current_ttc >= self.TTC_WARN:
                self._transition(self.IDLE)

        elif self._state == self.BRAKING:
            pass  # held until vehicle stops

    def _transition(self, new_state):
        self.get_logger().warn(
            f'STATE: {self._state} → {new_state} '
            f'| TTC={self._current_ttc:.2f}s '
            f'| speed={self._current_speed:.1f}m/s')
        self._state = new_state

    def _publish_brake(self, cmd):
        msg = String()
        msg.data = cmd
        self._brake_pub.publish(msg)

    def _publish_shutdown(self):
        self._shutdown_published = True
        self._active = False
        self.get_logger().warn('Vehicle stopped — publishing shutdown signal')
        msg = Bool()
        msg.data = True
        self._shutdown_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = AebDecisionNode()
    while rclpy.ok() and node._active:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()