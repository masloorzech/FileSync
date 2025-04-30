## FileSync 🚀
FileSync is a file synchronization and management tool that uses both TCP and UDP communication 
protocols to handle file transfers and synchronization between a client and a server. 
It ensures that files are efficiently and securely synchronized, keeping them up-to-date between
devices or systems.

## Features ✨
- TCP Server: Handles file synchronization tasks and manages connections with multiple clients.
- UDP Discovery: Uses multicast to allow clients to discover the server and establish communication.
- File Comparison: Compares file modification dates to determine if a file needs to be transferred or updated.
- File Storage: Saves client files in an organized directory structure, with support for handling large amounts of data.
- Synchronization Rate: Allows users to set a synchronization rate for file updates and transfers.

## Custom Protocols 🔧
In FileSync, communication between the client and server is managed using custom protocols designed to handle file synchronization tasks efficiently. These protocols are built on top of standard networking protocols (TCP/UDP) and are structured in a way that allows for smooth communication during file transfers, discovery, and synchronization.

### Overview of Protocols 📝
The project uses JSON-based protocols that define the structure of the messages exchanged between the server and the client. The communication is split into different types of messages, each serving a specific purpose in the synchronization process.

### Protocol Types 📝
Here are the primary protocol types used in FileSync:

1. **DISCOVER**
   - Sent by the client to discover available server.
     ```json
     {
       "type": "DISCOVER"
     }
     ```

2. **OFFER**
   - Sent by the server in response to a DISCOVER message, offering a connection (including the TCP port number).
     ```json
     {
       "type": "OFFER",
       "port": 12345
     }
     ```

3. **BUSY**
   - Sent by the server when it is unavailable.
     ```json
     {
       "type": "BUSY"
     }
     ```

4. **READY**
   - Sent by the server to indicate it is ready for file exchange.
     ```json
     {
       "type": "READY"
     }
     ```

5. **ARCHIVE_INFO**
   - Sent by the client to provide details about the files to be archived or synchronized.
     ```json
     {
       "type": "ARCHIVE_INFO",
       "client_id": "id",
       "files": [
         {
           "filename": "file.txt",
           "file_path": "documents/file.txt"
         }
       ]
     }
     ```

6. **ARCHIVE_TASKS**
   - Sent by the server to specify which files need to be archived.
     ```json
     {
       "type": "ARCHIVE_TASKS",
       "files": [
         {
           "filename": "file.txt",
           "file_path": "documents/file.txt"
         }
       ]
     }
     ```

7. **ARCHIVE_DATA**
   - Sent by the client with base64-encoded file data and associated metadata (e.g., modification timestamp).
     ```json
     {
       "type": "ARCHIVE_DATA",
       "client_id": "id",
       "files_data": [
         {
           "filename": "file.txt",
           "file_path": "documents/file.txt",
           "last_modified": "2025-04-29T14:00:00",
           "content": "base64-encoded-data"
         }
       ]
     }
     ```

8. **NEXT_SYNC**
   - Sent by the server to indicate the time for the next synchronization.
     ```json
     {
       "type": "NEXT_SYNC",
       "next_sync_time": "2025-05-01T12:00:00"
     }
     ```

9. **NOT_PROTOCOL_INFO**
   - Indicates that the received message does not conform to any known protocol.
     ```json
     {
       "type": "NOT_PROTOCOL_INFO"
     }
     ```
     
### Protocol Handling ⚙️

The custom protocols are handled through the `protocols.py` file. Each protocol type has a corresponding function that generates a JSON-encoded message. Functions are available for encoding and decoding messages, including file data and metadata.

## Getting Started 🏁

### Prerequisites 📚

- Python 3.x
- Dependencies listed in the `requirements.txt` file.

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/FileSync.git
cd FileSync
```

2. Install the necessary dependencies (if any):

```bash    
pip install -r requirements.txt
```

3. Run the application:

 ```bash
python server/server.py
python client/client.py
```