import socket
import struct

"""
This file contains utility functions to create and configure UDP sockets for multicast communication:

    - create_UDP_send_socket() — creates a socket for sending multicast messages (TTL = 1 to limit scope to local network, can be changed).
    - create_UDP_receive_socket(ip, port) — joins a multicast group and binds a socket to receive messages on a specified port.
"""

# Creates a UDP socket for sending multicast messages.
# Sets the multicast TTL (Time-To-Live) to 1, limiting the packet to the local network.
def create_UDP_send_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 1))
    return sock

# Creates a UDP socket for receiving multicast messages.
# Binds the socket to the specified port and joins the multicast group identified by the given IP address.
#
# Parameters:
# - ip: Multicast group IP address to join (e.g. "224.0.0.1")
# - port: Port number to bind the socket to

def create_UDP_receive_socket(ip,port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))

    # Join the multicast group by setting IP_ADD_MEMBERSHIP option
    mreq = struct.pack("4s4s", socket.inet_aton(ip), socket.inet_aton("0.0.0.0"))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return sock