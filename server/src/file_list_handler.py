import config
from models.message_structure import *
from models.file_info import FileInfo

def send_file_list(conn):
    try:
        fileList = FileInfo.list_from_directory(config.SERVER_DATA_PATH)
        send_file_list_response(conn, fileList)
    except Exception as e:
        send_error(conn, f'Error sending file list: {e}')