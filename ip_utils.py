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



import math

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
