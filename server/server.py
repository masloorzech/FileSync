import threading
from time import sleep

from core.TCP_threads import TCP_server
from core.UDP_threads import UDP_receiver

# Function to get user input for synchronization rate and TCP port
def get_user_input():
    sync_time = input("Enter sync rate in seconds: ")

    if not sync_time.isdigit() or int(sync_time) <= 0:
        print("Invalid sync rate. Must be a positive integer.")
        exit(-1)
    sync_time = int(sync_time)

    port = input("Enter TCP port (1024–65535): ")

    if not port.isdigit() or not (1024 <= int(port) <= 65535):
        print("Invalid port. Must be an integer between 1024 and 65535.")
        exit(-1)

    port = int(port)

    return sync_time, port

# Main function to run the server
def main():
    # Get user input for sync rate and port
    sync_time, port = get_user_input()

    # Start a new thread for the TCP server with the provided port and sync_time
    threading.Thread(target=TCP_server, args=(port,sync_time)).start()

    # Start a new thread for the UDP receiver with the provided port
    threading.Thread(target=UDP_receiver, args=(port, )).start()

    # The main thread sleeps indefinitely, keeping the program alive for the threads to continue running
    while True:
        sleep(10)

# If this file is executed as a standalone script, the following code runs
if __name__ == '__main__':
    main()

