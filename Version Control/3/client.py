import socket
import pickle
import time
import sys
import argparse
from threading import Thread, Event

client_conn_list = [] # Tracker's Client conn List
client_addr_list = [] # Current clients connected to Tracker
connected_client_conn_list = [] # Current clients conn connected to this client
connected_client_addr_list = [] # Current clients addr connected to this client
stop_event = Event()
nconn_threads = []

# List of clients connected to Tracker
def list_clients():
    if client_addr_list:
        print("Connected Clients:")
        for i, client in enumerate(client_addr_list, start=1):
            print(f"{i}. IP: {client[0]}, Port: {client[1]}")
    else:
        print("No clients are currently connected.") 

# List of clients connected to this client
def list_connected_clients():
    if connected_client_addr_list:
        print("Connected Clients:")
        for i, client in enumerate(connected_client_addr_list, start=1):
            print(f"{i}. IP: {client[0]}, Port: {client[1]}")
    else:
        print("No clients are currently connected.") 


# New connection for newly connected client
def new_connection(conn, addr):
    conn.settimeout(1) # Setting timeout to check the stop_event
    
    # Record the new client's metainfo
    connected_client_conn_list.append(conn)
    connected_client_addr_list.append(addr)


    print(f"Client {addr} connected.")

    while not stop_event.is_set():
        try:
            data = conn.recv(1024)
            command = data.decode("utf-8")
            if not data:
                break
            #TODO: process at client side
        except socket.timeout:
            continue
        except Exception:
            print("Error occured!")
            break

    conn.close()
    connected_client_conn_list.remove(conn)
    connected_client_addr_list.remove(addr)
    print(f"Client {addr} removed.")

# New connection for client
def client_program(client_ip, client_port):
    print(f"Client IP: {client_ip} | Client Port: {client_port}")
    print("Listening on: {}:{}".format(client_ip, client_port))
    client_socket = socket.socket()
    client_socket.settimeout(1) # Setting timeout to check the stop_event

    client_socket.bind((client_ip, client_port))
    client_socket.listen(10)

    while not stop_event.is_set():
        try:
            conn, addr = client_socket.accept()
            nconn = Thread(target=new_connection, args=(conn, addr))
            nconn.start()
            nconn_threads.append(nconn)
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Client error: {e}")
            break
    
    client_socket.close()
    print(f"Client {client_ip} stopped.")


def update_client_list(tracker_socket):
    # Create command for the Tracker
    command = "update_client_list"
    tracker_socket.send(command.encode("utf-8"))
    print("Client List requested.")

    # Receive the clients list from the Tracker
    pickle_client_addr_list = tracker_socket.recv(4096)
    client_addr_list = pickle.loads(pickle_client_addr_list)
    print("Client List received.")

    return client_addr_list, tracker_socket

# Connect to the Tracker
def connect_to_tracker(server_host, server_port):
    tracker_socket = socket.socket()
    tracker_socket.settimeout(5) # Setting timeout to check the stop_event
    tracker_socket.connect((server_host, server_port))
    print(f"Tracker ('{server_host}', {server_port}) connected.")

    return update_client_list(tracker_socket)

# Connect to other peers
def connect_to_all_peers():
    for client in client_addr_list:
        try:
            if client[0] == get_host_default_interface_ip():
                continue
            peer_socket = socket.socket()
            peer_socket.connect((client[0], client_port))
            print(f"Connected to peer {client[0]}:{client_port}")
        except ConnectionRefusedError:
            print(f"Could not connect to peer {client[0]}:{client_port}")

# Connect to one specific peer
def connect_to_peer(peer_ip, peer_port):
    if peer_ip == get_host_default_interface_ip():
        print("Cannot connect to self.")
        return
    peer_socket = socket.socket()
    peer_socket.connect((peer_ip, peer_port))
    print(f"Connected to peer {peer_ip}:{peer_port}")

# Disconnect to other peers
def disconnect_to_all_peers():
    for conn, addr in zip(connected_client_conn_list, connected_client_addr_list):
        try:
            conn.close()  # Close the connection to the peer
            print(f"Disconnected from peer {addr}")
        except Exception as e:
            print(f"Error disconnecting from peer {addr}: {e}")
    
    # Clear the client_list after closing all connections
    connected_client_conn_list.clear()
    connected_client_addr_list.clear()
    print("All peers disconnected.")

# Get client IP
def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Not for communication with clients but simply to discover the server’s outward-facing IP address.
    try:
       s.connect(('8.8.8.8',1))
       ip = s.getsockname()[0]
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip

def shutdown_client():
    stop_event.set()
    for nconn in nconn_threads:
        nconn.join()
    print("All threads have been closed.")

def client_terminal():
    global client_addr_list
    print("Client Terminal started.")
    try:
        while True:
            command = input("Peer> ")
            if command == "test":
                print("The program is running normally.")
            elif command.startswith("connect_tracker"):
                parts = command.split()
                if len(parts) == 3:
                    server_host = parts[1]
                    try:
                        server_port = int(parts[2])
                        client_addr_list, tracker_socket = connect_to_tracker(server_host, server_port)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: connect_tracker <IP> <Port>")
            elif command == "list_clients":
                list_clients()
            elif command == "list_connected_clients":
                list_connected_clients()
            elif command == "connect_to_all_peers":
                connect_to_all_peers()    
            elif command.startswith("connect_to_peer"):
                parts = command.split()
                if len(parts) == 3:
                    peer_ip = parts[1]
                    try:
                        peer_port = int(parts[2])
                        connect_to_peer(peer_ip, peer_port)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: connect_to_peer <IP> <Port>")
            elif command == "disconnect_to_all_peers":
                disconnect_to_all_peers()  
            elif command == "exit":
                print("Exiting Tracker Terminal.")
                break
            else:
                print("Unknown Command.")
    except KeyboardInterrupt:
        print("\nThe Client Terminal interrupted by user. Exiting Client Terminal...")
    finally:
        print("Client Terminal exited.")

if __name__ == "__main__":
    client_ip = get_host_default_interface_ip()
    client_port = 5000

    # Start client
    thread_client = Thread(target=client_program, args=(client_ip, client_port))
    thread_client.start()

    # Start terminal
    client_terminal()

    shutdown_client()
    thread_client.join()

    sys.exit(0)

