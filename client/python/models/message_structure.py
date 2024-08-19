# message_structure.py

import struct
from enum import IntEnum

class OpCode(IntEnum):
    FILE_LIST_REQUEST = 1
    FILE_LIST_RESPONSE = 2
    DOWNLOAD_REQUEST = 3
    DOWNLOAD_RESPONSE = 4
    DOWNLOAD_PART_PORT = 5
    DOWNLOAD_PART_NUMBER = 6
    DOWNLOAD_INCOMPLETE = 7
    UPLOAD_REQUEST = 8
    UPLOAD_RESPONSE = 9
    UPLOAD_PART_PORT = 10
    UPLOAD_PART_NUMBER = 11
    UPLOAD_INCOMPLETE = 12
    FILE_MD5 = 13
    ERROR = 14

class MessageHeader:
    def __init__(self, op_code, payload_length):
        self.op_code = op_code
        self.payload_length = payload_length

    def pack(self):
        return struct.pack('!BI', self.op_code, self.payload_length)

    @classmethod
    def unpack(cls, data):
        op_code, payload_length = struct.unpack('!BI', data)
        return cls(OpCode(op_code), payload_length)

def send_message(conn, op_code, payload):
    header = MessageHeader(op_code, len(payload))
    conn.sendall(header.pack() + payload)

def recv_message(conn):
    header_data = recv_all(conn, 5) 
    if not header_data:
        return None, None
    header = MessageHeader.unpack(header_data)
    payload = recv_all(conn, header.payload_length)
    return header.op_code, payload

def recv_all(conn, n):
    data = bytearray()
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def send_file_list_request(conn):
    send_message(conn, OpCode.FILE_LIST_REQUEST, b'')

def send_file_list_response(conn, file_list):
    payload = '\n'.join(f"{f.name},{f.size},{f.last_modified.isoformat()}" for f in file_list).encode()
    send_message(conn, OpCode.FILE_LIST_RESPONSE, payload)

def send_download_request(conn, file_index):
    payload = struct.pack('!I', file_index)
    send_message(conn, OpCode.DOWNLOAD_REQUEST, payload)

def send_download_response(conn, file_size, part_size):
    payload = struct.pack('!QQ', file_size, part_size)
    send_message(conn, OpCode.DOWNLOAD_RESPONSE, payload)

def send_upload_request(conn, file_name, file_size):
    payload = f"{file_name},{file_size}".encode()
    send_message(conn, OpCode.UPLOAD_REQUEST, payload)

def send_upload_response(conn, part_size):
    payload = struct.pack('!Q', part_size)
    send_message(conn, OpCode.UPLOAD_RESPONSE, payload)

def send_error(conn, error_message):
    send_message(conn, OpCode.ERROR, error_message.encode())