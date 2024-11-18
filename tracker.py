import socket
import pickle
from threading import Thread

all_connections = []
all_address = []

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

    while True:
        try:
            data = conn.recv(1024)

            #TODO: process at tracker side
        except Exception:
            print("Error occured!")
            break

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


def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)
    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_connection, args=(conn, addr))
        nconn.start()


if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236
    print("Listening on: {}:{}".format(hostip,port))
    server_program(hostip, port)