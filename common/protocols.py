import enum
import json

class PROTOCOLS(enum.Enum):
    DISCOVER = "DISCOVER"
    OFFER = "OFFER"
    BUSY = "BUSY"
    READY = "READY"
    ARCHIVE_INFO = "ARCHIVE_INFO"
    ARCHIVE_TASKS = "ARCHIVE_TASKS"
    NEXT_SYNC = "NEXT_SYNC"

def protocol_get_type(message: bytes) -> PROTOCOLS:
    json_message = json.loads(message)
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