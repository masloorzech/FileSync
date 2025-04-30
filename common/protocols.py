import base64
import enum
import json
import os
from datetime import datetime

"""
This file defines the structure and behavior of all protocol messages used in communication between clients/servers.

    - Declares the PROTOCOLS enumeration containing supported protocol message types (e.g., DISCOVER, OFFER, ARCHIVE_DATA, etc.).
    - Provides factory functions that generate JSON-encoded protocol messages for each supported action.
    - Handles encoding/decoding, including reading protocol type, encoding files using base64, and embedding metadata (e.g., modification timestamps).
"""

# Enumeration of available protocol message types.
class PROTOCOLS(enum.Enum):
    DISCOVER = "DISCOVER"                 # Sent to discover available servers/clients.

    OFFER = "OFFER"                       # Sent in response to DISCOVER to offer a connection.
    BUSY = "BUSY"                         # Sent when the recipient is currently unavailable.
    READY = "READY"                       # Indicates readiness to begin data exchange.

    ARCHIVE_INFO = "ARCHIVE_INFO"         # Contains information about archives sends to the server, files that client want to save on the server.
    ARCHIVE_TASKS = "ARCHIVE_TASKS"       # Contains a list of files to be archived.
    ARCHIVE_DATA = "ARCHIVE_DATA"         # Contains the actual encoded file data for archiving.

    NEXT_SYNC = "NEXT_SYNC"               # Suggests the time for the next synchronization.

    NOT_PROTOCOL_INFO = "NOT_PROTOCOL_INFO"  # Indicates the message does not conform to any known protocol.


# Decodes a JSON-formatted byte string and returns the corresponding Python object.
def read_protocol_data(message: bytes):
    return json.loads(message)

# Attempts to determine the protocol type from a JSON-formatted message.
# If the type field is missing or invalid, returns NOT_PROTOCOL_INFO.
def protocol_get_type(message: bytes) -> PROTOCOLS:
    try:
        json_message = json.loads(message)
    except Exception as e:
        return PROTOCOLS.NOT_PROTOCOL_INFO

    return PROTOCOLS(json_message["type"])

# Creates a DISCOVER protocol message.
def protocol_DISCOVER():
    return json.dumps({
        "type": "DISCOVER"
    })

# Creates an OFFER protocol message containing the port number to connect to.
def protocol_OFFER(port):
    return json.dumps({
        "type": "OFFER",
        "port": port
    })

# Creates a BUSY protocol message to indicate that the TCP server is currently unavailable.
def protocol_BUSY():
    return json.dumps({
        "type": "BUSY"
    })

# Creates a READY protocol message to indicate that TCP server is ready to proceed.
def protocol_READY():
    return json.dumps({
        "type": "READY"
    })

# Creates an ARCHIVE_INFO message including a client ID and list of files to create backup.
def protocol_ARCHIVE_INFO(client_id, files):
    return json.dumps({
        "type": "ARCHIVE_INFO",
        "client_id": client_id,
        "files": files
    })

# Creates an ARCHIVE_TASKS message that contains data about files to be archived.
def protocol_ARCHIVE_TASKS(files):
    file_info = []

    for file in files:
        file_info.append({
            "filename": file[0],
            "file_path": file[1],
        })
    return json.dumps({
        "type": "ARCHIVE_TASKS",
        "files": file_info
    })

# Creates an ARCHIVE_DATA message containing base64-encoded contents of files and metadata.
# Includes last modification time and full data for each file.
def protocol_ARCHIVE_DATA(files, client_id,path):
    files_data =[]

    for file in files:

        file_path = file['file_path']

        mtime = os.path.getmtime(path+"\\"+file_path)
        last_modified_time = datetime.fromtimestamp(mtime).isoformat()

        with open(path+"\\"+file_path, "rb") as f:
            encoded_content = base64.b64encode(f.read()).decode('utf-8')

        files_data.append({
            "filename": file['filename'],
            "file_path": file_path,
            "last_modified": last_modified_time,
            "content": encoded_content
        })

    return json.dumps({
        "type": "ARCHIVE_DATA",
        "client_id": client_id,
        "files_data": files_data
    })

# Creates a NEXT_SYNC message specifying the next planned synchronization time.
def protocol_NEXT_SYNC(next_sync_time):
    return json.dumps({
        "type": "NEXT_SYNC",
        "next_sync_time": next_sync_time
    })

# Creates a NOT_PROTOCOL_INFO message indicating an invalid or unrecognized protocol message.
def protocol_NOT_PROTOCOL_INFO():
    return json.dumps({
        "type": "NOT_PROTOCOL_INFO"
    })