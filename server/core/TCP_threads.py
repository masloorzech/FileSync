import queue
import socket
import threading
from datetime import datetime, timedelta
from . import protocols_handlers
from common import protocols

client_queue = queue.Queue()
current_client = None
lock = threading.Lock()

def handle_USP_service(conn, addr, sync_time):
    global current_client, lock, client_queue
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
                files_to_send = protocols_handlers.handle_archive_info(data.decode())
                message = protocols.protocol_ARCHIVE_TASKS(files_to_send).encode()
                print(message)
                conn.sendall(message)

            if type == protocols.PROTOCOLS.ARCHIVE_DATA:
                protocols_handlers.handle_archive_data(data.decode())
                timestamp = (datetime.now() + timedelta(seconds=sync_time)).timestamp()
                message = protocols.protocol_NEXT_SYNC(timestamp).encode()
                print(message)
                conn.sendall(message)
                return


    finally:
        conn.close()
        with lock:
            current_client = None

def queue_manager(tcp_port):
    global current_client
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', tcp_port))
    server_socket.listen(5)

    print(f"TCP server listening on port {tcp_port}")

    while True:
        conn, addr = server_socket.accept()
        if current_client is not None:
            conn.sendall(protocols.protocol_BUSY().encode())
        print(f"Connection from {addr} accepted")
        client_queue.put((conn, addr))

def TCP_server(tcp_port,sync_time):
    global current_client, lock, client_queue

    threading.Thread(target=queue_manager, args=(tcp_port,)).start()

    while True:
        with lock:
            if current_client is None and not client_queue.empty():
                conn, addr = client_queue.get()
                current_client = conn
                threading.Thread(target=handle_USP_service, args=(conn, addr, sync_time)).start()