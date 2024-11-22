import socket
import pickle
import sys
import time
import threading
from threading import Thread, Event
from tool import *
import json

SERVER_IP = get_host_default_interface_ip()
SERVER_PORT = 22236
stop_event = Event()

class tracker:
    def __init__(self):
        self.port = SERVER_PORT
        self.ip = SERVER_IP
        self.id = SERVER_PORT

        self.running = True

        self.client_info = {} #* A dictionary for storing the conenction of each client and the files they have
        self.lock = threading.Lock()
        self.client_conn_list = []
        self.client_addr_list = []
        self.nconn_threads = []

    # List of connected clients available
    def list_clients(self):
        if self.client_addr_list:
            print("Connected Clients:")
            for i, client in enumerate(self.client_addr_list, start=1):
                print(f"{i}. IP: {client[0]}, Port: {client[1]}")
        else:
            print("No clients are currently connected.")

    # FIX
    # Send the client list to the connected client
    def update_client_list(self, client_socket):
        print("Client list being sent...")

        header = "update_client_list:"
        pickle_client_addr_list = pickle.dumps(self.client_addr_list)
        message = header.encode("utf-8") + pickle_client_addr_list
        client_socket.sendall(message)
    
        print("Client list sent.")

                
    # New connection for connected client
    def new_conn_client(self, client_socket, client_ip, client_port):
        print(f"Connected to Client ('{client_ip}', {client_port}).")

        client_socket.settimeout(5)
        while not stop_event.is_set():
            try:
                data = client_socket.recv(4096)
                if not data:
                    break

                command = data[:(data.find(b":"))].decode("utf-8")
                if command == "update_client_list":
                    self.update_client_list(client_socket)
                elif command == "disconnect":
                    self.remove_client_info(client_ip, client_port) #! WORKING ON THIS
                    break
                elif command == "send_metainfo": #! WORKING ON THIS
                    metainfo_data = pickle.loads(data[len("send_metainfo:"):])
                    self.receive_metainfo(metainfo_data, client_ip, client_port)
                elif command == "find_peer_have":
                    pieces = pickle.loads(data[len("find_peer_have:"):])
                    self.find_peer_have(pieces, client_ip, client_port)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error occured: {e}")
                break

        client_socket.close()
        self.client_conn_list.remove(client_socket)
        self.client_addr_list.remove((client_ip, client_port))
        print(f"Client ('{client_ip}', {client_port}) disconnected.")


    def server_program(self):
        print(f"Tracker IP: {self.ip} | Tracker Port: {self.port}")
        print("Listening on: {}:{}".format(self.ip, self.port))
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.settimeout(5)

        serversocket.bind((self.ip, self.port))
        serversocket.listen(10)

        while not stop_event.is_set():
            try:
                client_socket, addr = serversocket.accept()
                client_ip = addr[0]

                # Receive client port separately
                string_client_port = client_socket.recv(1024)
                client_port = int(string_client_port.decode("utf-8"))

                # Create thread
                thread_client = Thread(target=self.new_conn_client, args=(client_socket, client_ip, client_port))
                thread_client.start()
                self.nconn_threads.append(thread_client)

                # Record the new client metainfo
                self.client_conn_list.append(client_socket)
                self.client_addr_list.append((client_ip, client_port))
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Server error: {e}")
                break
    
        serversocket.close()
        print("Tracker server stopped.")

    def disconnect_from_client(self, client_ip, client_port):
        if (client_ip, client_port) in self.client_addr_list:
            index = self.client_addr_list.index((client_ip, client_port))
            conn = self.client_conn_list[index]
        else:
            print(f"No connection found with client {client_ip}:{client_port}.")
            return

        header = "disconnect:"
        message = header.encode("utf-8")
        conn.sendall(message)

        print(f"Disconnect requested to client ('{client_ip}', {client_port}).")

    def disconnect_from_all_clients(self):
        for addr in client_addr_list:
            self.disconnect_from_client(addr[0], addr[1])
    
        print("All clients have been disconnected.")
        
    def shutdown_server(self):
        stop_event.set()
        for nconn in self.nconn_threads:
            nconn.join(timeout=5)
        print("All threads have been closed.")

    def receive_metainfo(self, metainfo_dict, client_ip, client_port): #! WORKING ON THIS
        print(f"Receiving  metainfo from client {client_ip}:{client_port}")

        try:
            print(f"Received Metainfo: {metainfo_dict}")

            file_name = metainfo_dict.get('file_name')
            pieces = metainfo_dict.get('pieces') 

            if not file_name or not pieces:
                print("Invalid metainfo received, missing 'file_name' or 'pieces'.")
                return
            
            self.update_client_info(client_ip, client_port, pieces)
        except Exception as e:
            print(f"Error receiving metainfo from {client_ip}:{client_port}: {e}")
            
    def update_client_info(self, client_ip, client_port, hashcode):  
        try:
            # Locking client_info for thread safety
            with self.lock:
                client_key = (client_ip, client_port)  

                if client_key in self.client_info:
                    self.client_info[client_key] += hashcode
                else:
                    self.client_info[client_key] = hashcode  

            print(f"Updated client_info: {client_key} now has hashcode '{hashcode}'.")
        except Exception as e:
            print(f"Error updating client_info for {client_ip}:{client_port}: {e}")

    def find_peer_have(self, hashcode, client_ip, client_port):
        try:
            peer_list = []  

            # Locking client_info for thread safety
            with self.lock:
                for client_key, client_hashcode in self.client_info.items():
                    #print(f"{client_key} with {client_hashcode}") #! THIS IS ONLY USED FOR DEBUGGING, REMEMBER TO DELETE
                    if hashcode in client_hashcode:
                        peer_list.append(client_key) 

            print(f"Peers with hashcode '{hashcode}': {peer_list}")
        except Exception as e:
            print(f"Error finding peers with hashcode '{hashcode}': {e}")

        self.send_peer_have(peer_list, client_ip, client_port)

    
    def send_peer_have(self, peer_list, client_ip, client_port): #! WORKING ON THIS
        if (client_ip, client_port) in self.client_addr_list:
            index = self.client_addr_list.index((client_ip, client_port))
            conn = self.client_conn_list[index]
        else:
            print(f"No connection found with client {client_ip}:{client_port}.")
            return

        try :
            header = "peer_list:".encode("utf-8")
            header += pickle.dumps(peer_list)
            conn.sendall(header)
            time.sleep(0.1)
            print(f"Complete sending peer list to {client_ip} : {client_port}")
        except Exception as e:
            print(f"Failed to send peer list to {client_ip} : {client_port}: {e}")

    def remove_client_info(self, client_ip, client_port): #! WORKING ON THIS 
        try:
            # Locking client_info for thread safety
            with self.lock:
                client_key = (client_ip, client_port)
                if client_key in self.client_info:
                    del self.client_info[client_key]
                    #! ONLY USED FOR DEBUGGING
                    #print(f"Removed client_info for {client_key}.")
                else:
                    print(f"Client {client_key} not found in client_info.")
        except Exception as e:
            print(f"Error removing client_info for {client_ip}:{client_port}: {e}")


if __name__ == "__main__":

    # Start server
    tracker_instance = tracker()
    try:
        thread_tracker = Thread(target=tracker_instance.server_program)
        thread_tracker.start()

        while True:
            command = input("Tracker> ")
            if command == "test":
                print("The program is running normally.")
            elif command == "list_clients":
                tracker_instance.list_clients()
            elif command.startswith("disconnect_from_client"):
                parts = command.split()
                if len(parts) == 3:
                    client_ip = parts[1]
                    try:
                        client_port = int(parts[2])
                        tracker_instance.disconnect_from_client(client_ip, client_port)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: disconnect_from_client <IP> <Port>")
            elif command == "disconnect_from_all_clients":
                tracker_instance.disconnect_from_all_clients()
            elif command == "exit":
                tracker_instance.disconnect_from_all_clients()
                print("Exiting Tracker Terminal...")
                break
            else:
                print("Unknown Command.")
    except KeyboardInterrupt:
        print("\nThe Tracker Terminal interrupted by user. Exiting Tracker Terminal...")
    finally:
        print("Tracker Terminal exited.")


    tracker_instance.shutdown_server()
    thread_tracker.join(timeout=5)

    sys.exit(0)