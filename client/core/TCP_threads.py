from datetime import datetime
from . import runtime_shared as runtime
import socket
import threading
import common.protocols as protocols
import os

# Collects file metadata from a given folder (recursively).
# Returns a list of dictionaries with filename, relative path, and last modification time.
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

# Stores data in a thread-safe way to the shared communication node.
def send_data_to_sender(data):
    with runtime.PROTOCOL_DATA_COMMUNICATION_NODE_MUTEX:
        runtime.PROTOCOL_DATA_COMMUNICATION_NODE = data

# Retrieves data in a thread-safe way from the shared communication node.
def get_data_form_receiver():
    with runtime.PROTOCOL_DATA_COMMUNICATION_NODE_MUTEX:
        return runtime.PROTOCOL_DATA_COMMUNICATION_NODE

# Manages the TCP connection lifecycle.
# Waits for a connection signal, opens a socket, and launches sender/receiver threads.
def TCP_manager(unique_client_ID, archive_folder_path ):
    while True:

        # Wait for signal from UDP part that TCP connection should be established
        runtime.TCP_CONNECTION_ACTIVE_SIGNAL.wait()

        # Read connection parameters safely
        with runtime.TCP_INFORMATION_MUTEX:
            tcp_server_port = runtime.TCP_SERVER_PORT
            tcp_server_ip = runtime.TCP_SERVER_IP

        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            tcp_socket.connect((tcp_server_ip, tcp_server_port))

        except socket.error as e:
            print("Cannot perform connection to TCP server {e}".format(e=e))
            runtime.TCP_CONNECTION_ACTIVE_SIGNAL.clear()
            continue

        # Connection established – start sender and receiver threads

        receiver = threading.Thread(target=TCP_receiver, args=(tcp_socket,))
        receiver.start()

        sender = threading.Thread(target=TCP_sender, args=(tcp_socket,unique_client_ID,archive_folder_path,))
        sender.start()

        sender.join()
        receiver.join()

        # Cleanup after both threads finish

        tcp_socket.close()

        runtime.PROTOCOL_DATA_COMMUNICATION_NODE_SIGNAL.clear()
        runtime.TCP_CONNECTION_ACTIVE_SIGNAL.clear()

# Handles sending data over the TCP socket based on the received protocol type.
def TCP_sender(tcp_socket, unique_client_ID, archive_folder_path):
    while True:
        # Wait until there is data to send
        runtime.PROTOCOL_DATA_COMMUNICATION_NODE_SIGNAL.wait()
        try:

            message = protocols.protocol_NOT_PROTOCOL_INFO()

            data = get_data_form_receiver()

            protocol = protocols.PROTOCOLS(data["type"])

            # Handle sync time update
            if protocol == protocols.PROTOCOLS.NEXT_SYNC:
                runtime.next_sync_time = data["next_sync_time"]
                runtime.NEXT_SYNC_TIME_SET_SIGNAL.set()
                return

            # Prepare archive info
            if protocol == protocols.PROTOCOLS.READY:
                files = collect_files(archive_folder_path)
                message = protocols.protocol_ARCHIVE_INFO(unique_client_ID, files)

            # Prepare archive data for sending
            if protocol == protocols.PROTOCOLS.ARCHIVE_TASKS:
                files_to_send = data["files"]
                message = protocols.protocol_ARCHIVE_DATA(files_to_send, client_id=unique_client_ID, path=archive_folder_path)


            print(f"[TCP INFO] Sending message {message}")

            tcp_socket.send(message.encode())

            runtime.PROTOCOL_DATA_COMMUNICATION_NODE_SIGNAL.clear()

        except socket.error as e:
            print(f"[TCP ERROR TCP_sender] TCP connection closed by server: {e}")
            return


# Receives data over the TCP socket and notifies the system of new data.
def TCP_receiver(tcp_socket):
    while True:
        try:
            data = tcp_socket.recv(1024)

            if not data:
                print("[ERROR] TCP connection closed by server")
                break

            # Determine which protocol type was received
            protocol = protocols.protocol_get_type(data)

            print(f"[TCP INFO] TCP connection received: {protocols.PROTOCOLS(protocol)}")

            # Store and signal received data
            if protocol != protocols.PROTOCOLS.BUSY:
                send_data_to_sender(protocols.read_protocol_data(data))
                if protocol == protocols.PROTOCOLS.NEXT_SYNC:
                    runtime.PROTOCOL_DATA_COMMUNICATION_NODE_SIGNAL.set()
                    return

            runtime.PROTOCOL_DATA_COMMUNICATION_NODE_SIGNAL.set()

        except socket.error as e:
            print(f"[ERROR TCP_receiver] TCP connection closed by server: {e}")
            runtime.PROTOCOL_DATA_COMMUNICATION_NODE_SIGNAL.set()
            return
