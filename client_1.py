import socket
import pickle
import time
import argparse
from threading import Thread, Event

client_list = []
client_port = 5000
stop_event = Event()

# List of clients available
def list_clients():
    if all_connections and all_address:
        print("Connected Clients:")
        for i, addr in enumerate(all_address, start=1):
            print(f"{i}. IP: {addr[0]}, Port: {addr[1]}")
    else:
        print("No clients are currently connected.")    

# New connection for client
def client_program(server_host, server_port):
    print('Thread ID {:d} connecting to {}:{:d}'.format(server_host, server_port))
    client_socket = socket.socket()
    client_socket.bind(("0.0.0.0", client_port))
    client_socket.listen(10)
    print(f"Listening for peer connections on port {client_port}")
    
    while True:
        conn, addr = client_socket.accept()
        print(f"Connected by peer at {addr}")
        # threads = Thread(target=handle_peer, args=(conn, addr))
        # threads.start()

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
    client_ip_l, client_port_l = tracker_socket.getsockname()
    print(f"Client IP: {client_ip_l}, Client Port: {client_port_l}")

    # Receive the clients list from the Tracker
    client_list = tracker_socket.recv(4096)
    client_list = pickle.loads(client_list)
    
    return client_list

# Connect to other peers
def connect_to_peers(client_list):
    for peer_ip, peer_port in client_list:
        try:
            peer_socket = socket.socket()
            peer_socket.connect((peer_ip, peer_port))
            print(f"Connected to peer {peer_ip}:{peer_port}")

        except ConnectionRefusedError:
            print(f"Could not connect to peer {peer_ip}:{peer_port}")

# def client_program(threadnum, server_host, server_port):
#    # Create "threadnum" of Thread to parallelly connnect
#    threads = [Thread(target=new_connection, args=(i, server_host, server_port)) for i in range(0,threadnum)]
#    [t.start() for t in threads]
#    # TODO: wait for all threads to finish
#    [t.join() for t in threads]

def client_terminal():
    print("Client Terminal started.")
    while True:
        command = input("> ")
        if command == "test":
            print("The program is running normally.")
        elif command.startswith("connect_tracker"):
            parts = command.split()
            if len(parts) == 3:
                server_host = parts[1]
                try:
                    server_port = int(parts[2])
                    connect_to_tracker(server_host, server_port)
                except ValueError:
                    print("Invalid port.")
            else:
                print("Usage: connect_tracker <IP> <Port>")
        elif command == "exit":
            print("Exiting Tracker Terminal.")
            stop_event.set()
            break

if __name__ == "__main__":
    # python3 client_1.py --server-ip 192.168.1.14 --server-port 22236 --client-num 1
    # parser = argparse.ArgumentParser(
    #                    prog='Client',
    #                    description='Connect to pre-declard server',
    #                    epilog='!!!It requires the server is running and listening!!!')
    # parser.add_argument('--server-ip')
    # parser.add_argument('--server-port', type=int)
    # parser.add_argument('--client-num', type=int)
    # args = parser.parse_args()
    # server_host = args.server_ip
    # server_port = args.server_port
    # cnum = args.client_num

    # thread_1 = Thread(target=client_program, args=(server_host, server_port))
    # thread_1.start()

    try:
        client_terminal()
    except KeyboardInterrupt:
        stop_event.set()
