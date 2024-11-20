import socket
import pickle
import sys
import time
from threading import Thread, Event

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

hostip = get_host_default_interface_ip()
port = 22236

client_conn_list = [] # Tracker's connected client conn List
client_addr_list = [] # Tracker's connected client addr List
stop_event = Event() # Stop all the command loops
nconn_threads = [] # Store all the threads created

# List of connected clients available
def list_clients():
    if client_addr_list:
        print("Connected Clients:")
        for i, client in enumerate(client_addr_list, start=1):
            print(f"{i}. IP: {client[0]}, Port: {client[1]}")
    else:
        print("No clients are currently connected.")

# FIX
# Send the client list to the connected client
def update_client_list(client_socket):
    print("Client list being sent...")

    header = "update_client_list:"
    pickle_client_addr_list = pickle.dumps(client_addr_list)
    message = header.encode("utf-8") + pickle_client_addr_list
    client_socket.sendall(message)
    time.sleep(1)
    
    print("Client list sent.")

# New connection for connected client
def new_conn_client(client_socket, client_ip, client_port):
    print(f"Connected to Client ('{client_ip}', {client_port}).")

    client_socket.settimeout(5)
    while not stop_event.is_set():
        try:
            data = client_socket.recv(4096)
            command = data.decode("utf-8")
            if not data:
                break
            elif command == "update_client_list":
                update_client_list(client_socket)
            elif command == "disconnect":
                break
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error occured: {e}")
            break

    client_socket.close()
    client_conn_list.remove(client_socket)
    client_addr_list.remove((client_ip, client_port))
    print(f"Client ('{client_ip}', {client_port}) disconnected.")

def server_program():
    print(f"Tracker IP: {hostip} | Tracker Port: {port}")
    print("Listening on: {}:{}".format(hostip,port))
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.settimeout(5)

    serversocket.bind((hostip, port))
    serversocket.listen(10)

    while not stop_event.is_set():
        try:
            client_socket, addr = serversocket.accept()
            client_ip = addr[0]

            # Receive client port separately
            string_client_port = client_socket.recv(1024)
            client_port = int(string_client_port.decode("utf-8"))

            # Create thread
            thread_client = Thread(target=new_conn_client, args=(client_socket, client_ip, client_port))
            thread_client.start()
            nconn_threads.append(thread_client)

            # Record the new client metainfo
            client_conn_list.append(client_socket)
            client_addr_list.append((client_ip, client_port))
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Server error: {e}")
            break
    
    serversocket.close()
    print("Tracker server stopped.")

# FIX
def disconnect_from_client(conn, client_ip, client_port):
    command = "disconnect"
    conn.send(command.encode("utf-8"))
    print(f"Disconnect requested to client ('{client_ip}', {client_port}).")

# FIX
def disconnect_from_all_clients():
    command = "disconnect"
    for conn in client_conn_list:
        conn.send(command.encode("utf-8"))
        print("Exit requested.")

def shutdown_server():
    stop_event.set()
    for nconn in nconn_threads:
        nconn.join(timeout=5)
    print("All threads have been closed.")

def tracker_terminal():
    print("Tracker Terminal started.") 
    try:
        while True:
            command = input("Tracker> ")
            if command == "test":
                print("The program is running normally.")
            elif command == "list_clients":
                list_clients()
            elif command == "exit":
                disconnect_from_all_clients()
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

    # Start server
    thread_server = Thread(target=server_program)
    thread_server.start()

    # Start terminal
    tracker_terminal()

    shutdown_server()
    thread_server.join(timeout=5)

    sys.exit(0)


