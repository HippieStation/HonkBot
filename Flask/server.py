#!/usr/bin/env python2
from __future__ import print_function
from flask import Blueprint, request, abort, Flask
import hashlib
import hmac

app = Flask(__name__)


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

@app.route("/github", methods=['POST'])
def gh_relay():
    hmac_calc = hmac.new("password", request.get_data(), hashlib.sha1).hexdigest()
    hmac_github_raw = request.headers.get("X-Hub-Signature")
    hmac_github_split = hmac_github_raw.split("=")
    hmac_github_type = hmac_github_split[0]
    hmac_github_hash = hmac_github_split[1]

    if hmac_github_type != "sha1":
      return "Unsupported Hash Type"

    if hmac_calc != hmac_github_hash:
        return "Wew lad, what you trying here?"

    payload = {
        "event": request.headers.get("X-GitHub-event"),
        "content": request.get_json()
    }
    MoMMI(("localhost", 1679), b"password", "github", "", payload)
    return "Successfully sent the message to MoMMI."


@app.route("/discord")
def dc_relay():
    message = {
        "pass": request.args["pass"],
        "admin": request.args.get("admin", "false") == "true",
        "content": request.args["content"],
        "ping": request.args.get("ping", "false") == "true"
    }

    MoMMI(("localhost", 1679), b"password", "nudge", "", message)
    return "Successfully sent the message to MoMMI."


if __name__ == "__main__":
        app.run(host="0.0.0.0", port=9000)
