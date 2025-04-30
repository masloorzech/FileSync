# Multicast configuration constants
"""
Contains network configuration constants shared across the application:
- MULTICAST_IP — the multicast group IP used for communication.
- MULTICAST_PORT — the port number all nodes listen to/send on.
"""
MULTICAST_PORT = 8000           # Port number used for multicast communication
MULTICAST_IP = "224.0.0.1"      # IP address of the multicast group (in the local multicast range)