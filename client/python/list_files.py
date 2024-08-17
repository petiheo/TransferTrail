import socket
import sys
import json
from datetime import datetime
from config import HOST, SERVER_PORT
from models.file_info import FileInfo
from models.message_structure import *

def recv_list_from_server(conn):
    send_file_list_request(conn)
    op_code, payload = recv_message(conn)
    if op_code != OpCode.FILE_LIST_RESPONSE:
        raise ValueError("Unexpected response from server")
    
    file_list = []
    for line in payload.decode().split('\n'):
        name, size, last_modified = line.split(',')
        file_list.append(FileInfo(name, int(size), datetime.fromisoformat(last_modified)))
    return file_list

def main():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, SERVER_PORT))
            print('Connected to server', file=sys.stderr)
            fileList = recv_list_from_server(client)
            print(json.dumps([fileInfo.to_dict() for fileInfo in fileList]))
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()