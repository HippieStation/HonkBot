#!/usr/bin/env python2
from __future__ import print_function
import hashlib
import hmac
import subprocess

# This lone function sends a message to MoMMI's commloop.
def MoMMI(address, key, type, meta, content):
    import json
    import struct
    from socket import socket, AF_INET, SOCK_STREAM

    msg = json.dumps({
        "type": type,
        "meta": meta,
        "cont": content
    }).encode("UTF-8")  # type: bytes
    h = hmac.new(key, msg, hashlib.sha1)
    packet = b"\x30\x05"  # type: bytes
    packet += h.digest()
    packet += struct.pack("!I", len(msg))
    packet += msg

    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.settimeout(5)
        s.connect(address)
        s.sendall(packet)
        ret = struct.unpack("!B", s.recv(1))[0]  # type: int
        if ret != 0:
            raise IOError("MoMMI returned non-zero code {}".format(ret))
    finally:
        s.close()

def update_server():
    MoMMI(("localhost", 1679), b"password", "update", "", {"content": "Server Updater running"})
    p = subprocess.Popen('/home/byond/updater.sh', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ""
    for line in p.stdout.readlines():
        print(line)
        output = output + str(line)
    retval = p.wait()

    message = {
        "content": "```{}```\nreturned exit code: {}".format(output, retval),
    }

    MoMMI(("localhost", 1679), b"password", "update", "", message)

update_server()