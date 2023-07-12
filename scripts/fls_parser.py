#!/usr/bin/env python3
"""
Norbit's FLS data parser.
"""
import struct
import socket
import rospy
import numpy as np

from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray, MultiArrayDimension

__author__ = "Aldo Teran"
__author_email = "aldot@kth.se"
__license__ = "MIT"
__status__ = "Development"



class FlsParser:
    """
    Class for handling the raw logic of parsing a raw FLS data packet.

    Based on Sec. 8.2 of the Norbit's TN-180196 document.
    """
    def __init__(self):
        # Map from dtype to corresponding byte size for stepping and format
        # character for parsing. Keys correspond to the indices in `parse_dtype`.
        self.dtype_map = {
            0: ('B', 1),     # uint8
            1: ('b', 1),     # int8
            2: ('H', 2),     # uint16
            3: ('h', 2),     # int16
            4: ('I', 4),     # uint32
            5: ('i', 4),     # int32
            6: ('Q', 8),     # uint64
            7: ('q', 8),     # int64
            0x15: ('f', 4),  # float32
            0x17: ('d', 8),  # float64
        }


    def parse_preamble(self, msg):
        '''This should always be 0xDEADBEEF.'''
        return struct.unpack('<I', msg[0:4])[0]


    def parse_type(self, msg):
        '''This corresponds to the type of data being returned.'''
        return struct.unpack('<I', msg[4:8])[0]


    def parse_size(self, msg):
        '''Returns the size of the entire package in bytes.'''
        return struct.unpack('<I', msg[8:12])[0]


    def parse_sound_velocity(self, msg):
        '''Returns the sound velocity in m/s.'''
        return struct.unpack('<f', msg[24:28])[0]


    def parse_sample_rate(self, msg):
        '''Returns the sample rate in Hz.'''
        return struct.unpack('<f', msg[28:32])[0]


    def parse_num_beams(self, msg):
        '''Returns the number of available beams.'''
        return struct.unpack('<I', msg[32:36])[0]


    def parse_num_samples(self, msg):
        '''Returns the number samples in each beam.'''
        return struct.unpack('<I', msg[36:40])[0]


    def parse_timestamp(self, msg):
        '''Returns the ping's Unix timestamp at TX.'''
        return struct.unpack('<d', msg[40:48])[0]


    def parse_dtype(self, msg):
        '''Returns the underlying type of the data.

        The dtype options are:
            0:uint8
            1:int8
            2:uint16
            3:int16
            4:uint32
            5:int32
            6:uint64
            7:int64
            0x15:float32
            0x17:float64
        '''
        return struct.unpack('<I', msg[48:52])[0]


    def parse_pixel_data(self, msg):
        '''Returns the MxN pixel data array.

        M: number of samples in each beam
        N: number of beams
        '''
        M = self.parse_num_samples(msg)
        N = self.parse_num_beams(msg)

        # The step size in bytes depends on the dtype representation.
        dtype = self.parse_dtype(msg)
        step_char,step_size = self.dtype_map[dtype]
        parse_str = '<{}'.format(step_char)

        print("M={} N={}, num pixels={}".format(M,N,M*N))
        pixel_values = []
        for i in range(M * N):
            offset = 192 + i * step_size
            pixel_values.append(
                struct.unpack(parse_str, msg[offset:offset+step_size])[0])
        return pixel_values


    def parse_directions(self, msg):
        '''Returns the beam directions in radians.'''
        N = self.parse_num_beams(msg)
        M = self.parse_num_samples(msg)
        step_char,step_size = self.dtype_map[self.parse_dtype(msg)]

        fixed_offset = 192 + M*N*step_size

        directions = []
        for i in range(N):
            offset = fixed_offset + 4 * i
            directions.append(
                struct.unpack('<f', msg[offset:offset+4])[0])
        return directions



