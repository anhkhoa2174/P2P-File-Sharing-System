import socket
import threading
import os
from tool import *
from file import File
import random
import time
import pickle
from threading import Thread
import sys
import json

PEER_IP = get_host_default_interface_ip()
LISTEN_DURATION = 5
PORT_FOR_PEER= random.randint(12600, 22000)
stop_event = Event()

class peer:
    def __init__(self):
        self.peerIP = PEER_IP # peer's IP
        self.peerID = PORT_FOR_PEER # peer' ID
        self.portForPeer = PORT_FOR_PEER # port for peer conection with other peers
        self.portForTracker = PORT_FOR_PEER + 1 # port for peer connection with tracker
        self.lock = threading.Lock()
        self.fileInRes = []
        self.isRunning = False
        self.peerDownloadingFrom = []
        self.server = []
        self.processedFileName = []  # List of already processed files
         # A socket for listening from other peers in the network
        self.peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peerSocket.bind((self.peerIP, self.portForPeer))
        self.file_info_array = []   # mang chua cac mapping cua bitfield message

        print(f"A peer with IP address {self.peerIP}, ID {self.portForTracker} has been created")

        
        self.connected_client_conn_list = [] # Current clients conn connected to this client
        self.connected_client_addr_list = [] # Current clients addr connected to this client
        self.connected_tracker_conn_list = []
        self.connected_tracker_addr_list = []
        self.new_conn_thread_list = []

    @property # This creates an own respo for peer to save metainfo file
    def peerOwnRes(self):
        peerOwnRes = "my_own_respo_" + str(self.peerID)
        os.makedirs(peerOwnRes, exist_ok=True)
        peerOwnRes += "/"
        return peerOwnRes
    
    
    def print_file_info_array(self):
        for entry in self.file_info_array:
            print(f"Infohash: {entry['infohash']}")
            print("Mapping:")
            for ip, bitfield in entry["mapping"].items():
                print(f"  IP: {ip}, BitfieldMessage: {bitfield}")
            print()
            
            
    def add_or_update_file_info_array(self, infohash, peer_ip, bitfieldMessage):

        # Tìm xem infohash đã tồn tại trong danh sách chưa
        file_info = next((item for item in self.file_info_array if item["infohash"] == infohash), None)
        
        if file_info:
            # Nếu đã tồn tại, cập nhật mapping
            file_info["mapping"][peer_ip] = bitfieldMessage
        else:
            # Nếu chưa tồn tại, thêm mới vào array
            new_entry = {
                "infohash": infohash,
                "mapping": {peer_ip: bitfieldMessage}
            }
            self.file_info_array.append(new_entry)
            
    def wait_for_mapping_size(self, hashcode, peer_list):
        mapping_size = 0

        timeout = 30  # Đặt thời gian chờ tối đa
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Duyệt qua file_info_array để lấy mapping_size
            for entry in self.file_info_array:
                if entry['infohash'] == hashcode:
                    mapping_size = len(entry['mapping'])
                    break

            # Kiểm tra nếu mapping_size đã khớp với kích thước của peer_list
            if mapping_size == len(peer_list):
                print("Thoa dieu kien de vo thuat toan roi")
                return True

            # Nếu điều kiện chưa thỏa mãn, chờ một thời gian ngắn trước khi thử lại
            time.sleep(1)  # Đợi 1 giây trước khi kiểm tra lại

        print(f"Timeout reached. Bi loi r, nguuuuuuuuuuuuuuuuuuuuuu {hashcode}.")
        return False
        
    def getFileInRes(self) -> list:
       
        ownRespository = os.listdir("peer_respo")
        if len(ownRespository) == 0:
            return self.fileInRes
        else:
            for name in ownRespository:
                # Skip files that are already processed
                if name in self.processedFileName:
                    continue

                file_path = "peer_respo/" + name
                if os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                else:
                    # Add the file to fileInRes and mark it as processed
                    file_obj = File(file_path, "")
                    self.fileInRes.append(file_obj)
                    self.processedFileName.append(name)
                    
                    
    
                    file_obj.split_file(name, file_obj.meta_info.length, 512 * 1024)
                    
                    if file_obj.meta_info_from_torrent.info_hash == None:
                        # Testing creating metainfo
                        file_obj.meta_info_from_torrent = file_obj.meta_info
                        
                        with self.lock:
                            file_obj._initialize_piece_states()

                    file_obj.print_file_information()  # For testing

                    self.save_metainfo_to_txt(file_obj.meta_info)

        return self.fileInRes
    
    def save_metainfo_to_txt(self, metainfo):
        # The path to txt file that saves metainfo of a specific file
        file_path = os.path.join(self.peerOwnRes, f"{metainfo.fileName}_metainfo.txt")
        
        # Write metainfo into file
        with open(file_path, "w", encoding=CODE) as file:
            file.write(f"File Name: {metainfo.fileName}\n")
            file.write(f"File Length: {metainfo.length} bytes\n")
            file.write(f"Piece Length: {metainfo.pieceLength} bytes\n")
            file.write(f"Number of Pieces: {int(metainfo.numOfPieces)}\n")
            file.write(f"Piece List: {(metainfo.piecesList)}\n")
            file.write(f"SHA-1 Hashes of Pieces: {metainfo.pieces}\n")
            file.write(f"Info Hash: {metainfo.info_hash}\n")
        
        print(f"Metainfo for {metainfo.fileName} has been saved to {file_path}") 
    
    # List of clients connected to the Tracker
    def list_clients(self):
        if client_addr_list:
            print("Connected Clients:")
            for i, client in enumerate(client_addr_list, start=1):
                print(f"{i}. IP: {client[0]}, Port: {client[1]}")
        else:
            print("No clients are currently connected.")

    # List of peers connected to this client
    def list_peers(self):
        if self.connected_client_addr_list:
            print("Connected Peers:")
            for i, client in enumerate(self.connected_client_addr_list, start=1):
                print(f"{i}. IP: {client[0]}, Port: {client[1]}")
        else:
            print("No peers are currently connected.")

    def update_client_list(self, server_host, server_port):
        if (server_host, server_port) in self.connected_tracker_addr_list:
            index = self.connected_tracker_addr_list.index((server_host, server_port))
            conn = self.connected_tracker_conn_list[index]
        else:
            print(f"No connection found with Tracker {server_host}:{server_port}.")
            return

        # Create command for the Tracker
        header = "update_client_list:"
        message = header.encode(CODE)
        conn.sendall(message)

        print(f"Client list requested to Tracker ({server_host}:{server_port}).")     

    # Connect to the Tracker
    def new_conn_tracker(self, tracker_socket, server_host, server_port):
        global client_addr_list
        print(f"Connected to Tracker ('{server_host}', {server_port}).")
        
        tracker_socket.settimeout(5)
        while not stop_event.is_set():
            try:
                data = tracker_socket.recv(4096)
                if not data:
                    break

                command = data[:(data.find(b":"))].decode(CODE)
                if command == "update_client_list":
                    # Receive the clients list from the Tracker
                    client_addr_list = pickle.loads(data[len("update_client_list:"):])
                    print("Client list received.")
                elif command == "disconnect":
                    break
                
          ##TODO TIẾN TRÌNH CHÍNH Ở DƯỚI
                if command == "peer_list": #! WORKING ON THIS 
                    # Receive the clients list from the Tracker
                    separator_index = data.rfind(b":")
                    
                    if separator_index == -1:
                        raise ValueError("Invalid data format. Missing separator for hashcode.")
                    
                    part1 = data[:separator_index]
                    part2 = data[separator_index + 1:]


                    peer_list = pickle.loads(part1[len("peer_list:"):])

                    # Phần sau dấu ":" cuối là hashcode
                    hashcode = part2.decode("utf-8")

                    print(f"Peer list received: {peer_list}, hashcode:{hashcode}")
                    
                    downloadFile = None
                    
                    for file in self.fileInRes:
                        if file.meta_info_from_torrent.info_hash == hashcode:
                            downloadFile = file
                            
                    #print(f"fileName:{downloadFile.meta_info_from_torrent.fileName}")
 
                            
                    for peer_ip, peer_port in peer_list:
                        connected = True
                        for peer_ip2, peer_port2 in self.connected_client_addr_list:
                            if peer_ip == peer_ip2 and peer_port == peer_port2: #!!! CO NEN BO so sanh peer port khong ?
                                connected = False
                                break
                            
                        if connected:
                            self.connect_to_peer(peer_ip, peer_port)
                            
                        self.send_infohash(peer_ip, peer_port, hashcode) 
                    
                    
                    download = self.wait_for_mapping_size(hashcode, peer_list)
                    
                    if download:
                        #self.download()
                        print(f"bat dau download")
                       
    ##TODO TIẾN TRÌNH CHÍNH Ở TRÊN
                        
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Client error: {e}")
                break

        tracker_socket.close()
        self.connected_tracker_conn_list.remove(tracker_socket)
        self.connected_tracker_addr_list.remove((server_host, server_port))
        print(f"Tracker ('{server_host}', {server_port}) disconnected.")

    def connect_to_tracker(self, server_host, server_port):
        try:
            tracker_socket = socket.socket()
            tracker_socket.connect((server_host, server_port))
        except ConnectionRefusedError:
            print(f"Could not connect to Tracker {server_host}:{server_port}.")

        # Send client port separately
        string_client_port = str(self.portForPeer)
        tracker_socket.sendall(string_client_port.encode(CODE))
        time.sleep(0.1) # SPE: neighbour sendall()

        # Create thread
        thread_tracker = Thread(target=self.new_conn_tracker, args=(tracker_socket, server_host, server_port))
        thread_tracker.start()
        self.new_conn_thread_list.append(thread_tracker)

        # Record the Tracker metainfo
        self.connected_tracker_conn_list.append(tracker_socket)
        self.connected_tracker_addr_list.append((server_host, server_port))
    
        self.update_client_list(server_host, server_port)

    def new_conn_peer(self, peer_socket, peer_ip, peer_port):
        print(f"Connected to peer {peer_ip}:{peer_port}.")

        peer_socket.settimeout(5)
        while not stop_event.is_set():
            try:
                data = peer_socket.recv(4096)
                if not data:
                    break

                command = data[:(data.find(b":"))].decode(CODE)
                if command == "disconnect":
                    break
                
                elif command == "download":
                    file_name = data[(data.find(b":") + 1):].decode(CODE)
                    print(f"Received request download_file '{file_name}' from peer ({peer_ip}:{peer_port})")
                    self.send_file(peer_socket, file_name)
                    
                elif command == "info":
                    info_hash = data[(data.find(b":") + 1):].decode(CODE)
                    print(f"Received info_hash '{info_hash}' from peer ({peer_ip}:{peer_port})")
                    self.send_bfm(peer_socket, info_hash)
                    
                elif command == "bfm":
                    try:
                        bfm = data[(data.find(b":") + 1):].decode(CODE)
                        
                        separator_index = bfm.find(":")
                        
                        if separator_index == -1:
                            raise ValueError("Invalid bfm format. Missing separator for infohash and bitFieldMessage.")
                        
                        infohash = bfm[:separator_index] 
                        bitFieldMessage = bfm[separator_index + 1:] 

                        print(f"Received bfm with infohash: '{infohash}', bitFieldMessage: '{bitFieldMessage}' from peer ({peer_ip}:{peer_port})")
                        
                        with self.lock:
                            self.add_or_update_file_info_array(infohash, peer_ip, bitFieldMessage)
                            self.print_file_info_array()
                        
                    except Exception as e:
                        print(f"Error processing bfm: {e}")
                    
                elif command == "receive_file":
                    data_receive = data[(data.find(b":") + 1):]
                    self.receive_file(peer_socket, data_receive)
                elif command == "not_receive_file":
                    data_receive = data[(data.find(b":") + 1):].decode(CODE)
                    print(f"{data_receive} from peer ({peer_ip}:{peer_port})")
                    
                else:
                    print(f"Unknown command received: {command}")                
            except socket.timeout:
                continue
            except Exception:
                print("Error occured!")
                break

        peer_socket.close()
        self.connected_client_conn_list.remove(peer_socket)
        self.connected_client_addr_list.remove((peer_ip, peer_port))
        print(f"Peer ('{peer_ip}', {peer_port}) removed.")

    # Connect to all peers
    def connect_to_all_peers(self):
        for peer in client_addr_list:
            if peer[0] == self.peerIP and peer[1] == self.portForPeer:
                continue
            self.connect_to_peer(peer[0], peer[1])
        print("All peers have been connected.")

    # Connect to one peer
    def connect_to_peer(self, peer_ip, peer_port):
        try:
            if peer_ip == self.peerIP and peer_port == self.portForPeer:
                print("Cannot connect to self.")
                return
            peer_socket = socket.socket()
            peer_socket.connect((peer_ip, peer_port))
        except ConnectionRefusedError:
            print(f"Could not connect to peer {peer_ip}:{peer_port}.")
    
        # Send peer port separately
        string_peer_port = str(self.portForPeer)
        peer_socket.send(string_peer_port.encode(CODE))
        
        # Create thread
        thread_peer = Thread(target=self.new_conn_peer, args=(peer_socket, peer_ip, peer_port))
        thread_peer.start()
        self.new_conn_thread_list.append(thread_peer)

        # Record the new peer metainfo
        self.connected_client_conn_list.append(peer_socket)
        self.connected_client_addr_list.append((peer_ip, peer_port))

    # Send info hash to a peer
    def send_infohash(self, peer_ip, peer_port, infohash):
        try:
            if (peer_ip, peer_port) in self.connected_client_addr_list:
                index = self.connected_client_addr_list.index((peer_ip, peer_port))
                peer_socket = self.connected_client_conn_list[index]
            else:
                print(f"No connection found with peer {peer_ip}:{peer_port}.")
                return
            
            request_message = f"info:{str(infohash)}"
            peer_socket.send(request_message.encode(CODE))
            
            
            print(f"Sent successful infohash to {peer_ip}:{peer_port}") 
        except Exception as e:
            print(f"Error sending infohash: {e}")  
            
    def send_bfm(self, conn, infohash):   
        try:         
            for file in self.fileInRes:
                if file.meta_info_from_torrent.info_hash == infohash:
                    with self.lock:
                        file._initialize_piece_states()
                        bfm = f"bfm:{infohash}:{file.bitFieldMessage}"
                        conn.send(bfm.encode(CODE))
        except Exception as e:
                print(f"Error send_bfm: {e}")  
                
                
                            
        #print(f"fileName:{downloadFile.meta_info_from_torrent.fileName}")
    def download_file(self, peer_ip, peer_port, file_name):
            try:
                if (peer_ip, peer_port) in self.connected_client_addr_list:
                    index = self.connected_client_addr_list.index((peer_ip, peer_port))
                    peer_socket = self.connected_client_conn_list[index]
                else:
                    print(f"No connection found with peer {peer_ip}:{peer_port}.")
                    return
                
                print(f"Requesting file '{file_name}' from peer {peer_ip}:{peer_port}..............")
                
                request_message = f"download:{file_name}"
                peer_socket.send(request_message.encode(CODE))

            except Exception as e:
                print(f"Error requesting file: {e}")  
                
    # Download a file from all peers
    def download_file_from_all_peers(self, file_name):
        try:
            threads = []
            
            for peer_ip, peer_port in self.connected_client_addr_list:
                thread = Thread(target=self.download_file, args=(peer_ip, peer_port, file_name))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
            
            print(f"Finished downloading '{file_name}' from all peers.")
        
        except Exception as e:
            print(f"Error download from all peers: {e}")  

    def send_file(self, conn, file_name):
        
        #if(filename == filename1):print("fffffffffff")
        try:
            with open(file_name, "rb") as f:
                file_data = f.read()

            file_size = len(file_data)
            
            header = f"receive_file:{file_name}:{file_size}"

            data_to_send = header.encode(CODE) + b"\n" + file_data

            conn.sendall(data_to_send)
            
            print(f"File {file_name} has been sent to the client.")

        except FileNotFoundError:
            print(f"File {file_name} not found.")
            error_message = f"not_receive_file:File '{file_name}' not found."
            conn.sendall(error_message.encode(CODE)) 
        except Exception as e:
            print(f"Error sending file {file_name}: {e}")
            
        
    def receive_file(self, peer_socket, data_receive):
        try:
            header, file_data = data_receive.split(b"\n", 1)
            parts = header.split(b':')

            if len(parts) == 2:
                file_name = parts[0].decode(CODE)
                file_size = int(parts[1].decode(CODE))
            else:
                print("Invalid data format.")

            if file_size <= 0:
                print(f"Cannot receiving invalid file")
                return
            
            print(f"File size to receive: {file_size} bytes")

            print(f"Receiving file: {file_name}")
            
            with open(file_name, "wb") as file:

                file.write(file_data)
                received_size = len(file_data)
                if received_size != file_size:
                    print(f"\nFile '{file_name}' cannot receive enough.")
                    return

            print(f"\nFile '{file_name}' received successfully.")

        except Exception as e:
            print(f"Error receiving file: {e}")     
            
    def client_program(self):
        print(f"Peer IP: {self.peerIP} | Peer Port: {self.portForPeer}")
        print("Listening on: {}:{}".format(self.peerIP, self.portForPeer))
        
        self.peerSocket.settimeout(5)
        self.peerSocket.listen(10)

        while not stop_event.is_set():
            try:
                peer_socket, addr = self.peerSocket.accept()
                peer_ip = addr[0]

                # Receive peer port separately
                string_peer_port = peer_socket.recv(1024).decode(CODE)
                peer_port = int(string_peer_port)

                # Create thread
                thread_peer = Thread(target=self.new_conn_peer, args=(peer_socket, peer_ip, peer_port))
                thread_peer.start()
                self.new_conn_thread_list.append(thread_peer)

                # Record the new peer metainfo
                self.connected_client_conn_list.append(peer_socket)
                self.connected_client_addr_list.append((peer_ip, peer_port))
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Peer error: {e}")
                break

        self.peerSocket.close()
        print(f"Peer {self.peerIP} stopped.")

    def disconnect_from_tracker(self, server_host, server_port):
        if (server_host, server_port) in self.connected_tracker_addr_list:
            index = self.connected_tracker_addr_list.index((server_host, server_port))
            conn = self.connected_tracker_conn_list[index]
        else:
            print(f"No connection found with Tracker {server_host}:{server_port}.")
            return

        header = "disconnect:"
        message = header.encode(CODE)
        conn.sendall(message)

        print(f"Disconnect requested to Tracker ({server_host}:{server_port}).")
        
    def disconnect_from_peer(self, peer_ip, peer_port):
        if (peer_ip, peer_port) in self.connected_client_addr_list:
            index = self.connected_client_addr_list.index((peer_ip, peer_port))
            conn = self.connected_client_conn_list[index]
        else:
            print(f"No connection found with client {peer_ip}:{peer_port}.")
            return

        header = "disconnect:"
        message = header.encode(CODE)
        conn.sendall(message)

        print(f"Disconnect requested to peer ('{peer_ip}', {peer_port}).")

    def disconnect_from_all_peers(self):
        for addr in self.connected_client_addr_list:
            self.disconnect_from_peer(addr[0], addr[1])

        print("All peers have been disconnected.")

    def shutdown_peer(self):
        stop_event.set()
        for nconn in self.new_conn_thread_list:
            nconn.join(timeout=5)
        print("All threads have been closed.") 

    def send_metainfo_to_tracker(self, server_host, server_port): #! WORKING ON THIS 
        if (server_host, server_port) in self.connected_tracker_addr_list:
            index = self.connected_tracker_addr_list.index((server_host, server_port))
            conn = self.connected_tracker_conn_list[index]
        else:
            print(f"No connection found with Tracker {server_host}:{server_port}.")
            return
    
        
        for file in self.fileInRes:
            metainfo = file.meta_info  

            if not file.sentMetaInfo:
                metainfo_dict = {
                    'file_name': metainfo.fileName,
                    'file_size': metainfo.length,
                    'piece_length': metainfo.pieceLength,
                    'pieces_list': metainfo.piecesList,
                    'pieces': metainfo.pieces,
                    'num_of_pieces': metainfo.numOfPieces,
                    'info_hash': metainfo.info_hash
                }

            try:
                header = "send_metainfo:".encode(CODE)
                header += pickle.dumps(metainfo_dict)
                file.sentMetaInfo = True
                conn.sendall(header)
                time.sleep(0.1)
                print(f"Sent Metainfo for {metainfo.fileName} to tracker.")
            except Exception as e:
                print(f"Failed to send Metainfo for {metainfo.fileName} to tracker: {e}")

    def find_peer_have(self, hash_info, server_host, server_port): #! WORKING ON THIS 
        new_entry = {
            "infohash": hash_info,
            "mapping": {}
        }
        
        self.file_info_array.append(new_entry)
        
        
        if (server_host, server_port) in self.connected_tracker_addr_list:
            index = self.connected_tracker_addr_list.index((server_host, server_port))
            conn = self.connected_tracker_conn_list[index]
        else:
            print(f"No connection found with Tracker {server_host}:{server_port}.")
            return

        try:
            print(f"Asking tracker to find peer list with magnet text {hash_info}.")
            header = "find_peer_have:".encode(CODE)
            header += pickle.dumps(hash_info)
            conn.sendall(header)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Failed to ask for tracker to find peer list with magnet text {hash_info}.: {e}")
       
    
        
    #Merge a file received
    def merge_file(self, file_name):
        import os

        root_folder = os.getcwd()  # Thư mục gốc của project
        file_have_folder = os.path.join(root_folder, "peer_respo")
        file_share_folder = os.path.join(root_folder, "FileShare")
        
        # Đảm bảo các folder peer_respo và Fileshare tồn tại
        if not os.path.exists(file_have_folder):
            print(f"'peer_respo' folder does not exist in the project root: {root_folder}")
            return None
        if not os.path.exists(file_share_folder):
            print(f"'Fileshare' folder does not exist in the project root: {root_folder}")
            return None

        # Kiểm tra xem folder tên file có tồn tại trong Fileshare không
        folder_with_pieces = os.path.join(file_share_folder, os.path.splitext(file_name)[0])
        if not os.path.exists(folder_with_pieces) or not os.path.isdir(folder_with_pieces):
            print(f"Folder '{file_name}' not found in 'Fileshare'.")
            return None


        merged_file_path = os.path.join(file_have_folder, file_name)

        try:
            with open(merged_file_path, "wb") as merged_file:
                # Lấy danh sách tất cả các piece trong folder, đảm bảo theo thứ tự
                pieces = sorted(os.listdir(folder_with_pieces))
                
                for piece in pieces:
                    piece_path = os.path.join(folder_with_pieces, piece)
                    print(f"Merging: {piece_path}")
                    
                    # Đọc dữ liệu từ từng piece và ghi vào file hợp nhất
                    with open(piece_path, "rb") as piece_file:
                        merged_file.write(piece_file.read())
            
            print(f"File '{file_name}' has been successfully merged in '{file_have_folder}'.")
            return merged_file_path

        except Exception as e:
            print(f"Error merging file '{file_name}': {e}")
            return None


