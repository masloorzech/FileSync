import threading
import time

# TCP server port – default is 0, seated when DISCOVERY reaches server and server sends back OFFER with port number.
TCP_SERVER_PORT = 0

# TCP server IP address - default is empty, but when OFFER comes set it to server IP .
TCP_SERVER_IP = ""

#Mutex to protect TCP_SERVER_PORT and TCP_SERVER_IP because these variables are used by multiple threads.
TCP_INFORMATION_MUTEX = threading.Lock()

# Event indicating whether the TCP connection is currently active.
TCP_CONNECTION_ACTIVE_SIGNAL = threading.Event()

# Event used to signal that the next synchronization time has been set.
# Used to protect next_sync_time variable against multithread access.
NEXT_SYNC_TIME_SET_SIGNAL = threading.Event()

# Timestamp for the next synchronization event, initialized with the current time, but always changes in runtime so initial time is dump value.
next_sync_time = time.time()

# Node which provides data exchange between TCP Sender and TCP Receiver threads.
# Sender sets this node receiver reads, protection ensured by using mutex below
PROTOCOL_DATA_COMMUNICATION_NODE = None

#Mutex to protect PROTOCOL_DATA_COMMUNICATION_NODE because variable is used by multiple threads.
PROTOCOL_DATA_COMMUNICATION_NODE_MUTEX = threading.Lock()

# Event to signal that TCP Receiver can read new information from socket.
PROTOCOL_DATA_COMMUNICATION_NODE_SIGNAL = threading.Event()