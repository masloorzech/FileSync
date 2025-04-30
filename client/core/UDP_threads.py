import json
import socket
import time
from time import sleep
from datetime import datetime

import common.net_sockets as net_socket
import common.shared_globals as shared
import common.protocols as protocols
from . import runtime_shared as runtime


def multicast_discoverer():
    send_socket = net_socket.create_UDP_send_socket()

    receive_socket = net_socket.create_UDP_receive_socket(shared.MULTICAST_IP, shared.MULTICAST_PORT)
    receive_socket.settimeout(5)


    message = protocols.protocol_DISCOVER()
    while True:
        if runtime.NEXT_SYNC_TIME_SET_SIGNAL.is_set():
            print(f"[INFO] Sleeping while waiting for next sync time: {datetime.fromtimestamp(runtime.next_sync_time).strftime("%Y-%m-%d %H:%M:%S")}")
            now = time.time()
            difference = runtime.next_sync_time - now

            if difference > 0:
                sleep(difference)
                runtime.NEXT_SYNC_TIME_SET_SIGNAL.clear()
            else:
                runtime.NEXT_SYNC_TIME_SET_SIGNAL.clear()

        if runtime.TCP_CONNECTION_ACTIVE_SIGNAL.is_set():
            sleep(5)
            continue

        print('[UDP INFO] Sending DISCOVERY')

        try:
            send_socket.sendto(message.encode(), (shared.MULTICAST_IP, shared.MULTICAST_PORT))

            msg, addr = receive_socket.recvfrom(1024)

            msg_type = protocols.protocol_get_type(msg)

            if msg_type == protocols.PROTOCOLS.OFFER:
                offer_data = json.loads(msg.decode())
                tcp_ip = addr[0]
                tcp_port = offer_data["port"]

                with runtime.TCP_INFORMATION_MUTEX:
                    runtime.TCP_SERVER_IP = tcp_ip
                    runtime.TCP_SERVER_PORT = tcp_port

                print(f"[UDP INFO] Received OFFER from {tcp_ip}:{tcp_port}")

                runtime.TCP_CONNECTION_ACTIVE_SIGNAL.set()
                continue

            print("[UDP INFO] No OFFER received. Sleeping 10 seconds before retrying...")
            sleep(10)

        except socket.timeout:
            print("[UDP DISCOVERY] No OFFER received. Sleeping 10 seconds before retrying...")
            sleep(10)

        except Exception as e:
            print(f"[UDP DISCOVERY] Error: {e}")
            sleep(10)
