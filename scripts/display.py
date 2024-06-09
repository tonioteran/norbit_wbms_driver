#!/usr/bin/env python3
import rospy

import math

from sensor_msgs.msg import Image
import numpy as np
import cv2
from norbit_wbms_driver.msg import WaterColumn


class ImageConverter:
    def __init__(self, topic_in, topic_out, rotation):
        self.rotation = rotation
        self.pub = rospy.Publisher(topic_out, Image, queue_size=1)
        self.sub = rospy.Subscriber(topic_in, WaterColumn, self.data_callback)
        #sub_parser = rospy.Subscriber('', WaterColumn, data_callback)
        
        beam_samples=650
        num_beams = 256

    def data_callback(self, msg):
        #New FLS data
        beam_samples= msg.num_samples
        num_beams = msg.num_beams
        aperture = msg.swath_open
        height = msg.num_samples
        width = msg.num_beams
        imagearray = np.array(msg.watercolumn_raw.data[:-width])
        imagearray = np.reshape(imagearray, (height,width))

        #filter data
        imagearray = np.log(imagearray)

        # Normalize the imagearray between 0 and 255
        max_value = np.max(imagearray[imagearray != -math.inf])
        min_value = np.min(imagearray[imagearray != -math.inf])
        imagearray = (imagearray - min_value) * (255.0 / (max_value - min_value))
        imagearray[imagearray < 0] = 0
        rospy.loginfo([min_value, max_value, np.min(imagearray), np.max(imagearray)])

        #Add more data to image to cover 360 deg
        aperture = np.degrees(aperture)
        not_covered = 360 - aperture
        step = aperture / width
        toadd = int(not_covered / step)
        offset = self.rotation
        imagearray = np.concatenate((np.zeros((height, offset)), imagearray[:,0:], np.zeros((height, toadd-offset))), axis=1)

        #Convert to cv2 image
        cv_pic = imagearray.astype(np.float32)
        cv_pic = cv2.transpose(cv_pic)

        #Do inverse polar transform
        cartisian_image = cv2.warpPolar(cv_pic, (height,height), (height/2, height/2), height/2, cv2.WARP_INVERSE_MAP)

        #output_image = cv_pic
        output_image = cartisian_image
        output_image = output_image.astype(np.uint8)
        output_image = cv2.flip(output_image,1)

        # Create the final Image message
        final = Image()
        final.data = output_image.flatten().tolist()
        final.width = np.size(output_image,1)
        final.height = np.size(output_image,0)
        final.encoding = "mono8"
        final.is_bigendian = 0
        final.step = beam_samples*2
        self.pub.publish(final)

if __name__ == '__main__':
    fls_topic_in = '/lolo/sensors/fls/wc/data'
    fls_topic_out = '/lolo/sensors/fls/wc/pie'
    mbes_topic_in = '/lolo/sensors/mbes/wc/data'
    mbes_topic_out = '/lolo/sensors/mbes/wc/pie'
    
    rospy.init_node('waterColumn_converter')
    fls = ImageConverter(fls_topic_in, fls_topic_out, 90)#90)
    mbes = ImageConverter(mbes_topic_in, mbes_topic_out, 35)

    rospy.spin()
