import json
import os
import queue
import socket
import struct
import threading
from datetime import datetime
from time import sleep

import common.protocols as protocols

MULTICAST_IP = "224.0.0.1"
MULTICAST_PORT = 8000
TCP_PORT = 5000

client_queue = queue.Queue()
current_client = None
lock = threading.Lock()

def compare_file_dates(client_file, server_file_path):
    client_file_date = datetime.strptime(client_file["last_modified"], "%a %b %d %H:%M:%S %Y")

    if os.path.exists(server_file_path):
        server_file_date = datetime.fromtimestamp(os.path.getmtime(server_file_path))
        return client_file_date > server_file_date
    return True

def create_client_folder(client_id, archive_base_path):
    client_folder_path = os.path.join(archive_base_path, client_id)
    if not os.path.exists(client_folder_path):
        os.makedirs(client_folder_path)
    return client_folder_path

def handle_archive_info(data):
    archive_info = json.loads(data)
    print("Received archive info:", archive_info)
    client_id = archive_info["client_id"]
    files = archive_info["files"]
    archive_folder = create_client_folder(client_id, "archive")

    files_to_send = []

    for file in files:
        client_filename = file["filename"]
        file_path = file["file_path"]
        server_file_path = os.path.join(archive_folder, os.path.relpath(file_path, "archive"))

        if compare_file_dates(file, server_file_path):
            files_to_send.append((client_filename, file_path))
        else:
            continue

        return files_to_send

def handle_USP_service(conn, addr):
    global current_client
    try:
        conn.sendall(protocols.protocol_READY().encode())
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"[{addr}] Connection closed.")
                break

            print(f"[{addr}] Received data: {data.decode()}")

            type = protocols.protocol_get_type(data)

            if type == protocols.PROTOCOLS.ARCHIVE_INFO:
                files_to_send = handle_archive_info(data.decode())
                conn.sendall(protocols.protocol_ARCHIVE_TASKS(files_to_send).encode())


    finally:
        conn.close()
        with lock:
            current_client = None

def accept_connections():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', TCP_PORT))
    server_socket.listen(5)

    print(f"TCP server listening on port {TCP_PORT}")

    while True:
        conn, addr = server_socket.accept()
        if current_client is not None:
            conn.sendall(protocols.protocol_BUSY().encode())
        print(f"Connection from {addr} accepted")
        client_queue.put((conn, addr))

def TCP_server():
    global current_client

    queue_manager = threading.Thread(target=accept_connections)
    queue_manager.start()

    while True:
        with lock:
            if current_client is None and not client_queue.empty():
                conn, addr = client_queue.get()
                current_client = conn
                threading.Thread(target=handle_USP_service, args=(conn, addr)).start()




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
            print("Received from ", address)
            send_sock.sendto(offer_message.encode(), (MULTICAST_IP, MULTICAST_PORT))



if __name__ == '__main__':
    period = 60
    TCP_server_thread = threading.Thread(target=TCP_server).start()
    thread = threading.Thread(target=UDP_receiver).start()

    while True:
        sleep(10)
