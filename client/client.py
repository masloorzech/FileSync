import json
import os
import struct
import threading
import socket
from time import sleep
import common.protocols as protocols
from queue import Queue

MULTICAST_PORT = 8000
MULTICAST_IP = "224.0.0.1"


#GLOBAL VARIABLE
TCP_SERVER_PORT = 0
TCP_SERVER_IP = ""
mutex = threading.Lock()

tcp_connection_active = threading.Event()

archive_folder_path =""
unique_client_ID = ""

COMMUNICATION_NODE = protocols.PROTOCOLS.NOT_PROTOCOL_INFO
communication_node_mutex = threading.Lock()
read_communication_node = threading.Event()

def send_to_sender(protocol: protocols.PROTOCOLS):
    global COMMUNICATION_NODE
    with communication_node_mutex:
        COMMUNICATION_NODE = protocol

def get_protocol_form_receiver() -> protocols.PROTOCOLS:
    global COMMUNICATION_NODE
    with communication_node_mutex:
        return COMMUNICATION_NODE

def collect_files(folder_path):
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append({
                'filename': filename,
                'file_path': file_path
            })
    return files

def TCP_sender(tcp_socket):
    global unique_client_ID, archive_folder_path
    files = collect_files(archive_folder_path)

    while True:
        read_communication_node.wait()
        try:
            message = protocols.protocol_NOT_PROTOCOL_INFO()

            protocol = get_protocol_form_receiver()

            if protocol == protocols.PROTOCOLS.NEXT_SYNC:
                return

            if protocol == protocols.PROTOCOLS.READY:
                message = protocols.protocol_ARCHIVE_INFO(unique_client_ID, files)

            if protocol == protocols.PROTOCOLS.ARCHIVE_TASKS:
                #TODO send files
                pass

            tcp_socket.send(message.encode())
            read_communication_node.clear()

        except socket.error as e:
            print(f"[ERROR TCP_sender] TCP connection closed by server: {e}")
            return


def TCP_receiver(tcp_socket):
    while True:
        try:
            data = tcp_socket.recv(1024)

            if not data:
                print("[ERROR] TCP connection closed by server")
                break

            protocol = protocols.protocol_get_type(data)
            print(data.decode())

            print(f"[INFO] TCP connection received: {protocols.PROTOCOLS(protocol)}")

            send_to_sender(protocol)
            read_communication_node.set()

        except socket.error as e:
            print(f"[ERROR TCP_receiver] TCP connection closed by server: {e}")
            read_communication_node.set()
            return


def TCP_manager():
    global TCP_SERVER_PORT, TCP_SERVER_IP
    while True:
        # waiting for signal form UDP about connection
        tcp_connection_active.wait()

        #after wait tries to create TCP socket
        with mutex:
            tcp_server_port = TCP_SERVER_PORT
            tcp_server_ip = TCP_SERVER_IP

        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            tcp_socket.connect((tcp_server_ip, tcp_server_port))

        except socket.error as e:
            print("Cannot perform connection to TCP server {e}".format(e=e))

            #if program cannot perform connection tcp_connection flag is set to false
            tcp_connection_active.clear()

            continue

        #if program performend connection starts two threads one to send data one to receive data

        receiver = threading.Thread(target=TCP_receiver, args=(tcp_socket,))
        receiver.start()

        sender = threading.Thread(target=TCP_sender, args=(tcp_socket,))
        sender.start()

        sender.join()
        receiver.join()

        tcp_socket.close()

        tcp_connection_active.clear()




def multicast_discoverer():
    global TCP_SERVER_PORT
    global TCP_SERVER_IP

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 1))

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    recv_sock.bind(('', MULTICAST_PORT))

    mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST_IP), socket.inet_aton("0.0.0.0"))
    recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    recv_sock.settimeout(5)

    message = protocols.protocol_DISCOVER()
    while True:
        if tcp_connection_active.is_set():
            sleep(5)
            continue
        try:
            print('Sending DISCOVERY')

            sock.sendto(message.encode(), (MULTICAST_IP, MULTICAST_PORT))

            msg, addr = recv_sock.recvfrom(1024)

            msg_type = protocols.protocol_get_type(msg)

            if msg_type == protocols.PROTOCOLS.OFFER:
                offer_data = json.loads(msg.decode())
                tcp_ip = addr[0]
                tcp_port = offer_data["port"]

                with mutex:
                    TCP_SERVER_IP = tcp_ip
                    TCP_SERVER_PORT = tcp_port

                print(f"[DISCOVERY] Received OFFER from {tcp_ip}:{tcp_port}")

                tcp_connection_active.set()
                continue

            sleep(10)

        except socket.timeout:
            print("[DISCOVERY] No OFFER received. Sleeping 10 seconds before retrying...")
            sleep(10)

        except Exception as e:
            print(f"[DISCOVERY] Error: {e}")
            sleep(10)

if __name__ == "__main__":

    archive_folder_path = input("Enter folder path for archive: ")

    if not os.path.isdir(archive_folder_path):
        print("[ERROR] Invalid folder path")
        exit(1)

    unique_client_ID = input("Enter unique user ID: ")

    threading.Thread(target=multicast_discoverer, daemon=True).start()
    threading.Thread(target=TCP_manager, daemon=True).start()

    while True:
        sleep(1)



