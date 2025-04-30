import common.net_sockets as nt
import common.shared_globals as shared
from common import protocols


def UDP_receiver(tcp_port):

    receive_socket = nt.create_UDP_receive_socket(shared.MULTICAST_IP, shared.MULTICAST_PORT)

    send_socket = nt.create_UDP_send_socket()

    while True:
        msg, address = receive_socket.recvfrom(1024)
        type = protocols.protocol_get_type(msg)

        if type == protocols.PROTOCOLS.DISCOVER:
            offer_message = protocols.protocol_OFFER(tcp_port)
            print("Received from ", address)
            send_socket.sendto(offer_message.encode(), (shared.MULTICAST_IP, shared.MULTICAST_PORT))