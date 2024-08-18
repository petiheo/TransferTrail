import os
import socket
import threading
import math
import time
import utils
import config
from collections import deque
from models.file_info import FileInfo
from models.message_structure import *

def send_file_to_client(conn, client_addr, filePath, partNum, startByte, endByte, lock, is_last_part, completed_parts, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as downloadSocket:
                downloadSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                downloadSocket.bind(('', 0))
                port = downloadSocket.getsockname()[1]
                downloadSocket.listen(1)

                send_message(conn, OpCode.DOWNLOAD_PART_PORT, struct.pack('!I', port))
                client_socket, _ = downloadSocket.accept()

                with client_socket:
                    partSize = endByte - startByte + 1
                    with open(filePath, "rb") as input_file:
                        input_file.seek(startByte)
                        send_message(client_socket, OpCode.DOWNLOAD_PART_NUMBER, struct.pack('!I', partNum))
                        bytes_sent = 0
                        speed_queue = deque(maxlen=5)

                        while partSize > 0:
                            chunk = input_file.read(min(partSize, config.BUFFER_SIZE))
                            if not chunk:
                                break
                            chunk_start_time = time.time()
                            client_socket.sendall(chunk)
                            chunk_end_time = time.time()
                            
                            chunk_size = len(chunk)
                            chunk_time = chunk_end_time - chunk_start_time
                            if chunk_time > 0:
                                chunk_speed = chunk_size / chunk_time
                                speed_queue.append(chunk_speed)
                            
                            bytes_sent += chunk_size
                            partSize -= chunk_size
                        
                            average_speed = sum(speed_queue) / len(speed_queue) if speed_queue else config.INITIAL_SPEED
                            remaining_size = endByte - startByte + 1 - bytes_sent
                            dynamic_timeout = max(config.MIN_TIMEOUT, min(config.MAX_TIMEOUT, remaining_size / average_speed * 1.5))
                            client_socket.settimeout(dynamic_timeout)

                    if bytes_sent != (endByte - startByte + 1):
                        if is_last_part and (endByte - startByte + 1 - bytes_sent) <= 10:  # Allow up to 10 bytes difference for the last part
                            print(f"Last part {partNum} sent {bytes_sent} bytes, expected {endByte - startByte + 1} bytes. Accepting as complete.")
                        else:
                            raise ValueError(f"Incomplete send for part {partNum}: sent {bytes_sent} bytes, expected {endByte - startByte + 1} bytes")

                    with lock:
                        completed_parts.add(partNum)
                        print(f"Part {partNum} has been sent to {client_addr}.")
                    return True  # Successfully sent the part
        except socket.timeout:
            retries += 1
            print(f'Timeout sending file part {partNum} to {client_addr}. Retry {retries}/{max_retries}')
        except Exception as e:
            retries += 1
            print(f'Error sending file part {partNum} to {client_addr}: {e}. Retry {retries}/{max_retries}')
        
        if retries < max_retries:
            time.sleep(1)  # Wait for a second before retrying

    print(f'Failed to send part {partNum} to {client_addr} after {max_retries} attempts.')
    return False

def download_file(conn, addr, payload):
    fileList = FileInfo.list_from_directory(config.SERVER_DATA_PATH)
    fileIndex = struct.unpack('!I', payload)[0]
    filePath = os.path.join(config.SERVER_DATA_PATH, fileList[fileIndex].name)
    fileSize = os.path.getsize(filePath)

    partSize = math.ceil(fileSize / config.NUMBER_OF_PARTS)
    
    send_download_response(conn, fileSize, partSize)

    threads = []
    lock = threading.Lock()
    completed_parts = set()

    for i in range(config.NUMBER_OF_PARTS):
        startByte = i * partSize
        endByte = min(startByte + partSize - 1, fileSize - 1)
        is_last_part = i == config.NUMBER_OF_PARTS - 1
        thread = threading.Thread(target=send_file_to_client, 
                                  args=(conn, addr, filePath, i, startByte, endByte, lock, is_last_part, completed_parts))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Verify all parts have been sent
    missing_parts = set(range(config.NUMBER_OF_PARTS)) - completed_parts
    if missing_parts:
        print(f"Missing parts: {missing_parts}")
        send_message(conn, OpCode.DOWNLOAD_INCOMPLETE, ','.join(map(str, missing_parts)).encode())
        return

    # Calculate and send MD5 hash of the file
    file_md5 = utils.calculate_md5(filePath)
    send_message(conn, OpCode.FILE_MD5, file_md5.encode())
    print(f"File {fileList[fileIndex].name} sent to {addr}. MD5: {file_md5}")