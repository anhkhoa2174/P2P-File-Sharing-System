import socket
from threading import Thread, Event
import hashlib

PIECE_LENGTH = 512 * 1024
BLOCK_LENGTH = 1024 * 4
client_addr_list = [] # Current clients connected to Tracker
CODE = 'utf-8'

def split_into_pieces(file_path, piece_length):
#    """Split the file into pieces of the given length and return a list of pieces."""
    pieces = []
    with open(file_path, 'rb') as f:
        while True:
            piece = f.read(piece_length)
            if not piece:
                break
            pieces.append(piece)
    return pieces

def sha1_hash(piece):
#   """Compute SHA-1 hash of a piece."""
    sha1 = hashlib.sha1()
    sha1.update(piece)
    return sha1.digest()

def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

