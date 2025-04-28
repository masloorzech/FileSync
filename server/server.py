import queue
import socket
import struct
import threading
from time import sleep

import common.protocols as protocols

MULTICAST_IP = "224.0.0.1"
MULTICAST_PORT = 8000
TCP_PORT = 5000

client_queue = queue.Queue()
current_client = None
lock = threading.Lock()

def handle_USP_service(conn, addr):
    global current_client
    try:
        conn.sendall(protocols.protocol_READY().encode())
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"[{addr}] Connection closed.")
                break
            print(f"[{addr}] Received data: {data}")
            conn.sendall(b"ACK\n")
    except Exception as e:
        print(f"[{addr}] Error: {e}")
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
    #todo handeling user input
    period = 60
    TCP_server_thread = threading.Thread(target=TCP_server).start()
    thread = threading.Thread(target=UDP_receiver).start()

    while True:
        sleep(10)
