import socket
from threading import Thread, Event

PIECE_LENGTH = 512 * 1024
client_addr_list = [] # Current clients connected to Tracker
CODE = 'utf-8'
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

