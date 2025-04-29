import json
import os
import struct
import threading
import socket
import time
from datetime import datetime
from time import sleep
import common.protocols as protocols
import common.net_sockets as nt
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

next_sync_time_set = threading.Event()
next_sync_time = time.time()

PROTOCOL_DATA_COMMUNICATION_NODE = None
communication_node_mutex = threading.Lock()
read_communication_node = threading.Event()

def send_data_to_sender(data):
    global PROTOCOL_DATA_COMMUNICATION_NODE
    with communication_node_mutex:
        PROTOCOL_DATA_COMMUNICATION_NODE = data

def get_data_form_receiver():
    global PROTOCOL_DATA_COMMUNICATION_NODE
    with communication_node_mutex:
        return PROTOCOL_DATA_COMMUNICATION_NODE

def collect_files(folder_path):
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            try:
                mtime = os.path.getmtime(file_path)
                mod_time_str = datetime.fromtimestamp(mtime).isoformat()
                relative_path = os.path.relpath(file_path, folder_path)
                files.append({
                    'filename': filename,
                    'relative_path': relative_path,
                    'last_modified': mod_time_str
                })
            except Exception as e:
                print(f"Error with: {file_path}: {e}")
    return files

def TCP_sender(tcp_socket):
    global unique_client_ID, archive_folder_path, next_sync_time

    while True:
        read_communication_node.wait()
        try:

            message = protocols.protocol_NOT_PROTOCOL_INFO()

            data = get_data_form_receiver()

            protocol = protocols.PROTOCOLS(data["type"])

            if protocol == protocols.PROTOCOLS.NEXT_SYNC:
                next_sync_time = data["next_sync_time"]
                next_sync_time_set.set()
                return

            if protocol == protocols.PROTOCOLS.READY:
                files = collect_files(archive_folder_path)
                message = protocols.protocol_ARCHIVE_INFO(unique_client_ID, files)

            if protocol == protocols.PROTOCOLS.ARCHIVE_TASKS:
                files_to_send = data["files"]
                message = protocols.protocol_ARCHIVE_DATA(files_to_send, client_id=unique_client_ID, path=archive_folder_path)


            print(f"[TCP INFO] Sending message {message}")

            tcp_socket.send(message.encode())

            read_communication_node.clear()

        except socket.error as e:
            print(f"[TCP ERROR TCP_sender] TCP connection closed by server: {e}")
            return


def TCP_receiver(tcp_socket):
    while True:
        try:
            data = tcp_socket.recv(1024)

            if not data:
                print("[ERROR] TCP connection closed by server")
                break

            protocol = protocols.protocol_get_type(data)

            print(f"[TCP INFO] TCP connection received: {protocols.PROTOCOLS(protocol)}")

            if protocol != protocols.PROTOCOLS.BUSY:
                send_data_to_sender(protocols.read_protocol_data(data))
                if protocol == protocols.PROTOCOLS.NEXT_SYNC:
                    read_communication_node.set()
                    return

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

        #if program performed connection starts two threads one to send data one to receive data

        receiver = threading.Thread(target=TCP_receiver, args=(tcp_socket,))
        receiver.start()

        sender = threading.Thread(target=TCP_sender, args=(tcp_socket,))
        sender.start()

        sender.join()
        receiver.join()

        tcp_socket.close()

        read_communication_node.clear()
        tcp_connection_active.clear()


def multicast_discoverer():
    global TCP_SERVER_PORT
    global TCP_SERVER_IP
    global next_sync_time

    send_socket = nt.create_UDP_send_socket()

    receive_socket = nt.create_UDP_receive_socket(MULTICAST_IP, MULTICAST_PORT)
    receive_socket.settimeout(5)


    message = protocols.protocol_DISCOVER()
    while True:
        if next_sync_time_set.is_set():
            print(f"[INFO] Sleeping while waiting for next sync time: {datetime.fromtimestamp(next_sync_time).strftime("%Y-%m-%d %H:%M:%S")}")
            now = time.time()
            difference = next_sync_time - now

            if difference > 0:
                time.sleep(difference)
                next_sync_time_set.clear()
            else:
                next_sync_time_set.clear()

        if tcp_connection_active.is_set():
            sleep(5)
            continue

        print('[UDP INFO] Sending DISCOVERY')

        try:
            send_socket.sendto(message.encode(), (MULTICAST_IP, MULTICAST_PORT))

            msg, addr = receive_socket.recvfrom(1024)

            msg_type = protocols.protocol_get_type(msg)

            if msg_type == protocols.PROTOCOLS.OFFER:
                offer_data = json.loads(msg.decode())
                tcp_ip = addr[0]
                tcp_port = offer_data["port"]

                with mutex:
                    TCP_SERVER_IP = tcp_ip
                    TCP_SERVER_PORT = tcp_port

                print(f"[UDP INFO] Received OFFER from {tcp_ip}:{tcp_port}")

                tcp_connection_active.set()
                continue

            print("[UDP INFO] No OFFER received. Sleeping 10 seconds before retrying...")
            sleep(10)

        except socket.timeout:
            print("[UDP DISCOVERY] No OFFER received. Sleeping 10 seconds before retrying...")
            sleep(10)

        except Exception as e:
            print(f"[UDP DISCOVERY] Error: {e}")
            sleep(10)

if __name__ == "__main__":


    # archive_folder_path = input("Enter folder path for archive: ")
    #
    # if not os.path.isdir(archive_folder_path):
    #     print("[ERROR] Invalid folder path")
    #     exit(1)
    #
    # unique_client_ID = input("Enter unique user ID: ")

    archive_folder_path = "archive"
    unique_client_ID = "lampa"

    threading.Thread(target=multicast_discoverer, daemon=True).start()
    threading.Thread(target=TCP_manager, daemon=True).start()

    while True:
        sleep(1)



