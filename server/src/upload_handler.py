import os
import socket
import threading
import time
import uuid
import config
import utils
import math
from models.message_structure import *

def recv_file_from_client(conn, partNum, partSize, temp_dir, file_id, is_last_part):
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

    if bytes_received != partSize:
        if is_last_part:
            print(f'Last part {partNum} received {bytes_received} bytes, expected {partSize} bytes. Accepting as complete.')
            return temp_file_path
        elif partSize - bytes_received <= 10:  # Allow small discrepancies for all parts
            print(f'Part {partNum} received {bytes_received} bytes, expected {partSize} bytes. Accepting as complete.')
            return temp_file_path
        else:
            print(f'Incomplete part {partNum}: received {bytes_received} bytes, expected {partSize} bytes')
            return None
    return temp_file_path


def handle_thread(conn, addr, partNum, partSize, dataList, temp_dir, file_id, lock, completed_parts, total_parts):
    is_last_part = partNum == total_parts - 1
    try:
        temp_file_path = recv_file_from_client(conn, partNum, partSize, temp_dir, file_id, is_last_part)
        with lock:
            if temp_file_path:
                dataList[partNum] = temp_file_path
                completed_parts.add(partNum)
                print(f'Part {partNum} received from {addr}.')
            else:
                print(f'Failed to receive part {partNum} from {addr}.')
    finally:
        conn.close()

def assemble_file(dataList, filePath, fileSize):
    with open(filePath, 'wb') as output_file:
        bytes_written = 0
        for i, temp_file_path in enumerate(dataList):
            if temp_file_path is not None and os.path.exists(temp_file_path):
                with open(temp_file_path, 'rb') as temp_file:
                    chunk = temp_file.read()
                    output_file.write(chunk)
                    bytes_written += len(chunk)
            else:
                print(f"Warning: Part {i} is missing or incomplete.")

    size_difference = abs(bytes_written - fileSize)
    if size_difference > fileSize * 0.01:  # Allow up to 1% difference
        raise ValueError(f"Assembled file size ({bytes_written} bytes) does not match expected size ({fileSize} bytes). Difference: {size_difference} bytes")
    else:
        print(f"File assembled successfully. Size difference: {size_difference} bytes")

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
    completed_parts = set()

    threads = []
    for i in range(config.NUMBER_OF_PARTS):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as uploadSocket:
            uploadSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            uploadSocket.bind((config.HOST, 0))
            port = uploadSocket.getsockname()[1]
            uploadSocket.listen(1)

            send_message(conn, OpCode.UPLOAD_PART_PORT, struct.pack('!I', port))

            client_conn, client_addr = uploadSocket.accept()
            thread = threading.Thread(target=handle_thread, args=(client_conn, client_addr, i, partSize, dataList, temp_dir, file_id, lock, completed_parts, config.NUMBER_OF_PARTS))
            thread.start()
            threads.append(thread)
    
    for thread in threads:
        thread.join()

    # Verify all parts have been received
    missing_parts = set(range(config.NUMBER_OF_PARTS)) - completed_parts
    if missing_parts:
        print(f"Missing parts: {missing_parts}")
        send_message(conn, OpCode.UPLOAD_INCOMPLETE, ','.join(map(str, missing_parts)).encode())
        return

    max_assembly_attempts = 3
    for attempt in range(max_assembly_attempts):
        try:
            assemble_file(dataList, filePath, fileSize)
            print(f'{fileName} uploaded and assembled successfully from {addr}.')
            break
        except ValueError as e:
            if attempt < max_assembly_attempts - 1:
                print(f"Assembly attempt {attempt + 1} failed: {e}. Retrying...")
                # Retry receiving missing parts
                missing_parts = [i for i, part in enumerate(dataList) if part is None]
                threads = []
                for i in missing_parts:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as uploadSocket:
                        uploadSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        uploadSocket.bind((config.HOST, 0))
                        port = uploadSocket.getsockname()[1]
                        uploadSocket.listen(1)

                        send_message(conn, OpCode.UPLOAD_PART_PORT, struct.pack('!I', port))

                        client_conn, client_addr = uploadSocket.accept()
                        thread = threading.Thread(target=handle_thread, args=(client_conn, client_addr, i, partSize, dataList, temp_dir, file_id, lock, completed_parts, config.NUMBER_OF_PARTS))
                        thread.start()
                        threads.append(thread)
                for thread in threads:
                    thread.join()
            else:
                print(f"Failed to assemble file after {max_assembly_attempts} attempts: {e}")
                send_message(conn, OpCode.ERROR, str(e).encode())
                return

    try:
        # Clean up temporary files
        for temp_file_path in dataList:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        os.rmdir(temp_dir)
        print(f"Temporary directory {temp_dir} removed successfully.")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    # Calculate and send MD5 hash of the received file
    file_md5 = utils.calculate_md5(filePath)
    send_message(conn, OpCode.FILE_MD5, file_md5.encode())
    print(f'{fileName} uploaded successfully from {addr}. MD5: {file_md5}')