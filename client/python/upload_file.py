import socket
import threading
import os
import sys
import time
from collections import deque
from config import *
from utils import *
from models.message_structure import *

def update_upload_progress(partNum, bytes_sent, totalSize, progress_dict):
    progress_dict[partNum] = bytes_sent
    total_sent = sum(progress_dict.values())
    progress_percentage = int((total_sent / totalSize) * 100)
    print(progress_percentage, flush=True)

def send_file_to_server(filePath, partNum, startByte, endByte, server_addr, server_port, totalSize, progress_dict, is_last_part):
    for attempt in range(RETRY_LIMIT):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client2:
            try:
                client2.settimeout(MAX_TIMEOUT)
                client2.connect((server_addr, server_port))
                
                partSize = endByte - startByte + 1
                bytes_sent = 0
                speed_queue = deque(maxlen=5)

                with open(filePath, "rb") as input_file:
                    input_file.seek(startByte)
                    while bytes_sent < partSize:
                        chunk = input_file.read(min(partSize - bytes_sent, BUFFER_SIZE))
                        if not chunk:
                            break
                        
                        chunk_start_time = time.perf_counter()
                        client2.sendall(chunk)
                        chunk_end_time = time.perf_counter()
                        
                        chunk_size = len(chunk)
                        chunk_time = chunk_end_time - chunk_start_time
                        if chunk_time > 0:
                            chunk_speed = chunk_size / chunk_time
                            speed_queue.append(chunk_speed)
                        
                        bytes_sent += chunk_size
                        
                        average_speed = sum(speed_queue) / len(speed_queue) if speed_queue else INITIAL_SPEED
                        remaining_size = partSize - bytes_sent
                        dynamic_timeout = max(MIN_TIMEOUT, min(MAX_TIMEOUT, remaining_size / average_speed * 1.5))
                        client2.settimeout(dynamic_timeout)

                        update_upload_progress(partNum, bytes_sent, totalSize, progress_dict)

                if bytes_sent != partSize:
                    if is_last_part and (partSize - bytes_sent) <= 10:  # Allow up to 10 bytes difference for the last part
                        print(f'Last part {partNum} sent {bytes_sent} bytes, expected {partSize} bytes. Accepting as complete.', file=sys.stderr)
                        return True
                    raise ValueError(f"Incomplete send for part {partNum}: sent {bytes_sent} bytes, expected {partSize} bytes")

                print(f'Part {partNum} has been sent to server.', file=sys.stderr)
                return True
            except socket.timeout:
                print(f'Timeout sending file part {partNum}, attempt {attempt + 1}', file=sys.stderr)
            except Exception as e:
                print(f'Error sending file part {partNum}, attempt {attempt + 1}: {e}.', file=sys.stderr)

    print(f'Failed to send part {partNum} after {RETRY_LIMIT} attempts.', file=sys.stderr)
    return False

def upload_file(client, filePath):
    fileName = os.path.basename(filePath)
    fileSize = os.path.getsize(filePath)
    send_upload_request(client, fileName, fileSize)

    op_code, payload = recv_message(client)
    if op_code != OpCode.UPLOAD_RESPONSE:
        raise ValueError("Unexpected response from server")

    partSize = struct.unpack('!Q', payload)[0]

    progress_dict = {i: 0 for i in range(NUMBER_OF_PARTS)}
    threads = []

    def upload_part(i):
        nonlocal threads
        op_code, payload = recv_message(client)
        if op_code != OpCode.UPLOAD_PART_PORT:
            raise ValueError("Unexpected message from server")
        server_port = struct.unpack('!I', payload)[0]
        
        startByte = i * partSize
        endByte = min(startByte + partSize - 1, fileSize - 1)
        is_last_part = i == NUMBER_OF_PARTS - 1
        thread = threading.Thread(target=send_file_to_server, args=(filePath, i, startByte, endByte, HOST, server_port, fileSize, progress_dict, is_last_part))
        thread.start()
        threads.append(thread)

    for i in range(NUMBER_OF_PARTS):
        upload_part(i)
        time.sleep(0.1)

    for thread in threads:
        thread.join()

    while True:
        # Wait for server response
        op_code, payload = recv_message(client)
        if op_code == OpCode.UPLOAD_INCOMPLETE:
            missing_parts = list(map(int, payload.decode().split(',')))
            print(f"Upload incomplete. Missing parts: {missing_parts}", file=sys.stderr)
            # Retry sending missing parts
            threads = []
            for i in missing_parts:
                upload_part(i)
            for thread in threads:
                thread.join()
        elif op_code == OpCode.ERROR:
            print(f"Error during upload: {payload.decode()}", file=sys.stderr)
            return
        elif op_code == OpCode.FILE_MD5:
            break
        else:
            raise ValueError("Unexpected message from server")

    server_md5 = payload.decode()
    print(f'Server MD5 hash of {fileName}: {server_md5}', file=sys.stderr)
    
    local_md5 = calculate_md5(filePath)
    print(f'Local MD5 hash of {fileName}: {local_md5}', file=sys.stderr)
    
    if server_md5 == local_md5:
        print(f"{fileName} uploaded successfully. MD5 hash verification successful.", file=sys.stderr)
    else:
        print(f"WARNING: MD5 hash verification failed for {fileName}!", file=sys.stderr)

def main():
    if len(sys.argv) != 2:
        print("Usage: python upload_file.py <file_path>", file=sys.stderr)
        sys.exit(1)

    filePath = sys.argv[1]
    if not os.path.exists(filePath):
        print(f"Error: File '{filePath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, SERVER_PORT))
        upload_file(client, filePath)
        # upload_file(client, "index.html")

if __name__ == '__main__':
    main()