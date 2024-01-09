#!/usr/bin/env python3
import socket
import configparser
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
print("Current working directory: " + os.getcwd())
print("Loading config file: " + str(sys.argv[1]))
config = configparser.ConfigParser(defaults=None, 
                                   delimiters=(':', '='), 
                                   comment_prefixes=('#', ';'),
                                   inline_comment_prefixes=('#'),
                                   interpolation=None)
config.read(sys.argv[1])

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.settimeout(2)
print("Connecting to " + config["sonar"]['ip'] + " " + config['sonar']['port'])

try:
    tcp_socket.connect((config['sonar']['ip'], int(config['sonar']['port'])))
    print("TCP successfully connected.")
except:
    print("Failed to bind socket.")

def send(msg: str):
    msg = msg + "\n\r"
    tcp_socket.send(msg.encode())
    print(msg.encode())

modes = config['mode.operation_modes']

send('set_mode ' + modes.get(config['sonar']['mode']))

# Swath configuration 
swath = config['swath']
send('set_direction ' + swath['direction'])
send('set_opening_angle ' + swath['openingAngle'])


# Transmission Configuration
tx = config['tx']
tcp_socket.send(str('set_tx ' + 
                tx['frequency'] + ' ' +
                tx['bandwidth'] + ' ' +
                tx['amplitude'] + ' ' +
                tx['length']).encode())

flipmodes = config['mode.flip_modes']
send('set_flip ' + flipmodes.get(config['sonar']['flipMode']))

gatemodes = config['mode.gate_modes']
send('set_gate_mode ' + gatemodes.get(config['sonar']['gateMode']))
send('set_gate_tilt ' + config['sonar']['gateTilt'])


tcp_socket.close()








