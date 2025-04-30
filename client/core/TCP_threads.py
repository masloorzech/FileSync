from datetime import datetime
from . import runtime_shared as runtime
import socket
import threading
import common.protocols as protocols
import os

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

def send_data_to_sender(data):
    with runtime.communication_node_mutex:
        runtime.PROTOCOL_DATA_COMMUNICATION_NODE = data

def get_data_form_receiver():
    with runtime.communication_node_mutex:
        return runtime.PROTOCOL_DATA_COMMUNICATION_NODE

def TCP_manager(unique_client_ID, archive_folder_path ):
    while True:

        # waiting for signal form UDP about connection
        runtime.tcp_connection_active.wait()

        #after wait tries to create TCP socket
        with runtime.mutex:
            tcp_server_port = runtime.TCP_SERVER_PORT
            tcp_server_ip = runtime.TCP_SERVER_IP

        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            tcp_socket.connect((tcp_server_ip, tcp_server_port))

        except socket.error as e:
            print("Cannot perform connection to TCP server {e}".format(e=e))

            #if program cannot perform connection tcp_connection flag is set to false
            runtime.tcp_connection_active.clear()

            continue

        #if program performed connection starts two threads one to send data one to receive data

        receiver = threading.Thread(target=TCP_receiver, args=(tcp_socket,))
        receiver.start()

        sender = threading.Thread(target=TCP_sender, args=(tcp_socket,unique_client_ID,archive_folder_path,))
        sender.start()

        sender.join()
        receiver.join()

        tcp_socket.close()

        runtime.read_communication_node.clear()
        runtime.tcp_connection_active.clear()

def TCP_sender(tcp_socket, unique_client_ID, archive_folder_path):

    while True:
        runtime.read_communication_node.wait()
        try:

            message = protocols.protocol_NOT_PROTOCOL_INFO()

            data = get_data_form_receiver()

            protocol = protocols.PROTOCOLS(data["type"])

            if protocol == protocols.PROTOCOLS.NEXT_SYNC:
                runtime.next_sync_time = data["next_sync_time"]
                runtime.next_sync_time_set.set()
                return

            if protocol == protocols.PROTOCOLS.READY:
                files = collect_files(archive_folder_path)
                message = protocols.protocol_ARCHIVE_INFO(unique_client_ID, files)

            if protocol == protocols.PROTOCOLS.ARCHIVE_TASKS:
                files_to_send = data["files"]
                message = protocols.protocol_ARCHIVE_DATA(files_to_send, client_id=unique_client_ID, path=archive_folder_path)


            print(f"[TCP INFO] Sending message {message}")

            tcp_socket.send(message.encode())

            runtime.read_communication_node.clear()

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
                    runtime.read_communication_node.set()
                    return

            runtime.read_communication_node.set()

        except socket.error as e:
            print(f"[ERROR TCP_receiver] TCP connection closed by server: {e}")
            runtime.read_communication_node.set()
            return
