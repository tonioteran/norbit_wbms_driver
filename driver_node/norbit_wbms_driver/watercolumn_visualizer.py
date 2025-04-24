import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from norbit_wbms_interfaces.msg import WaterColumn


class WaterColumnVisualizer(Node):
    def __init__(self):
        super().__init__("watercolumn_visualizer")
        self.get_logger().info("WaterColumnVisualizer node started")
        self.message_counter = 0
        self.subscription = self.create_subscription(
            WaterColumn, "watercolumn_raw_image", self.listener_callback, 10
        )
        self.processed_image_publisher = self.create_publisher(
            Image, "watercolumn_processed_image", 10
        )

    def listener_callback(self, msg):
        self.message_counter += 1
        self.get_logger().info(
            "Received watercolumn_raw_image message #{}".format(self.message_counter)
        )
        processed_img = self.convert_image_to_polar(msg)
        self.get_logger().info(
            "Publishing processed image to {}".format(
                self.processed_image_publisher.topic
            )
        )
        self.processed_image_publisher.publish(processed_img)

    def convert_image_to_polar(self, msg):
        return msg.watercolumn_raw


def main(args=None):
    rclpy.init(args=args)
    watercolumn_visualizer = WaterColumnVisualizer()
    rclpy.spin(watercolumn_visualizer)
    watercolumn_visualizer.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
