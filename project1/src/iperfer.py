#!/usr/bin/python
# iperfer.py

import os
import sys
import time
import socket


def iperf(host, port, duration):
    # print('iperf', host, port, duration)
    sock = socket.socket()
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
    sock.connect((host, port))

    nbytes = 0
    data = b'0' * 4000
    start_time = int(round(time.time() * 1000))
    while (int(round(time.time() * 1000)) - start_time) < duration:
        sock.send(data)
        nbytes += 4000

    sock.close()
    print('sent={0} KB rate={1} Mbps'.format(nbytes/1000, nbytes/1000/1000/duration*1000*8))



def main():
    argc = len(sys.argv)
    if argc != 4:
        print('Error: missing or additional arguments')
        sys.exit(1)
    
    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
        if port < 1024 or port > 65535:
            raise ValueError('bad argument')
    except ValueError:
        print('Error: port number must be in the range 1024 to 65535')
        sys.exit(1)

    try:
        duration = int(sys.argv[3]) * 1000 # millisecond
    except ValueError:
        sys.exit(1)

    iperf(host, port, duration)


main()
