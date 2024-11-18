import socket
import pickle
import time
import argparse
from threading import Thread

client_port = 5000

def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Not for communication with clients but simply to discover the server’s outward-facing IP address.
    try:
       s.connect(('8.8.8.8',1))
       ip = s.getsockname()[0]
       print(ip)
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip

def start_listener():
    client_ip = get_host_default_interface_ip()
    client_socket = socket.socket()
    client_socket.bind((client_ip, client_port))
    client_socket.listen(10)
    print(f"Listening for peer connections on port {client_port}")
    
    while True:
        conn, addr = client_socket.accept()
        print(f"Connected by peer at {addr}")
        # threads = Thread(target=handle_peer, args=(conn, addr))
        # threads.start()

def new_connection(tid, server_host, server_port):
    print('Thread ID {:d} connecting to {}:{:d}'.format(tid, server_host, server_port))
    thread = Thread(target=start_listener)
    thread.start()

    client_list = connect_to_tracker(server_host, server_port)
    if not client_list:
        print("No other clients are currently connected.")
    else:
        print("List of connected clients:\n", client_list)    
        connect_to_peers(client_list)

    # Demo sleep time for fun (dummy command)
    for i in range(0,3):
        print('Let me, ID={:d} sleep in {:d}s'.format(tid,3-i))
        time.sleep(1)
 
    print('OK! I am ID={:d} done here'.format(tid))

# Connect to the Tracker
def connect_to_tracker(server_host, server_port):
    tracker_socket = socket.socket()
    tracker_socket.connect((server_host, server_port))

    # Client metainfo
    client_ip, client_port = tracker_socket.getsockname()
    print(f"Client IP: {client_ip}, Client Port: {client_port}")

    # Receive the clients list from the Tracker
    pickle_client_list = tracker_socket.recv(4096)
    client_list = pickle.loads(pickle_client_list)
    
    return client_list

# Connect to other peers
def connect_to_peers(client_list):
    for peer_ip, peer_port in client_list:
        try:
            peer_socket = socket.socket()
            peer_socket.connect((peer_ip, client_port))
            print(f"Connected to peer {peer_ip}:{client_port}")

        except ConnectionRefusedError:
            print(f"Could not connect to peer {peer_ip}:{client_port}")

def connect_server(threadnum, server_host, server_port):
    # Create "threadnum" of Thread to parallelly connnect
    threads = [Thread(target=new_connection, args=(i, server_host, server_port)) for i in range(0,threadnum)]
    [t.start() for t in threads]
    # TODO: wait for all threads to finish
    [t.join() for t in threads]

if __name__ == "__main__":
    # python3 client_1.py --server-ip 192.168.1.7 --server-port 22236 --client-num 1
    parser = argparse.ArgumentParser(
                        prog='Client',
                        description='Connect to pre-declard server',
                        epilog='!!!It requires the server is running and listening!!!')
    parser.add_argument('--server-ip')
    parser.add_argument('--server-port', type=int)
    parser.add_argument('--client-num', type=int)
    args = parser.parse_args()
    server_host = args.server_ip
    server_port = args.server_port
    cnum = args.client_num
    connect_server(cnum, server_host, server_port)
