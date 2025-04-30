import os
import threading
from time import sleep

import core.TCP_threads
import core.UDP_threads

def get_user_input():
    archive_folder_path = input("Enter folder path for archive: ")

    if not os.path.isdir(archive_folder_path):
        print("[ERROR] Invalid folder path")
        exit(1)

    unique_client_ID = input("Enter unique user ID: ")

    return unique_client_ID, archive_folder_path


def main():

    client_ID, folder_path = get_user_input()

    threading.Thread(target=core.UDP_threads.multicast_discoverer, daemon=True).start()
    threading.Thread(target=core.TCP_threads.TCP_manager,args=(client_ID, folder_path,), daemon=True).start()

    while True:
        sleep(10)

if __name__ == "__main__":
    main()



