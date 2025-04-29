import base64
import json
import os
import queue
import socket
import struct
import threading
import time
from datetime import datetime, timedelta
from time import sleep

import common.protocols as protocols
import common.net_sockets as nt

MULTICAST_IP = "224.0.0.1"
MULTICAST_PORT = 8000
TCP_PORT = 5000

client_queue = queue.Queue()
current_client = None
lock = threading.Lock()

ARCHIVE_INFO = None

#REFRESH RATE IN SECONDS
REFRESH_RATE = 20

def ensure_subfolders_exist(full_server_path):
    folder_path = os.path.dirname(full_server_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def compare_file_dates(client_file, server_file_path):
    try:
        client_file_date = datetime.fromisoformat(client_file["last_modified"])
    except Exception as e:
        print(f"Invalid data format: {client_file['last_modified']}. ERROR: {e}")
        return True

    if os.path.exists(server_file_path):
        server_file_date = datetime.fromtimestamp(os.path.getmtime(server_file_path))
        return client_file_date > server_file_date
    return True

def create_client_folder(client_id, folder_name="archive"):
    path = os.path.join(folder_name, client_id)
    os.makedirs(path, exist_ok=True)
    return path

def handle_archive_info(data):
    archive_info = json.loads(data)
    client_id = archive_info["client_id"]
    files = archive_info["files"]

    archive_folder = create_client_folder(client_id)

    files_to_send = []
    server_all_paths = set()

    for file in files:
        relative_path = os.path.normpath(file["relative_path"])
        client_filename = file["filename"]

        server_file_path = os.path.join(archive_folder, relative_path)

        folder_path = os.path.dirname(server_file_path)
        os.makedirs(folder_path, exist_ok=True)

        server_all_paths.add(server_file_path)

        if compare_file_dates(file, server_file_path):
            files_to_send.append((client_filename, relative_path))


    for dirpath, _, filenames in os.walk(archive_folder):
        for filename in filenames:
            full_path = os.path.normpath(os.path.join(dirpath, filename))
            if full_path not in server_all_paths:
                os.remove(full_path)

    return files_to_send

def handle_archive_data(data):
    archive_data = json.loads(data)
    files_data = archive_data.get("files_data", [])

    client_id = archive_data["client_id"]

    archive_folder = os.path.join("archive", client_id)
    print(f"Archive: {archive_folder}")


    for file_info in files_data:

        file_path = file_info["file_path"]
        last_modified = file_info["last_modified"]
        content_base64 = file_info["content"]

        server_file_path = os.path.join(archive_folder, file_path)

        print(f"File: {server_file_path}")

        os.makedirs(os.path.dirname(server_file_path), exist_ok=True)

        with open(server_file_path, "wb") as f:
            file_bytes = base64.b64decode(content_base64.encode("utf-8"))
            f.write(file_bytes)

        try:
            dt = datetime.fromisoformat(last_modified)
            mod_time = time.mktime(dt.timetuple())
            os.utime(server_file_path, (mod_time, mod_time))
        except Exception as e:
            print(f"[ERROR] Couldn't set time for file {server_file_path}: {e}")

    return


def handle_USP_service(conn, addr):
    global current_client, ARCHIVE_INFO
    message = ""
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
                message = protocols.protocol_ARCHIVE_TASKS(files_to_send).encode()
                conn.sendall(message)

            if type == protocols.PROTOCOLS.ARCHIVE_DATA:
                handle_archive_data(data.decode())
                timestamp = (datetime.now() + timedelta(seconds=REFRESH_RATE)).timestamp()
                message = protocols.protocol_NEXT_SYNC(timestamp).encode()
                conn.sendall(message)
                return

            print(message)

    finally:
        conn.close()
        with lock:
            current_client = None

def queue_manager():
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

    threading.Thread(target=queue_manager).start()

    while True:
        with lock:
            if current_client is None and not client_queue.empty():
                conn, addr = client_queue.get()
                current_client = conn
                threading.Thread(target=handle_USP_service, args=(conn, addr)).start()


def UDP_receiver():

    receive_socket = nt.create_UDP_receive_socket(MULTICAST_IP, MULTICAST_PORT)

    send_socket = nt.create_UDP_send_socket()

    while True:
        msg, address = receive_socket.recvfrom(1024)
        type = protocols.protocol_get_type(msg)

        if type == protocols.PROTOCOLS.DISCOVER:
            offer_message = protocols.protocol_OFFER(TCP_PORT)
            print("Received from ", address)
            send_socket.sendto(offer_message.encode(), (MULTICAST_IP, MULTICAST_PORT))



if __name__ == '__main__':

    TCP_server_thread = threading.Thread(target=TCP_server).start()
    thread = threading.Thread(target=UDP_receiver).start()

    while True:
        sleep(10)
