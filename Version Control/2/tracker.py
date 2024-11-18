import socket
import pickle
import sys
import time
from threading import Thread, Event

client_list = [] # Tracker's Client List
stop_event = Event()
nconn_threads = []

# List of clients available
def list_clients():
    if client_list:
        print("Connected Clients:")
        for i, client in enumerate(client_list, start=1):
            print(f"{i}. IP: {client[0]}, Port: {client[1]}")
    else:
        print("No clients are currently connected.")

# Send the list of clients available to the newly connected client
def update_client_list(conn):
    print(client_list)
    print("Client List being sent...")
    pickle_client_list = pickle.dumps(client_list)
    conn.send(pickle_client_list)
    print("Client List sent.")

# New connection for newly connected client
def new_connection(conn, addr):
    conn.settimeout(1) # Setting timeout to check the stop_event
    
    # Record the new client's metainfo
    client_list.append(addr)

    print(f"Client {addr} added.")

    while not stop_event.is_set():
        try:
            data = conn.recv(1024)
            command = data.decode("utf-8")
            if not data:
                break
            elif command == "update_client_list":
                update_client_list(conn)
            elif command == "disconnect":
                break
            #TODO: process at tracker side
        except socket.timeout:
            continue
        except Exception:
            print("Error occured!")
            break

    conn.close()
    client_list.remove(addr)
    print(f"Client {addr} removed.")

def server_program(hostip, port):
    print(f"Tracker IP: {hostip} | Tracker Port: {port}")
    print("Listening on: {}:{}".format(hostip,port))
    serversocket = socket.socket()
    serversocket.settimeout(1) # Setting timeout to check the stop_event

    serversocket.bind((hostip, port))
    serversocket.listen(10)

    while not stop_event.is_set():
        try:
            conn, addr = serversocket.accept()
            nconn = Thread(target=new_connection, args=(conn, addr))
            nconn.start()
            nconn_threads.append(nconn)
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Server error: {e}")
            break
    
    serversocket.close()
    print("Tracker server stopped.")

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

def shutdown_server():
    stop_event.set()
    for nconn in nconn_threads:
        nconn.join()
    print("All threads have been closed.")

def tracker_terminal():
    print("Tracker Terminal started.") 
    try:
        while True:
            command = input("Tracker> ")
            if command == "test":
                print("The program is running normally.")
            elif command == "list":
                list_clients()
            elif command == "exit":
                print("Exiting Tracker Terminal...")
                break
            else:
                print("Unknown Command.")
    except KeyboardInterrupt:
        print("\nThe Tracker Terminal interrupted by user. Exiting Tracker Terminal...")
    finally:
        print("Tracker Terminal exited.")

if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236

    # Start server
    thread_server = Thread(target=server_program, args=(hostip, port))
    thread_server.start()

    # Start terminal
    tracker_terminal()

    shutdown_server()
    thread_server.join()

    sys.exit(0)


