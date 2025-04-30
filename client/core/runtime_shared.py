import threading
import time

TCP_SERVER_PORT = 0
TCP_SERVER_IP = ""
mutex = threading.Lock()

tcp_connection_active = threading.Event()
next_sync_time_set = threading.Event()
next_sync_time = time.time()

PROTOCOL_DATA_COMMUNICATION_NODE = None
communication_node_mutex = threading.Lock()
read_communication_node = threading.Event()