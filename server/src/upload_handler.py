import os
import socket
import threading
import time
import uuid
import config
import utils
import math
from models.message_structure import *

def recv_file_from_client(conn, partNum, partSize, temp_dir, file_id):
    temp_file_path = os.path.join(temp_dir, f"{file_id}_part_{partNum}")
    bytes_received = 0
    start_time = time.perf_counter()

    try:
        with open(temp_file_path, 'wb') as temp_file:
            while bytes_received < partSize:
                remaining = partSize - bytes_received
                chunk = conn.recv(min(remaining, config.BUFFER_SIZE))
                if not chunk:
                    break
                temp_file.write(chunk)
                bytes_received += len(chunk)
                
                elapsed_time = time.perf_counter() - start_time
                if elapsed_time > 0:
                    speed = bytes_received / elapsed_time
                    remaining_size = partSize - bytes_received
                    dynamic_timeout = max(config.MIN_TIMEOUT, min(config.MAX_TIMEOUT, remaining_size / speed * 1.5))
                    conn.settimeout(dynamic_timeout)
    except socket.timeout:
        print(f'Timeout receiving file part {partNum}')
    except Exception as e:
        print(f'Error receiving file part {partNum}: {e}')

    return temp_file_path if bytes_received == partSize else None

def handle_thread(conn, addr, partNum, partSize, dataList, temp_dir, file_id, lock):
    try:
        temp_file_path = recv_file_from_client(conn, partNum, partSize, temp_dir, file_id)
        with lock:
            if dataList[partNum] is None:
                dataList[partNum] = temp_file_path
                print(f'Part {partNum} received from {addr}.')
            else:
                print(f'Duplicate part {partNum} received from {addr}. Ignoring.')
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
    finally:
        conn.close()

def upload_file(conn, addr, payload):
    fileName, fileSize = payload.decode().split(',')
    fileSize = int(fileSize)
    
    if not os.path.exists(config.SERVER_DATA_PATH):
        os.makedirs(config.SERVER_DATA_PATH)
    filePath = os.path.join(config.SERVER_DATA_PATH, fileName)
    
    partSize = math.ceil(fileSize / config.NUMBER_OF_PARTS)
    send_upload_response(conn, partSize)

    file_id = str(uuid.uuid4())
    temp_dir = os.path.join(config.SERVER_DATA_PATH, 'Uploading', file_id)
    utils.ensure_dir(temp_dir)

    dataList = [None] * config.NUMBER_OF_PARTS
    lock = threading.Lock()

    threads = []
    for i in range(config.NUMBER_OF_PARTS):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as uploadSocket:
            uploadSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            uploadSocket.bind((config.HOST, 0))
            port = uploadSocket.getsockname()[1]
            uploadSocket.listen(1)

            send_message(conn, OpCode.UPLOAD_PART_PORT, struct.pack('!I', port))

            client_conn, client_addr = uploadSocket.accept()
            thread = threading.Thread(target=handle_thread, args=(client_conn, client_addr, i, partSize, dataList, temp_dir, file_id, lock))
            thread.start()
            threads.append(thread)
    
    for thread in threads:
        thread.join()

    try:
        with open(filePath, 'wb') as output_file:
            for temp_file_path in dataList:
                if temp_file_path is not None and os.path.exists(temp_file_path):
                    with open(temp_file_path, 'rb') as temp_file:
                        output_file.write(temp_file.read())

        # Clean up temporary files and directories
        utils.clean_temp_files(temp_dir)
        utils.clean_temp_files(os.path.dirname(temp_dir))  # Clean up the 'Uploading' directory
    except Exception as e:
        print(f"Error during file assembly or cleanup: {e}")
    
    # Calculate and send MD5 hash of the received file
    file_md5 = utils.calculate_md5(filePath)
    send_message(conn, OpCode.FILE_MD5, file_md5.encode())
    print(f'{fileName} uploaded successfully from {addr}. MD5: {file_md5}')