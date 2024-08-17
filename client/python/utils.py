import hashlib
import os
from datetime import datetime, timezone, timedelta

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as input_file:
        for chunk in iter(lambda: input_file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
