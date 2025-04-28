import socket
import struct
import threading
from time import sleep

import common.protocols as protocols

MULTICAST_IP = "224.0.0.1"
MULTICAST_PORT = 8000
TCP_PORT = 5000

def TCP_receiver():
    pass

def UDP_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))

    mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST_IP), socket.inet_aton("0.0.0.0"))
    sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP, mreq)

    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 1))

    while True:
        msg, address = sock.recvfrom(1024)
        type = protocols.protocol_get_type(msg)
        if type == protocols.PROTOCOLS.DISCOVER:
            offer_message = protocols.protocol_OFFER(TCP_PORT)
            send_sock.sendto(offer_message.encode(), address)
        else:
            print("Still no DISCOVER received")

    pass

if __name__ == '__main__':
    #todo handeling user input
    period = 60
    thread = threading.Thread(target=UDP_receiver).start()

    while True:
        sleep(1)