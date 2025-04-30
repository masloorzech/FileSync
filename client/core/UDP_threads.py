import json
import socket
import time
from time import sleep
from datetime import datetime

import common.net_sockets as net_socket
import common.shared_globals as shared
import common.protocols as protocols
from . import runtime_shared as runtime

# Function responsible for discovering servers using multicast communication
def multicast_discoverer():

    send_socket = net_socket.create_UDP_send_socket()

    receive_socket = net_socket.create_UDP_receive_socket(shared.MULTICAST_IP, shared.MULTICAST_PORT)
    receive_socket.settimeout(5)

    while True:
        # If the next sync time has been set, sleep until that time
        if runtime.NEXT_SYNC_TIME_SET_SIGNAL.is_set():
            print(f"[INFO] Sleeping while waiting for next sync time: {datetime.fromtimestamp(runtime.next_sync_time).strftime("%Y-%m-%d %H:%M:%S")}")
            perform_sync_time_waiting()

        # If a TCP connection is already active, skip discovery for a short time
        if runtime.TCP_CONNECTION_ACTIVE_SIGNAL.is_set():
            sleep(5)
            continue

        print('[UDP INFO] Sending DISCOVERY')

        try:
            send_discover_protocol(send_socket)

            # Wait to receive a response (expecting an OFFER)
            msg, addr = receive_socket.recvfrom(1024)

            #Decodes type of protocol gathered from socket
            msg_type = protocols.protocol_get_type(msg)

            # If an OFFER was received, extract server details and proceed to TCP connection setup
            if msg_type == protocols.PROTOCOLS.OFFER:
                extract_server_information(msg, addr)
                continue

            # If no OFFER was received, wait and retry
            wait_before_retry()

        except socket.timeout:
            wait_before_retry()

        except Exception as e:
            wait_before_retry()


# Waits until the next sync time (used to align discovery attempts with external time requirements)
def perform_sync_time_waiting():
    now = time.time()
    difference = runtime.next_sync_time - now

    # Sleep only if the sync time is in the future
    if difference > 0:
        sleep(difference)
        runtime.NEXT_SYNC_TIME_SET_SIGNAL.clear()
    else:
        # If the sync time is already past, just clear the signal
        runtime.NEXT_SYNC_TIME_SET_SIGNAL.clear()

# Extracts server IP and TCP port from the received OFFER message and stores them for TCP connection
def extract_server_information(msg, addr):

    offer_data = json.loads(msg.decode())
    tcp_ip = addr[0]
    tcp_port = offer_data["port"]

    with runtime.TCP_INFORMATION_MUTEX:
        runtime.TCP_SERVER_IP = tcp_ip
        runtime.TCP_SERVER_PORT = tcp_port

    print(f"[UDP INFO] Received OFFER from {tcp_ip}:{tcp_port}")

    runtime.TCP_CONNECTION_ACTIVE_SIGNAL.set()

# Sends a multicast DISCOVER message to search for servers
def send_discover_protocol(sock):
    message = protocols.protocol_DISCOVER()
    sock.sendto(message.encode(), (shared.MULTICAST_IP, shared.MULTICAST_PORT))

# Displays information about raty and waits 10s before retrying
def wait_before_retry():
    print("[UDP INFO] Retrying in 10 seconds...")
    sleep(10)