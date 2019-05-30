#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: liown
# Filename: __init__.py
# Time: 2019/5/17 9:06
# Description:

import socket
import struct


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def ip2int(ip):
    return struct.unpack("!L",socket.inet_aton(ip))[0]

def int2ip(int_ip):
    return socket.inet_ntoa(struct.pack("!I", int_ip))
