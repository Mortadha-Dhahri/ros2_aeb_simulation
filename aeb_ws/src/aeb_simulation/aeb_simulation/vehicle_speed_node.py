import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
 
 
class VehicleStateNode(Node):
    def __init__(self):
        super().__init__('vehicle_state_node')
 
        self.declare_parameter('speed_mps', 15.0)
        self.declare_parameter('publish_rate_hz', 10.0)
 
        self._speed = self.get_parameter('speed_mps').value
        self._dt = 1.0 / self.get_parameter('publish_rate_hz').value
 
        self._pub = self.create_publisher(Float32, '/vehicle/speed', 10)
        self.create_timer(self._dt, self._tick)
 
        self.get_logger().info(
            f'Vehicle state node started — speed: {self._speed} m/s'
        )
 
    def _tick(self):
        msg = Float32()
        msg.data = float(self._speed)
        self._pub.publish(msg)
 
 
def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(VehicleStateNode())
    rclpy.shutdown()