import enum
import json
import os
import time


class PROTOCOLS(enum.Enum):
    DISCOVER = "DISCOVER"
    OFFER = "OFFER"
    BUSY = "BUSY"
    READY = "READY"
    ARCHIVE_INFO = "ARCHIVE_INFO"

    ARCHIVE_TASKS = "ARCHIVE_TASKS"

    ARCHIVE_DATA = "ARCHIVE_DATA"

    NEXT_SYNC = "NEXT_SYNC"

    NOT_PROTOCOL_INFO = "NOT_PROTOCOL_INFO"

def protocol_get_type(message: bytes) -> PROTOCOLS:
    try:
        json_message = json.loads(message)
    except Exception as e:
        return PROTOCOLS.NOT_PROTOCOL_INFO

    return PROTOCOLS(json_message["type"])

def protocol_DISCOVER():
    return json.dumps({
        "type": "DISCOVER"
    })

def protocol_OFFER(port):
    return json.dumps({
        "type": "OFFER",
        "port": port
    })

def protocol_BUSY():
    return json.dumps({
        "type": "BUSY"
    })

def protocol_READY():
    return json.dumps({
        "type": "READY"
    })


def protocol_ARCHIVE_INFO(client_id, files):
    file_info = []

    for file in files:
        file_path = file['file_path']
        last_modified_time = time.ctime(os.path.getmtime(file_path))
        file_info.append({
            "filename": file['filename'],
            "file_path": file_path,
            "last_modified": last_modified_time
        })

    return json.dumps({
        "type": "ARCHIVE_INFO",
        "client_id": client_id,
        "files": file_info
    })

def protocol_ARCHIVE_TASKS(files_to_send):
    return json.dumps({
        "type": "ARCHIVE_TASKS",
        "files_to_send": files_to_send
    })


def protocol_NEXT_SYNC(next_sync_time):
    return json.dumps({
        "type": "NEXT_SYNC",
        "next_sync_time": next_sync_time
    })