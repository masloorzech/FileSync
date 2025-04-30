import base64
import json
import os
import time
from datetime import datetime

from . import os_operation

def handle_archive_info(data):
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

        folder_path = os.path.dirname(server_file_path)
        os.makedirs(folder_path, exist_ok=True)

        server_all_paths.add(server_file_path)

        if os_operation.compare_file_dates(file, server_file_path):
            files_to_send.append((client_filename, relative_path))


    for dirpath, _, filenames in os.walk(archive_folder):
        for filename in filenames:
            full_path = os.path.normpath(os.path.join(dirpath, filename))
            if full_path not in server_all_paths:
                os.remove(full_path)

    return files_to_send

def handle_archive_data(data):
    archive_data = json.loads(data)
    files_data = archive_data.get("files_data", [])

    client_id = archive_data["client_id"]

    archive_folder = os.path.join("archive", client_id)
    print(f"Archive: {archive_folder}")


    for file_info in files_data:

        file_path = file_info["file_path"]
        last_modified = file_info["last_modified"]
        content_base64 = file_info["content"]

        server_file_path = os.path.join(archive_folder, file_path)

        print(f"File: {server_file_path}")

        os.makedirs(os.path.dirname(server_file_path), exist_ok=True)

        with open(server_file_path, "wb") as f:
            file_bytes = base64.b64decode(content_base64.encode("utf-8"))
            f.write(file_bytes)

        try:
            dt = datetime.fromisoformat(last_modified)
            mod_time = time.mktime(dt.timetuple())
            os.utime(server_file_path, (mod_time, mod_time))
        except Exception as e:
            print(f"[ERROR] Couldn't set time for file {server_file_path}: {e}")

    return