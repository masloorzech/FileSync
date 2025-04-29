import base64
import enum
import json
import os
import time
from datetime import datetime


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

def read_protocol_data(message: bytes):
    return json.loads(message)

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
    return json.dumps({
        "type": "ARCHIVE_INFO",
        "client_id": client_id,
        "files": files
    })

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

def protocol_NEXT_SYNC(next_sync_time):
    return json.dumps({
        "type": "NEXT_SYNC",
        "next_sync_time": next_sync_time
    })

def protocol_NOT_PROTOCOL_INFO():
    return json.dumps({
        "type": "NOT_PROTOCOL_INFO"
    })