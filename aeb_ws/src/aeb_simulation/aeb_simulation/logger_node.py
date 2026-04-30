import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, Bool
from datetime import datetime


class LoggerNode(Node):
    def __init__(self):
        super().__init__('logger_node')

        self._session_start = datetime.now()
        self._last_brake_cmd = None
        self._event_count = 0
        self._active = True

        self._last_speed = None
        self._last_ttc = None
        self._last_pressure = None

        self.create_subscription(String,  '/brake_cmd',           self._on_brake_cmd, 10)
        self.create_subscription(Float32, '/ttc',                 self._on_ttc,       10)
        self.create_subscription(Float32, '/vehicle/speed',       self._on_speed,     10)
        self.create_subscription(Float32, '/brake/pressure',      self._on_pressure,  10)
        self.create_subscription(Bool,    '/simulation/shutdown', self._on_shutdown,  10)

        self.get_logger().info(
            f'Logger node ready — session: '
            f'{self._session_start.strftime("%H:%M:%S")}')

    def _elapsed(self):
        return (datetime.now() - self._session_start).total_seconds()

    def _log_event(self, msg, level='info'):
        self._event_count += 1
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        full = f'[Event {self._event_count:02d}] [+{self._elapsed():.1f}s] [{ts}] {msg}'
        if level == 'warn':
            self.get_logger().warn(full)
        else:
            self.get_logger().info(full)

    def _on_brake_cmd(self, msg):
        if msg.data != self._last_brake_cmd:
            level = 'warn' if msg.data == 'FULL_BRAKE' else 'info'
            self._log_event(f'BRAKE CMD → {msg.data}', level)
            self._last_brake_cmd = msg.data

    def _on_ttc(self, msg):
        ttc = msg.data
        if self._last_ttc is None:
            self._last_ttc = ttc
            return
        for threshold in [5.0, 3.0, 2.0, 1.5, 1.0, 0.5]:
            if self._last_ttc > threshold >= ttc:
                self._log_event(f'TTC crossed {threshold}s → TTC={ttc:.2f}s', 'warn')
        self._last_ttc = ttc

    def _on_speed(self, msg):
        speed = msg.data
        if self._last_speed is None:
            self._last_speed = speed
            return
        for threshold in [10.0, 5.0, 1.0, 0.0]:
            if self._last_speed > threshold >= speed:
                self._log_event(f'Speed crossed {threshold}m/s → {speed:.2f}m/s')
        self._last_speed = speed

    def _on_pressure(self, msg):
        pressure = msg.data
        if self._last_pressure is None:
            self._last_pressure = pressure
            return
        for threshold in [0.25, 0.5, 0.75, 1.0]:
            if self._last_pressure < threshold <= pressure:
                self._log_event(
                    f'Brake pressure reached {threshold * 100:.0f}%', 'warn')
        self._last_pressure = pressure

    def _on_shutdown(self, msg):
        if msg.data and self._active:
            self._log_event(
                f'SIMULATION COMPLETE — '
                f'duration: {self._elapsed():.1f}s | '
                f'events logged: {self._event_count}',
                'warn')
            self._active = False


def main(args=None):
    rclpy.init(args=args)
    node = LoggerNode()
    try:
        while rclpy.ok() and node._active:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()