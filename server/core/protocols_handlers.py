import base64
import json
import os
import time
from datetime import datetime

from . import os_operation

# Handles incoming archive information by processing files that need to be sent
# and cleaning up files that should be removed.
# Returns a list of files to be sent to the server.
def handle_archive_info(data):
    # Parses incoming archive information (client ID and list of files)
    archive_info = json.loads(data)
    client_id = archive_info["client_id"]
    files = archive_info["files"]

    archive_folder = os_operation.create_client_folder(client_id)

    files_to_send = []
    server_all_paths = set()

    for file in files:
        relative_path = os.path.normpath(file["relative_path"])
        client_filename = file["filename"]

        server_file_path = os.path.join(archive_folder, relative_path)

        # Ensure the folder for the file exists
        folder_path = os.path.dirname(server_file_path)
        os.makedirs(folder_path, exist_ok=True)

        # Add the file path to the set of server file paths
        server_all_paths.add(server_file_path)

        # Check if the file needs to be sent (i.e., client file is newer than the server's)
        if os_operation.compare_file_dates(file, server_file_path):
            files_to_send.append((client_filename, relative_path))


    # Clean up any files on the server that no longer exist in the client’s archive
    for dirpath, _, filenames in os.walk(archive_folder):
        for filename in filenames:
            full_path = os.path.normpath(os.path.join(dirpath, filename))
            if full_path not in server_all_paths:
                os.remove(full_path)

    return files_to_send

# Handles the incoming data for files and saves them to the server.
# This function decodes the base64-encoded file contents and writes them to disk.
def handle_archive_data(data):
    # Parse the incoming archive data (client ID and file content)
    archive_data = json.loads(data)
    files_data = archive_data.get("files_data", [])

    client_id = archive_data["client_id"]

    # Define the folder for this client’s archive on the server
    archive_folder = os.path.join("archive", client_id)
    print(f"Archive: {archive_folder}")

    for file_info in files_data:

        # Extract information for the file to be saved
        file_path = file_info["file_path"]
        last_modified = file_info["last_modified"]
        content_base64 = file_info["content"]

        server_file_path = os.path.join(archive_folder, file_path)

        # Create any necessary directories for the file
        os.makedirs(os.path.dirname(server_file_path), exist_ok=True)

        # Decode the base64-encoded file content and write it to disk
        with open(server_file_path, "wb") as f:
            file_bytes = base64.b64decode(content_base64.encode("utf-8"))
            f.write(file_bytes)

        # Attempt to set the file's last modified timestamp
        try:
            dt = datetime.fromisoformat(last_modified)
            mod_time = time.mktime(dt.timetuple())
            os.utime(server_file_path, (mod_time, mod_time))
        except Exception as e:
            print(f"[ERROR] Couldn't set time for file {server_file_path}: {e}")

    return