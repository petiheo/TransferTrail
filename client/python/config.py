import os
import json

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r') as input_file:
        return json.load(input_file)

config = load_config()

# Network settings
HOST = config['host']
SERVER_PORT = config['serverPort']
BUFFER_SIZE = config['bufferSize']

# Protocol settings
FORMAT = config['format']
NUMBER_OF_PARTS = config['numberOfParts']

# Timeout settings
RETRY_LIMIT = config['retryLimit']
MIN_TIMEOUT = config['minTimeout']
MAX_TIMEOUT = config['maxTimeout']

# Performance settings
INITIAL_SPEED = config['initialSpeed'] # 1 MB/s, can be adjusted based on network speed estimate

# Temporary folder paths
CLIENT_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data')
DOWNLOADING_TEMP_PATH = os.path.join(CLIENT_DATA_PATH, 'Downloading')

# Ensure temporary directories exist
os.makedirs(DOWNLOADING_TEMP_PATH, exist_ok=True)