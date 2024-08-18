import os
import socket
import threading
import sys
import time
import uuid
from collections import deque
from list_files import recv_list_from_server
from config import *
from utils import *
from models.message_structure import *

def recv_file_from_server(conn: socket.socket, partNum, partSize, totalSize, progress_dict, temp_dir, file_id, is_last_part):
    temp_file_path = os.path.join(temp_dir, f"{file_id}_part_{partNum}")
    bytes_received = 0
    speed_queue = deque(maxlen=5)
    start_time = time.perf_counter()

    try:
        with open(temp_file_path, 'wb') as temp_file:
            while bytes_received < partSize:
                chunk_size = min(partSize - bytes_received, BUFFER_SIZE)
                chunk = conn.recv(chunk_size)
                
                if not chunk:
                    break

                temp_file.write(chunk)
                bytes_received += len(chunk)
                chunk_time = time.perf_counter() - start_time
                if chunk_time > 0:
                    chunk_speed = len(chunk) / chunk_time
                    speed_queue.append(chunk_speed)

                update_download_progress(partNum, bytes_received, totalSize, progress_dict)

                average_speed = sum(speed_queue) / len(speed_queue) if speed_queue else INITIAL_SPEED
                remaining_size = partSize - bytes_received
                dynamic_timeout = max(MIN_TIMEOUT, min(MAX_TIMEOUT, remaining_size / average_speed * 1.5))
                conn.settimeout(dynamic_timeout)

                start_time = time.perf_counter()

        if bytes_received != partSize:
            if is_last_part:
                print(f'Last part {partNum} received {bytes_received} bytes, expected {partSize} bytes. Accepting as complete.', file=sys.stderr)
                return temp_file_path
            elif partSize - bytes_received <= 10:  # Allow small discrepancies for all parts
                print(f'Part {partNum} received {bytes_received} bytes, expected {partSize} bytes. Accepting as complete.', file=sys.stderr)
                return temp_file_path
            else:
                print(f'Incomplete part {partNum}: received {bytes_received} bytes, expected {partSize} bytes', file=sys.stderr)
                return None

    except Exception as e:
        print(f'Error receiving file part {partNum}: {e}', file=sys.stderr)
        return None

    return temp_file_path

def assemble_file(dataList, savePath, fileSize):
    with open(savePath, 'wb') as output_file:
        bytes_written = 0
        for i, temp_file_path in enumerate(dataList):
            if temp_file_path is not None and os.path.exists(temp_file_path):
                with open(temp_file_path, 'rb') as temp_file:
                    chunk = temp_file.read()
                    output_file.write(chunk)
                    bytes_written += len(chunk)
            else:
                print(f"Warning: Part {i} is missing or incomplete.", file=sys.stderr)

    size_difference = abs(bytes_written - fileSize)
    if size_difference > fileSize * 0.01:  # Allow up to 1% difference
        raise ValueError(f"Assembled file size ({bytes_written} bytes) does not match expected size ({fileSize} bytes). Difference: {size_difference} bytes")
    else:
        print(f"File assembled successfully. Size difference: {size_difference} bytes", file=sys.stderr)

def update_download_progress(partNum, bytes_received, totalSize, progress_dict):
    progress_dict[partNum] = bytes_received
    total_received = sum(progress_dict.values())
    progress_percentage = int((total_received / totalSize) * 100)
    print(progress_percentage, flush=True)

