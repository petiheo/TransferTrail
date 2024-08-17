import socket
import threading
from file_list_handler import send_file_list
from download_handler import download_file
from upload_handler import upload_file

import config
from models.message_structure import *

def handle_client(conn, addr):
    print(f'Connected to {addr}')
    try:
        while True:
            op_code, payload = recv_message(conn)
            if op_code is None:
                print(f'Client {addr} disconnected.')
                break

            if op_code == OpCode.FILE_LIST_REQUEST:
                send_file_list(conn)
            elif op_code == OpCode.DOWNLOAD_REQUEST:
                download_file(conn, addr, payload)
            elif op_code == OpCode.UPLOAD_REQUEST:
                upload_file(conn, addr, payload)
            else:
                print(f'Unknown command from {addr}: {op_code}')
                break
    except Exception as e:
        print(f'Error handling client {addr}: {e}')
    finally:
        conn.close()
        print(f'Connection with {addr} closed.')

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mainSocket:
        mainSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mainSocket.bind((config.HOST, config.SERVER_PORT))
        mainSocket.listen()
        print('SERVER SIDE')
        while True:
            try:
                conn, addr = mainSocket.accept()
                clientThread = threading.Thread(target=handle_client, args=(conn, addr))
                clientThread.start()
            except Exception as e:
                print(f'Error accepting connection: {e}')

if __name__ == '__main__':
    main()