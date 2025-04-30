import os
import threading
from time import sleep

import core.TCP_threads         # Module responsible for handling TCP-related logic
import core.UDP_threads         # Module responsible for handling UDP discovery logic

# Function to get required input from the user at program start
def get_user_input():
    archive_folder_path = input("Enter folder path for archive: ")

    if not os.path.isdir(archive_folder_path):
        print("[ERROR] Invalid folder path")
        exit(1)

    unique_client_ID = input("Enter unique user ID: ")

    return unique_client_ID, archive_folder_path

# Main function of the client program
def main():

    # Retrieve user input before starting background processes
    client_ID, folder_path = get_user_input()

    # Start UDP multicast discovery in a background thread (daemon = will stop with main process)
    threading.Thread(target=core.UDP_threads.multicast_discoverer, daemon=True).start()

    # Start the TCP manager thread that will handle connections and data exchange
    threading.Thread(target=core.TCP_threads.TCP_manager,args=(client_ID, folder_path,), daemon=True).start()

    # Keep the main thread alive so that background threads keep running
    while True:
        sleep(10)

# Run the main function only if this file is executed directly (not imported)
if __name__ == "__main__":
    main()



