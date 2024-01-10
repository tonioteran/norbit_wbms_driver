#!/usr/bin/env python3
import rospy
import norbit_wbms_driver.srv
from std_msgs.msg import String 
import subprocess
import os
import rosparam

import wbms_configure

cfg_dir = ""
default_cfg = ""
short_range_cfg = ""
medium_range_cfg = ""
long_range_cfg = ""

# TODO: Make a class and move the code from wbms_configure.py into it

def send_configuration(req: norbit_wbms_driver.srv.WbmsConfigureRequest):
    cfg_dir = rosparam.get_param('wbms/cfg_dir')
    default_cfg = rosparam.get_param('wbms/default_conf_file')
    short_range_cfg = rosparam.get_param('wbms/short_range_conf_file')
    medium_range_cfg = rosparam.get_param('wbms/medium_range_conf_file')
    long_range_cfg = rosparam.get_param('wbms/long_range_conf_file')

    print("Setting configuration: " + str(req.ConfigRequest))
    if req.ConfigRequest == 1:
        print("Setting conf file: " + cfg_dir + default_cfg)
        wbms_configure.send_configuration(cfg_dir + default_cfg)
    elif req.ConfigRequest == 2:
        print("Setting conf file: " + cfg_dir + short_range_cfg)
        wbms_configure.send_configuration(cfg_dir + short_range_cfg)
    elif req.ConfigRequest == 3:
        print("Setting conf file: " + cfg_dir + medium_range_cfg)
        wbms_configure.send_configuration(cfg_dir + medium_range_cfg)
    elif req.ConfigRequest == 4:
        print("Setting conf file: " + cfg_dir + long_range_cfg)
        wbms_configure.send_configuration(cfg_dir + long_range_cfg)


    return norbit_wbms_driver.srv.WbmsConfigureResponse(str(-1))

def main():
    print("Configure service started")
    # Params: sonar ip, sonar port
    print(rospy.get_param_names())
    
    rospy.init_node('wbms_configure_server')
    configServ = rospy.Service('/wbms_configure', norbit_wbms_driver.srv.WbmsConfigure, send_configuration)
    rospy.spin()

if __name__ == "__main__":
    main()