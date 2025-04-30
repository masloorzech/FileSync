import queue
import socket
import threading
from datetime import datetime, timedelta
from . import protocols_handlers
from common import protocols

# Initialize a queue to manage incoming client connections
CLIENT_QUEUE = queue.Queue()

# Global variable to track the current client being served
CURRENT_CLIENT = None

# Lock object to ensure thread safety when accessing global variables
CURRENT_CLIENT_MUTEX = threading.Lock()

# This function handles the USP service for a given connection
# It processes incoming requests, sends responses, and manages the file synchronization process.
def handle_USP_service(conn, addr, sync_time):
    global CURRENT_CLIENT, CURRENT_CLIENT_MUTEX, CLIENT_QUEUE
    message = ""
    try:
        # Send a READY signal to the client to confirm readiness
        conn.sendall(protocols.protocol_READY().encode())

        while True:
            data = conn.recv(1024)

            # If no data is received, the connection has been closed by the client
            if not data:
                print(f"[{addr}] Connection closed.")
                break

            print(f"[{addr}] Received data: {data.decode()}")

            # Decode the protocol type of the received message
            type = protocols.protocol_get_type(data)

            # If the message is of type ARCHIVE_INFO, process the archive information
            if type == protocols.PROTOCOLS.ARCHIVE_INFO:
                files_to_send = protocols_handlers.handle_archive_info(data.decode())
                message = protocols.protocol_ARCHIVE_TASKS(files_to_send).encode()
                conn.sendall(message)

            # If the message is of type ARCHIVE_DATA, process the archive data
            if type == protocols.PROTOCOLS.ARCHIVE_DATA:
                protocols_handlers.handle_archive_data(data.decode())
                timestamp = (datetime.now() + timedelta(seconds=sync_time)).timestamp()
                message = protocols.protocol_NEXT_SYNC(timestamp).encode()
                print(message)
                conn.sendall(message)
                return


    finally:
        # Close the connection once the service is done
        conn.close()

        # Release the lock and set the current client to None, indicating no active client
        with CURRENT_CLIENT_MUTEX:
            CURRENT_CLIENT = None

# This function manages incoming connections, accepts clients, and places them in the client queue
def queue_manager(tcp_port):
    global CURRENT_CLIENT
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', tcp_port))
    server_socket.listen(5)

    print(f"TCP server listening on port {tcp_port}")

    while True:
        # Accept an incoming connection
        conn, addr = server_socket.accept()

        # If there is already an active client, send a "BUSY" message to the new client
        if CURRENT_CLIENT is not None:
            conn.sendall(protocols.protocol_BUSY().encode())

        print(f"Connection from {addr} accepted")
        # Put the connection and address into the client queue for further processing
        CLIENT_QUEUE.put((conn, addr))

# This function manages the overall TCP server. It starts the queue manager and processes clients.
def TCP_server(tcp_port,sync_time):
    global CURRENT_CLIENT, CURRENT_CLIENT_MUTEX, CLIENT_QUEUE

    # Start the queue manager in a separate thread
    threading.Thread(target=queue_manager, args=(tcp_port,)).start()

    while True:
        with CURRENT_CLIENT_MUTEX:

            # If there is no active client and there are clients in the queue, process the next client
            if CURRENT_CLIENT is None and not CLIENT_QUEUE.empty():
                conn, addr = CLIENT_QUEUE.get()

                # Set the current client to the new connection
                CURRENT_CLIENT = conn

                # Start a new thread to handle the USP service for the client
                threading.Thread(target=handle_USP_service, args=(conn, addr, sync_time)).start()