class FlsNode:
    """
    Class to handle the HEX parsing from an Norbit's FLS data stream.
    """

    # FLS's IP and port.
    FLS_IP = "192.168.1.89"
    # Water column data port.
    FLS_PORT = 2211

    BUFFER_SIZE_BYTES = 512000

    def __init__(self):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while not rospy.is_shutdown():
            try:
                self.tcp_sock.connect((self.FLS_IP, self.FLS_PORT))
                rospy.loginfo("TCP socket successfully bound to: %s:%i", self.FLS_IP,
                            self.FLS_PORT)
                break
            except:
                rospy.logerr("Failed to bind socket to %s:%s. Check ethernet configuration \
                            and restart the node.", self.FLS_IP, self.FLS_PORT)
                rospy.sleep(1)
                #raise

        # Set a timout for the socket.
        self.tcp_sock.settimeout(2)

        # Build our parser.
        self.p = FlsParser()

        # Create the buffer where we'll store the data being streamed in.
        self.data_buffer = b''

        # Setup our raw array publisher and the image publisher.
        self.img_pub = rospy.Publisher("fls/image",
                                       Image, queue_size=1)
        self.raw_pub = rospy.Publisher("fls/raw",
                                       Float32MultiArray, queue_size=1)


    def parse_and_publish(self):
        """
        Parse and publish the data recived from the ICP socket.
        """
        # Get data from udp socket
        try:
            # Fetch the initial chunk.
            data, addr = self.tcp_sock.recvfrom(self.BUFFER_SIZE_BYTES)
            # Quick check of the deadbeef.
            if self.p.parse_preamble(data) != 0xDEADBEEF:
                rospy.logerr("Message did not pass the deadbeef check!")
                return

            self.data_buffer += data

            # Get the expected size of the packet.
            M = self.p.parse_num_samples(data)
            N = self.p.parse_num_beams(data)
            dtype = self.p.parse_dtype(data)
            _,step_size = self.p.dtype_map[dtype]
            expected_size_bytes = 192 + M*N*step_size + 4*N
            real_size = self.p.parse_size(data)

            # Keep looping until the full message is completely received.
            while len(self.data_buffer) < expected_size_bytes:
                try:
                    data, addr = self.tcp_sock.recvfrom(self.BUFFER_SIZE_BYTES)
                    self.data_buffer += data
                except:
                    print("something went wrong in the msg reconstruction loop")

        except socket.timeout:
            rospy.logerr("Command interface socket timed out, verify connection.")
            return

        print("Final size of the concat msg={}".format(len(self.data_buffer)))

        # Get the pixel and beam directions arrays.
        pixel_data = self.p.parse_pixel_data(self.data_buffer)
        directions = self.p.parse_directions(self.data_buffer)

        # Build the image.
        image = Image()
        image.header.stamp = rospy.Time.now()
        image.height = self.p.parse_num_samples(self.data_buffer)  # M
        image.width = self.p.parse_num_beams(self.data_buffer)     # N
        image.encoding = 'mono8'  # TODO This should dynamically change
                                   # depending on the data's dtype...
        image.step = image.width * 1
        image.data =  np.array(pixel_data, dtype='uint8').tolist()
        self.img_pub.publish(image)

        # Build the multi array.
        array = Float32MultiArray()
        img_dim = MultiArrayDimension()
        img_dim.label = "pixel_data"
        img_dim.size = image.height * image.width
        img_dim.stride = img_dim.size * 4
        dir_dim = MultiArrayDimension()
        dir_dim.label = "directions"
        dir_dim.size = len(directions)
        dir_dim.stride = dir_dim.size * 4
        array.layout.dim = [img_dim, dir_dim]
        array.data = np.array(pixel_data).astype(float).tolist() + directions
        self.raw_pub.publish(array)

        # Reset the data buffer.
        self.data_buffer = b''



def main():
    """
    Main method for the ROS node.
    """
    rospy.init_node('fls_parser')
    rospy.loginfo("Starting the FLS parsing node...")
    fls = FlsNode()

    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        fls.parse_and_publish()
        rate.sleep()

if __name__ == "__main__":
    main()

