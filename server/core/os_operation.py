import os
from datetime import datetime

# Ensures that all parent directories of the given file path exist.
# If not, creates them to allow safe writing of files later.
def ensure_subfolders_exist(full_server_path):
    folder_path = os.path.dirname(full_server_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

# Compares the last modified timestamp of a client-side file (given as string)
# with the server-side file (based on its actual file timestamp).
# Returns True if the client file is newer or the server file does not exist.
def compare_file_dates(client_file, server_file_path):
    try:
        client_file_date = datetime.fromisoformat(client_file["last_modified"])
    except Exception as e:
        print(f"Invalid data format: {client_file['last_modified']}. ERROR: {e}")
        return True

    if os.path.exists(server_file_path):
        server_file_date = datetime.fromtimestamp(os.path.getmtime(server_file_path))
        return client_file_date > server_file_date
    return True

# Creates a unique folder for the client using their ID under the default/archive folder.
# If the folder already exists, it does nothing.
# Returns the full path to the created (or existing) folder.
def create_client_folder(client_id, folder_name="archive"):
    path = os.path.join(folder_name, client_id)
    os.makedirs(path, exist_ok=True)
    return path