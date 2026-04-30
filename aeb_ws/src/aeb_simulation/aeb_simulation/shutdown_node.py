import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


class ShutdownNode(Node):
    def __init__(self):
        super().__init__('shutdown_node')
        self._triggered = False
        self.create_subscription(Bool, '/simulation/shutdown', self._on_shutdown, 10)
        self.get_logger().info('Shutdown node ready — waiting for simulation end signal')

    def _on_shutdown(self, msg):
        if msg.data and not self._triggered:
            self._triggered = True
            self.get_logger().warn('Shutdown signal received — terminating all nodes')
            self.executor.shutdown(timeout_sec=0)


def main(args=None):
    rclpy.init(args=args)
    node = ShutdownNode()
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    node.executor = executor
    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()