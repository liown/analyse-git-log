import base64
import os
import stat
import sys
import urllib2
import json
import getpass
import syslog
from Crypto.Cipher import AES
from Crypto import Random


def login():
    try:
        proxy = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)
        jdata = json.dumps(login_body)
        req = urllib2.Request(login_uri, jdata)
        response = urllib2.urlopen(req, timeout=10)
        result = json.loads(response.read())
        errordata = result['error']
        errornum = errordata['code']
        if errornum != 0:
            set_log(str(result))
            return False
    except Exception, msg:
        print 'login eBackup failed, please check eBackup server.'
        sys.exit()
    return True
    

def aes_base64_encrypt(iv, input_pwd): 
    key = aes_key_start + aes_key_end
    block_size = AES.block_size
    cipher = AES.new(key, AES.MODE_CBC, iv)
    space_count = input_pwd.count('')
    if space_count < block_size:  
        add_count = (block_size - space_count) + 1 
        input_pwd = input_pwd + (' ' * add_count)  
    elif space_count > block_size:  
        add_count = (block_size - (space_count % block_size)) + 1 
        input_pwd = input_pwd + (' ' * add_count)
    en_pwd = base64.b64encode(cipher.encrypt(input_pwd))
    return en_pwd


def input_pwd():
    sk = getpass.getpass('Please enter the password:\n')
    
    
def modi_power(path):
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    

def get_iv():
    iv = Random.new().read(AES.block_size)
    return iv
