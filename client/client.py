import json
import struct
import threading
import socket
from time import sleep
import common.protocols as protocols

MULTICAST_PORT = 8000
MULTICAST_IP = "224.0.0.1"

#GLOBAL VARIABLE
TCP_SERVER_PORT = 0
TCP_SERVER_IP = ""
mutex = threading.Lock()

tcp_connection_active = threading.Event()

def TCP_connection():
    global TCP_SERVER_PORT, TCP_SERVER_IP
    while True:
        tcp_connection_active.wait()
        try:
            with mutex:
                print("TCP_SERVER_PORT:", TCP_SERVER_PORT)
                print("TCP_SERVER_IP:", TCP_SERVER_IP)
                TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    TCP_socket.connect((TCP_SERVER_IP, TCP_SERVER_PORT))
                    print("TCP connection established")

                    while True:
                        sleep(10)

                except socket.timeout:
                    print("[ERROR] TCP connection timed out")

                finally:
                    TCP_socket.close()
                    print("[INFO] Zamknięcie połączenia")
        except Exception as e:
            print(f"[ERROR] Global error: {e}")
            tcp_connection_active.clear()
            sleep(10)


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
            print("[DISCOVERY] Waiting for OFFER response...")

            msg, addr = recv_sock.recvfrom(1024)

            msg_type = protocols.protocol_get_type(msg)

            if msg_type == protocols.PROTOCOLS.OFFER:
                offer_data = json.loads(msg.decode())
                tcp_ip = addr[0]
                tcp_port = offer_data["port"]
                print(f"[DISCOVERY] Received OFFER from {tcp_ip}:{tcp_port}")
                with mutex:
                    TCP_SERVER_PORT = tcp_port
                    TCP_SERVER_IP = tcp_ip
                tcp_connection_active.set()


            sleep(10)

        except socket.timeout:
            print("[DISCOVERY] No OFFER received. Sleeping 10 seconds before retrying...")
            sleep(10)

        except Exception as e:
            print(f"[DISCOVERY] Error: {e}")
            sleep(10)

def fake_tcp_connection_simulator():
    while True:
        sleep(15)
        print("[SIMULATION] TCP connection established")
        tcp_connection_active.set()
        sleep(10)
        print("[SIMULATION] TCP connection lost")
        tcp_connection_active.clear()

if __name__ == "__main__":
    #open thread witch waits for connection
    threading.Thread(target=multicast_discoverer,  daemon=True).start()
    threading.Thread(target=TCP_connection, daemon=True).start()
    while True:
        sleep(1)