def handle_thread(server_addr, server_port, partSize, dataList, partNum, totalSize, progress_dict, temp_dir, file_id, is_last_part, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as downloadSocket:
                downloadSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                downloadSocket.connect((server_addr, server_port))
                
                op_code, payload = recv_message(downloadSocket)
                if op_code != OpCode.DOWNLOAD_PART_NUMBER:
                    raise ValueError("Unexpected message from server")
                
                part_num = struct.unpack('!I', payload)[0]
                temp_file_path = recv_file_from_server(downloadSocket, part_num, partSize, totalSize, progress_dict, temp_dir, file_id, is_last_part)
                
                if temp_file_path:
                    dataList[part_num] = temp_file_path
                    print(f'Part {part_num} received successfully.', file=sys.stderr)
                    return  # Success, exit the function
                else:
                    raise ValueError(f"Failed to receive part {part_num}")
        
        except (socket.error, ValueError) as e:
            retries += 1
            wait_time = 2 ** retries  # Exponential backoff
            print(f'Error during connection or receiving data for part {partNum}: {e}. Retrying in {wait_time} seconds. (Attempt {retries}/{max_retries})', file=sys.stderr)
            time.sleep(wait_time)
    
    print(f'Failed to download part {partNum} after {max_retries} attempts.', file=sys.stderr)
    
    print(f'Failed to download part {partNum} after {max_retries} attempts.', file=sys.stderr)

def download_file(clientSocket, fileName, fileList, savePath):
    fileIndex = next((i for i, file in enumerate(fileList) if file.name == fileName), -1)
    if fileIndex == -1:
        print(f'File {fileName} not found.', file=sys.stderr)
        return

    send_download_request(clientSocket, fileIndex)
    op_code, payload = recv_message(clientSocket)
    if op_code != OpCode.DOWNLOAD_RESPONSE:
        raise ValueError("Unexpected response from server")

    fileSize, partSize = struct.unpack('!QQ', payload)

    file_id = str(uuid.uuid4())
    temp_dir = os.path.join(DOWNLOADING_TEMP_PATH, file_id)
    ensure_dir(temp_dir)

    dataList = [None] * NUMBER_OF_PARTS
    progress_dict = {i: 0 for i in range(NUMBER_OF_PARTS)}
    server_ports = {}  # New dictionary to store server ports
    threads = []

    def download_part(i):
        nonlocal threads
        op_code, payload = recv_message(clientSocket)
        if op_code != OpCode.DOWNLOAD_PART_PORT:
            raise ValueError("Unexpected message from server")
        server_port = struct.unpack('!I', payload)[0]
        server_ports[i] = server_port 
        is_last_part = i == NUMBER_OF_PARTS - 1
        thread = threading.Thread(target=handle_thread, args=(HOST, server_port, partSize, dataList, i, fileSize, progress_dict, temp_dir, file_id, is_last_part))
        thread.start()
        threads.append(thread)

    for i in range(NUMBER_OF_PARTS):
        download_part(i)
        time.sleep(0.1)

    for thread in threads:
        thread.join()

    while True:
        op_code, payload = recv_message(clientSocket)
        if op_code == OpCode.DOWNLOAD_INCOMPLETE:
            missing_parts = list(map(int, payload.decode().split(',')))
            print(f"Download incomplete. Missing parts: {missing_parts}", file=sys.stderr)
            # Retry downloading missing parts
            threads = []
            for i in missing_parts:
                download_part(i)
            for thread in threads:
                thread.join()
        elif op_code == OpCode.ERROR:
            print(f"Error during download: {payload.decode()}", file=sys.stderr)
            return
        elif op_code == OpCode.FILE_MD5:
            break
        else:
            raise ValueError("Unexpected message from server")

    max_assembly_attempts = 3
    for attempt in range(max_assembly_attempts):
        try:
            assemble_file(dataList, savePath, fileSize)
            print(f'{fileName} downloaded and assembled successfully to {savePath}.', file=sys.stderr)
            break
        except ValueError as e:
            if attempt < max_assembly_attempts - 1:
                print(f"Assembly attempt {attempt + 1} failed: {e}. Retrying...", file=sys.stderr)
                # Retry downloading missing parts
                missing_parts = [i for i, part in enumerate(dataList) if part is None]
                threads = []
                for i in missing_parts:
                    thread = threading.Thread(target=handle_thread, args=(HOST, server_ports[i], partSize, dataList, i, fileSize, progress_dict, temp_dir, file_id, i == NUMBER_OF_PARTS - 1))
                    thread.start()
                    threads.append(thread)
                for thread in threads:
                    thread.join()
            else:
                print(f"Failed to assemble file after {max_assembly_attempts} attempts: {e}", file=sys.stderr)
                return


    # Clean up temporary files
    for temp_file_path in dataList:
        if temp_file_path is not None and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    os.rmdir(temp_dir)
    
    server_md5 = payload.decode()
    print(f'Server MD5 hash of {fileName}: {server_md5}', file=sys.stderr)
    
    local_md5 = calculate_md5(savePath)
    print(f'Local MD5 hash of {fileName}: {local_md5}', file=sys.stderr)
    
    if server_md5 == local_md5:
        print("MD5 hash verification successful.", file=sys.stderr)
    else:
        print("WARNING: MD5 hash verification failed!", file=sys.stderr)


def main():
    if len(sys.argv) != 3:
        print("Usage: python download_file.py <filename> <save_path>", file=sys.stderr)
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
        clientSocket.connect((HOST, SERVER_PORT))
        fileList = recv_list_from_server(clientSocket)
        download_file(clientSocket, sys.argv[1], fileList, sys.argv[2])
        # download_file(clientSocket, "input1.txt", fileList, "input1.txt")

if __name__ == '__main__':
    main()