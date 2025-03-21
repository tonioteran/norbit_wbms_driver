import rclpy
from rclpy.node import Node

class WBMSDriverNode(Node):
    """
    Class to configure settings of the WBMS driver.
    """

    def __init__(self):
        super().__init__('wbms_driver')
        self.get_logger().info("Starting WBMS driver node.")

def main(args=None):
    rclpy.init(args=args)
    wbms_driver = WBMSDriverNode()
    rclpy.spin(wbms_driver)
    wbms_driver.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()