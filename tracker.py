import socket
import pickle
import sys
import time
from threading import Thread, Event

all_connections = []
all_address = []
stop_event = Event()

# List of clients available
def list_clients():
    if all_connections and all_address:
        print("Connected Clients:")
        for i, addr in enumerate(all_address, start=1):
            print(f"{i}. IP: {addr[0]}, Port: {addr[1]}")
    else:
        print("No clients are currently connected.")

# Send the list of clients available to the newly connected client
def send_client_list(conn, addr):
    client_list = pickle.dumps(all_address)
    conn.send(client_list)

# New connection for newly connected client
def new_connection(conn, addr):
    # Send the clients list to the new client
    send_client_list(conn, addr)
    # Record the new client's metainfo
    all_connections.append(conn)
    all_address.append(addr)

    print(f"Client {addr} added.")

    while not stop_event.is_set():
        try:
            time.sleep(300) # Delete this later
            conn.settimeout(1)
            data = conn.recv(1024)
            if not data:
                break
            #TODO: process at tracker side
        except socket.timeout:
            continue
        except Exception:
            print("Error occured!")
            break

    conn.close()
    all_connections.remove(conn)
    all_address.remove(addr)
    print(f"Client {addr} removed.")

def server_program(host, port):
    print("Listening on: {}:{}".format(hostip,port))
    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)
    while not stop_event.is_set():
        try:
            serversocket.settimeout(1)
            conn, addr = serversocket.accept()
            if stop_event.is_set():
                break
            nconn = Thread(target=new_connection, args=(conn, addr))
            nconn.start()
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
       print(ip)
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip

def tracker_terminal():
    print("Tracker Terminal started.")
    while True:
        command = input("> ")
        if command == "test":
            print("The program is running normally.")
        elif command == "list":
            list_clients()
        elif command == "exit":
            print("Exiting Tracker Terminal.")
            stop_event.set()
            break

if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236
    thread_1 = Thread(target=server_program, args=(hostip, port))
    thread_1.start()

    try:
        tracker_terminal()
    except KeyboardInterrupt:
        stop_event.set()

    thread_1.join()
    for conn in all_connections:
        conn.close()
    sys.exit(0)


