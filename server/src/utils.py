import hashlib
import os

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def safe_remove(path):
    try:
        os.remove(path)
    except OSError as e:
        print(f"Error removing file {path}: {e}")

def safe_rmdir(path):
    try:
        os.rmdir(path)
    except OSError as e:
        print(f"Error removing directory {path}: {e}")

def clean_temp_files(temp_dir):
    for root, dirs, files in os.walk(temp_dir, topdown=False):
        for name in files:
            safe_remove(os.path.join(root, name))
        for name in dirs:
            safe_rmdir(os.path.join(root, name))
    safe_rmdir(temp_dir)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as input_file:
        for chunk in iter(lambda: input_file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()