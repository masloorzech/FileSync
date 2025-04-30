import common.net_sockets as nt
import common.shared_globals as shared
from common import protocols

# This function receives UDP messages, processes them, and responds based on the protocol type.
def UDP_receiver(tcp_port):

    receive_socket = nt.create_UDP_receive_socket(shared.MULTICAST_IP, shared.MULTICAST_PORT)

    send_socket = nt.create_UDP_send_socket()

    while True:

        # Receive a message from the multicast group.
        msg, address = receive_socket.recvfrom(1024)

        # Determine the type of the received message using a protocol handler.
        type = protocols.protocol_get_type(msg)

        # If the message is a "DISCOVER" type, respond with an "OFFER" message.
        if type == protocols.PROTOCOLS.DISCOVER:
            offer_message = protocols.protocol_OFFER(tcp_port)
            # Print the address from which the message was received (for debugging purposes).
            print("Received from ", address)

            # Send the offer message back to the multicast group.
            send_socket.sendto(offer_message.encode(), (shared.MULTICAST_IP, shared.MULTICAST_PORT))