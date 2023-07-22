#!/usr/bin/env python3



import socket

import rospy
from std_msgs.msg import Float32
from Norbit_FLS_driver.cfg import fls_paramsConfig 
from rospy_message_converter import message_converter
from Norbit_FLS_driver.msg import Configs

def create_configs():
    configlist = []
    config1 = fls_paramsConfig.defaults.copy()
    config1['set_power_mode'] = 1
    config2 = fls_paramsConfig.defaults.copy()
    config2['set_vga'] = 0
    config2['set_gain'] = 30
    config2['set_power_mode'] = 1
    config3 = fls_paramsConfig.defaults.copy()
    config3['set_tx_Frequency'] = 200
    config3['set_power_mode'] = 1
    configlist.append(config1)
    configlist.append(config2)
    configlist.append(config3) # last config in the list should be the default config if you want it in the loop
    return configlist




def main():
    """
    Main method for the ROS node.
    """
    rospy.init_node('cycler')
    pub = rospy.Publisher('configs', Configs, queue_size=10)
    dictlist = create_configs()
    iter = 0
    interval = 10
    rate = rospy.Rate(1/interval)
    rate.sleep()
    while not rospy.is_shutdown():
        if iter >len(dictlist)-1:
            iter = 0
        msg = message_converter.convert_dictionary_to_ros_message('Norbit_FLS_driver/Configs', dictlist[iter])
        iter = iter + 1
        pub.publish(msg)
        rate.sleep()

if __name__ == "__main__":
    main()