if __name__ == "__main__":
    my_peer = peer()
    try:
        peer_thread = Thread(target=my_peer.client_program)
        peer_thread.start()

        while True:
            command = input("Peer> ")
            if command == "test":
                print("The program is running normally.")
            elif command.startswith("merge_file"):
                parts = command.split()
                if len(parts) == 2:
                    file_name = parts[1]
                    try:
                        my_peer.merge_file(file_name)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: merge_file <file_name>")
            elif command.startswith("connect_to_tracker"):
                parts = command.split()
                if len(parts) == 3:
                    server_host = parts[1]
                    try:
                        server_port = int(parts[2])
                        my_peer.connect_to_tracker(server_host, server_port)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: connect_tracker <IP> <Port>")
            elif command.startswith("disconnect_from_tracker"):
                parts = command.split()
                if len(parts) == 3:
                    server_host = parts[1]
                    try:
                        server_port = int(parts[2])
                        my_peer.disconnect_from_tracker(server_host, server_port)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: disconnect_from_tracker <IP> <Port>")
            elif command == "list_clients":
                my_peer.list_clients()
            elif command == "update_client_list":
                my_peer.update_client_list(server_host, server_port)
            elif command == "list_peers":
                my_peer.list_peers()   
            elif command.startswith("connect_to_peer"):
                parts = command.split()
                if len(parts) == 3:
                    peer_ip = parts[1]
                    try:
                        peer_port = int(parts[2])
                        my_peer.connect_to_peer(peer_ip, peer_port)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: connect_to_peer <IP> <Port>")
            elif command == "connect_to_all_peers":
                my_peer.connect_to_all_peers() 
            elif command.startswith("disconnect_from_peer"):
                parts = command.split()
                if len(parts) == 3:
                    peer_ip = parts[1]
                    try:
                        peer_port = int(parts[2])
                        my_peer.disconnect_from_peer(peer_ip, peer_port)
                    except ValueError:
                        print("Invalid port.")
                else:
                    print("Usage: disconnect_from_peer <IP> <Port>")
            elif command == "disconnect_from_all_peers":
                my_peer.disconnect_from_all_peers()  
            elif command.startswith("download"):
                parts = command.split()
                if len(parts) == 4:
                    peer_ip = parts[1]
                    try:
                        peer_port = int(parts[2])
                        file_name = parts[3]
                        my_peer.download_file(peer_ip, peer_port, file_name)
                    except ValueError:
                        print("Invalid port.")
                    except Exception as e:
                        print(f"Error downloading file: {e}")
                else:
                    print("Usage: download <IP> <Port> <file_name>")   
            elif command.startswith("from_all_peers_download"):
                parts = command.split()
                if len(parts) == 2:
                    file_name = parts[1]
                    try:
                        my_peer.download_file_from_all_peers(file_name)
                    except Exception as e:
                        print(f"Error downloading file from all peers: {e}")
                else:
                    print("Usage: from_all_peers_download <file_name>")  
            elif command == "get_metainfo":
                my_peer.getFileInRes()
            elif command == "send_metainfo": #! WORKING ON THIS
                my_peer.send_metainfo_to_tracker(server_host, server_port)
            elif command == "find_peer_have": #! WORKING ON THIS
                torrent_path = input("Enter torrent path: ")
                downloadfile = File("",torrent_path)
                
                my_peer.fileInRes.append(downloadfile)
                
                hash_info = downloadfile.meta_info_from_torrent.info_hash
                my_peer.find_peer_have(hash_info, server_host, server_port)
            elif command == "exit":
                my_peer.disconnect_from_tracker(server_host, server_port)
                my_peer.disconnect_from_all_peers()
                print("Exiting Client Terminal.")
                break
            else:
                print("Unknown Command.")
    except KeyboardInterrupt:
        print("\nThe Client Terminal interrupted by user. Exiting Client Terminal...")
    finally:
        print("Client Terminal exited.")
    
    my_peer.shutdown_peer()
    peer_thread.join(timeout=5)
    sys.exit(0)