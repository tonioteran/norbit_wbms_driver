#!/usr/bin/env python3
import rospy
import norbit_wbms_driver.srv
from std_msgs.msg import String 
import subprocess
import os
import rosparam

import wbms_configure

def send_configuration(req: norbit_wbms_driver.srv.WbmsConfigureRequest):
    print("Sending configuration file: " + req.ConfigRequest)
    wbms_configure.send_configuration(req.ConfigRequest)

    return norbit_wbms_driver.srv.WbmsConfigureResponse(str(-1))

def main():
    print("Configure service started")
    # Params: sonar ip, sonar port
    print(rospy.get_param_names())
    cfg_dir = rosparam.get_param('wbms/cfg_dir')
    print(cfg_dir)
    
    rospy.init_node('wbms_configure_server')
    configServ = rospy.Service('/wbms_configure', norbit_wbms_driver.srv.WbmsConfigure, send_configuration)
    rospy.spin()

if __name__ == "__main__":
    main()