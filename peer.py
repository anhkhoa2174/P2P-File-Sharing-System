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
from file import Metainfo
from file import BLOCK_LENGTH
from file import PIECE_LENGTH
import queue
import shutil


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
        
        self.sent_requests_queue = queue.Queue() 

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
                return True

            # Nếu điều kiện chưa thỏa mãn, chờ một thời gian ngắn trước khi thử lại
            time.sleep(1)  # Đợi 1 giây trước khi kiểm tra lại

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
                    
                    self.save_metainfo_to_txt(file_obj.meta_info)
                    with self.lock:   
                        file_obj.split_file(name, file_obj.meta_info.length, 512 * 1024)
                    
                    if file_obj.meta_info_from_torrent.info_hash == None:
                        # Testing creating metainfo
                        file_obj.meta_info_from_torrent.fileName = file_obj.meta_info.fileName
                        file_obj.meta_info_from_torrent.length = file_obj.meta_info.length
                        file_obj.meta_info_from_torrent.pieceLength = file_obj.meta_info.pieceLength
                        file_obj.meta_info_from_torrent.piecesList = file_obj.meta_info.piecesList
                        file_obj.meta_info_from_torrent.pieces = file_obj.meta_info.pieces
                        file_obj.meta_info_from_torrent.info_hash = file_obj.meta_info.info_hash
                        file_obj.meta_info_from_torrent.numOfPieces = file_obj.meta_info.numOfPieces
                        file_obj.meta_info_from_torrent.filePath = f"{self.peerOwnRes}"+f"{file_obj.meta_info_from_torrent.fileName}"
                        
                        with self.lock:
                            file_obj._initialize_piece_states()

                    file_obj.print_file_information()  # For testing

               

        return self.fileInRes
    
    def save_metainfo_to_txt(self, metainfo):
        # The path to txt file that saves metainfo of a specific file
        file_path = os.path.join(self.peerOwnRes, f"{metainfo.fileName}")
        
        # Write metainfo into file
        with open(file_path, "w", encoding=CODE) as file:
            file.write(f"File Name: {metainfo.fileName}\n")
            file.write(f"File Length: {metainfo.length} bytes\n")
            file.write(f"Piece Length: {metainfo.pieceLength} bytes\n")
            file.write(f"Number of Pieces: {int(metainfo.numOfPieces)}\n")
            file.write(f"Piece List: {(metainfo.piecesList)}\n")
            file.write(f"SHA-1 Hashes of Pieces: {metainfo.pieces}\n")
            file.write(f"Info Hash: {metainfo.info_hash}\n")
        
       # print(f"Metainfo for {metainfo.fileName} has been saved to {file_path}") 
    
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
        time.sleep(0.1)


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
                
                if command == "peer_list": 
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
    
                    handle_thread = threading.Thread(target=self.handle, args=(hashcode, peer_list))
                    handle_thread.start()              
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Client error: {e}")
                break

        tracker_socket.close()
        self.connected_tracker_conn_list.remove(tracker_socket)
        self.connected_tracker_addr_list.remove((server_host, server_port))
        print(f"Tracker ('{server_host}', {server_port}) disconnected.")


            
    def handle(self, hashcode, peer_list):
        downloadFile = None
        for file in self.fileInRes:
            if file.meta_info_from_torrent.info_hash == hashcode:
                downloadFile = file          
                for peer_ip, peer_port in peer_list:
                    connected = True
                    for peer_ip2, peer_port2 in self.connected_client_addr_list:
                        if peer_ip == peer_ip2 and peer_port == peer_port2: 
                            connected = False
                            break
                            
                    if connected:
                        self.connect_to_peer(peer_ip, peer_port)           
                    self.send_infohash(peer_ip, peer_port, hashcode)            
                for peer_ip, peer_port in peer_list:
                    if not any(peer_ip == flag[0] for flag in downloadFile.flag):
                        downloadFile.flag.append([peer_ip, False])                       
                download = self.wait_for_mapping_size(hashcode, peer_list)
                self.create_or_update_bfm(hashcode)
                 
                if download:
                    print(f"Start downloading")
                threads = []    
                
                while downloadFile.piece_idx_not_downloaded != []:
                    plan_download = self.rarest_first_with_blocks(downloadFile.bitFieldMessage, downloadFile.meta_info.numOfPieces, PIECE_LENGTH, BLOCK_LENGTH, downloadFile.meta_info_from_torrent.length, downloadFile.meta_info_from_torrent.info_hash)
                   
                    break_out = False
                    for peer_ip, peer_port in peer_list:
                        break_out = False
                        for plan in plan_download:
                            if break_out:  
                                break
                            else:
                                piece_index = plan["piece"]
                           
                                flag = None
                                while flag is None or flag:  
                                    flag = next((f[1] for f in downloadFile.flag if f[0] == peer_ip), None)
                                    time.sleep(0.1) 
                                for block_index, peer_ip2 in plan["block_to_peer"].items():
                                           
                                    if peer_ip == peer_ip2:
                                         
                                        temp_list = list(self.sent_requests_queue.queue)
                                        if not any(req['hashcode'] == hashcode and
                                                    req['pieceinfo'] and
                                                    req['pieceinfo']['pieceindex'] == piece_index and
                                                    req['pieceinfo']['offset'] == block_index * BLOCK_LENGTH
                                                    for req in temp_list):                                                                            
                                            thread = threading.Thread(target=self.download_block, args=(peer_ip, peer_port, hashcode, piece_index, block_index * BLOCK_LENGTH ))
                             
                                            
                                            downloadFile.update_flag(peer_ip)
                                   
                                            threads.append(thread)
                                            thread.start()   
                                      
                                            break_out = True
                                            break   
                                        else:
                                            continue         
          
                
                try:
                    print(f"Finish downloading {downloadFile.meta_info.fileName} ")     
                    temp_list = list(self.sent_requests_queue.queue)
                    for request in temp_list:
                        if request['hashcode'] == hashcode:
                            with self.lock:
                                self.sent_requests_queue.queue.remove(request)   
                    for entry in self.file_info_array:
                        if entry['infohash'] == hashcode:
                            with self.lock:
                                self.file_info_array.remove(entry)
                                break
                    
                    Folder_FileShare = self.get_file_share_folder()
                    Folder_FileHave = self.get_peer_respo_folder()
                    
                    
                    file_folder = os.path.join(Folder_FileShare, os.path.splitext(downloadFile.meta_info.fileName)[0])
                    if not os.path.exists(file_folder):
                        print("noooooooooooooooooo1")  
        
                    file_path = os.path.join(file_folder, downloadFile.meta_info.fileName)       
                    if not os.path.exists(file_path) :
                        print('nooooooooooooooooo2')
                    
                    
                    shutil.move(file_path, Folder_FileHave)
                    print(f"Move {downloadFile.meta_info.fileName} to folder peer_respo")
                except Exception as e:
                    print(f"Đã xảy ra lỗi không xác định sau khi tai file: {e}")
                    
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
                data = peer_socket.recv(BLOCK_LENGTH *4)
         
                if not data:
                    break

                command = data[:(data.find(b":"))].decode(CODE)
                if command == "disconnect":
                    break
                
                elif command == "download":
                    message = data[(data.find(b":") + 1):].decode(CODE)
        
                
                    try:
                        hashcode, pieceindex, offset = message.split(":",2)
                        # print(f"Received request download from peer ({peer_ip}:{peer_port})")
                        # print(f"Hashcode: {hashcode}")
                        # print(f"Piece Index: {pieceindex}")
                        # print(f"Offset: {offset}")

                        self.send_block(peer_socket, hashcode, int(pieceindex), int(offset))
                    except ValueError as e:
                        #print(f"Malformed message from peer: {e}")
                        print("")
                                
                elif command == "block":
                    message = data[(data.find(b":") + 1):]
                    header, received_data = message.split(b"\n", 1)
                    header = header.decode(CODE)
                    
                    hashcode, pieceindex, offset, datalength = header.split(":")
                    pieceindex = int(pieceindex)
                    offset = int(offset)
                                    
                    receive_thread = threading.Thread(target=self.receive_block, args=(hashcode, pieceindex, offset, datalength, received_data, peer_ip))
                    receive_thread.start()
                    
                elif command == "info":
                    info_hash = data[(data.find(b":") + 1):].decode(CODE)
                    print(f"Received info_hash '{info_hash}' from peer ({peer_ip}:{peer_port})")
                    
                    self.create_or_update_bfm(info_hash)
                    with self.lock:
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
                        
                    except Exception as e:
                        print(f"Error processing bfm: {e}")
                    
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"")

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
        peer_socket.sendall(string_peer_port.encode(CODE))
        time.sleep(0.1)
        
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
            
            peer_socket.sendall(str(request_message).encode(CODE))
            time.sleep(0.1)
            
            print(f"Sent successful infohash to {peer_ip}:{peer_port}") 
        except Exception as e:
            print(f"Error sending infohash: {e}")  
    
    
    def create_or_update_bfm(self, infohash):
        with self.lock:
            
          
                   
            try:
                file_share_folder = self.get_file_share_folder()
                
                file = self.find_file_obj(infohash)
  
                file_name = file.meta_info_from_torrent.fileName
                        
                file_folder = os.path.join(file_share_folder, os.path.splitext(file_name)[0])
                if not os.path.exists(file_folder):
                    os.makedirs(file_folder)  
                self.merge_file_with_padding(file_name, file.meta_info_from_torrent.length)
                        
                file_path = os.path.join(file_folder,file_name)   
                      
                a = file.meta_info_from_torrent.filePath
                b = f"{self.peerOwnRes}"+f"{file.meta_info_from_torrent.fileName}"
                
        
                temp = file.flag
                if os.path.exists(a):
                    file.__init__(file_path, a) 
                    
                elif  os.path.exists(b):
                    file.__init__(file_path, b) 
                else:
                    print("]]]]]]]]]]]]]]]]]]]]]]]]]]]")
                file.flag = temp
                        
                        
                file._initialize_piece_states()

            
            except Exception as e:
                    print(f"Error create_or_update_bfm: {e}")  
            
    def send_bfm(self, conn, infohash):   
        try:               
            file = self.find_file_obj(infohash)
            bfm = f"bfm:{infohash}:{file.bitFieldMessage}"
            conn.sendall(bfm.encode(CODE))
            time.sleep(0.1)
        except Exception as e:
                print(f"Error send_bfm: {e}")  
                
                
    def merge_file_with_padding(self, file_name, total_size):
        file_share_folder = self.get_file_share_folder()
        
        if not os.path.exists(file_share_folder):
            print("Fileshare' folder does not exist")
            return None

        folder = os.path.join(file_share_folder, os.path.splitext(file_name)[0])
        if not os.path.exists(folder) or not os.path.isdir(folder):
            print(f"Folder '{file_name}' not found in 'Fileshare'.")
            return None
        
        # Tạo đường dẫn cho file hợp nhất
        merged_file_path = os.path.join(folder, file_name)
        try:
            if not os.path.exists(merged_file_path):
                with open(merged_file_path, 'wb') as merged_file:
                    merged_file.truncate(total_size)  # Tạo file với kích thước `total_size`

            # Ghi dữ liệu từng piece vào đúng vị trí
            num_pieces = (total_size + PIECE_LENGTH - 1) // PIECE_LENGTH
            for piece_index in range(0, num_pieces ): 
                piece_name = f"piece{piece_index}"
                piece_path = os.path.join(folder, piece_name)
                offset = (piece_index) * PIECE_LENGTH  
                
                if os.path.exists(piece_path):  
                    with open(piece_path, 'rb') as piece_file:
                        piece_data = piece_file.read()  
                        
                        with open(merged_file_path, 'r+b') as merged_file:
                            merged_file.seek(offset)
                            merged_file.write(piece_data)
        except Exception as e:
            print(f"An error occurred while merging files: {e}")
             
    def download_block(self, peer_ip, peer_port, hashcode, pieceindex, offset):
            try:
                if (peer_ip, peer_port) in self.connected_client_addr_list:
                    index = self.connected_client_addr_list.index((peer_ip, peer_port))
                    peer_socket = self.connected_client_conn_list[index]
                else:
                    print(f"No connection found with peer {peer_ip}:{peer_port}.")
                    return
                request_message = f"download:{hashcode}:{pieceindex}:{offset}"
                peer_socket.sendall(request_message.encode(CODE))
                time.sleep(0.1)
                
            
                
            except socket.timeout:
                print(f"Request to {peer_ip}:{peer_port} timed out.")
            except Exception as e:
                print(f"Error requesting piece: {e}")  
                


    def find_file_obj(self, hashcode):
        for file in self.fileInRes:      
            if file.meta_info_from_torrent.info_hash == hashcode:
                return file 
        
        raise Exception(f"File with hashcode '{hashcode}' not found in the resource list.")
        
      
                
                
    def send_block(self, conn, hash_code, pieceindex, offset):
        
        try:
            file = self.find_file_obj(hash_code)
            if not file:
                print(f"File for hash_code {hash_code} not found.")
                return
            
            File_name = file.meta_info.fileName
            Folder_path = os.path.join(self.get_file_share_folder(), os.path.splitext(File_name)[0])
            Piece_path = os.path.join(Folder_path, f"piece{pieceindex}")
            
            with open(Piece_path, "rb") as f:
                f.seek(offset)
                data_to_send  = f.read(BLOCK_LENGTH)
                data_length = len(data_to_send)
            
            header = f"block:{hash_code}:{pieceindex}:{offset}:{data_length}"
            
            message = header.encode(CODE) + b"\n" + data_to_send
            conn.sendall(message)
            time.sleep(0.1)

        except FileNotFoundError:
            print(f"piece for hash_code {hash_code} and pieceindex {pieceindex} not found.")
            error_message = f"not_receive_piece:piece for hash_code '{hash_code}' and pieceindex '{pieceindex}' not found."
            conn.sendall(error_message.encode(CODE))
        except Exception as e:
            print(f"Error sending piece {pieceindex} (offset: {offset}) for hash_code {hash_code}: {e}")
            
        
    def receive_block (self, hashcode, PieceIndex, Offset, Length, Data, peer_ip):
        try:
            File_Share_Folder = self.get_file_share_folder()
            filedownload = self.find_file_obj(hashcode)
            File_name = filedownload.meta_info.fileName
            Folder_path = os.path.join(File_Share_Folder, os.path.splitext(File_name)[0])
            piece_path = os.path.join(Folder_path, f"piece{PieceIndex}")
            if not os.path.exists(piece_path):
                with open(piece_path, "wb") as file:
                    pass  # Tạo file rỗng nếu chưa có
            if len(Data) != int(Length):
                raise ValueError(f"Data length mismatch: expected {Length}, got {len(Data)}")
            
            with open(piece_path, "r+b") as file:
                file.seek(Offset)  
                file.write(Data)  
          
            self.create_or_update_bfm(hashcode)
            
            with self.lock:     
                self.sent_requests_queue.put({
                    "hashcode": hashcode,
                    "pieceinfo": {
                        "pieceindex": PieceIndex,
                        "offset": Offset
                    }
                })  
                
               
            filedownload.update_flag(peer_ip)
                    
                               
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except ValueError as e:
            print(f"Data error: {e}")
            print(f"Request again")
            
            filedownload.update_flag(peer_ip)
        except Exception as e:
            print(f"Error in receive_block: {e}")   
            
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
        time.sleep(0.1)
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
        time.sleep(0.1)
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
            #if metainfo.fileName not in self.processedFileName:
          
                
                
                metainfo_string = ":".join([
                    metainfo.fileName,
                    str(metainfo.length),
                    str(metainfo.pieceLength),
                    ",".join(metainfo.piecesList),  # Ghép danh sách `piecesList` bằng dấu phẩy
                    metainfo.pieces,  # Giả sử đây là chuỗi, nếu không cần chuyển đổi thêm
                    str(metainfo.numOfPieces),
                    metainfo.info_hash  # Giả sử đây là chuỗi, nếu không cần chuyển đổi thêm
                ])
                try:
                    header = "send_metainfo:"
                    conn.sendall(header.encode(CODE))
                    time.sleep(0.1) 
                    chunk_size = 4096
                    num_chunks = len(metainfo_string) // chunk_size + (1 if len(metainfo_string) % chunk_size != 0 else 0)
                    
                    for i in range(num_chunks):
                        chunk = metainfo_string[i * chunk_size: (i + 1) * chunk_size]
                        encoded_data = chunk.encode(CODE)
                        conn.sendall(encoded_data)
                  
                        time.sleep(0.1)
                        
                    footer = "stop_metainfo:"
                    conn.sendall(footer.encode(CODE))
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
    def merge_piece(self, file_name):
        import os
        
        file_have_folder = self.get_peer_respo_folder()
        file_share_folder = self.get_file_share_folder()
        
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


    def get_peer_respo_folder(self):
        """Lấy đường dẫn đến thư mục peer_respo."""
        root_folder = os.getcwd() 
        file_have_folder = os.path.join(root_folder, "peer_respo")
        
        if not os.path.exists(file_have_folder):
            print(f"'peer_respo' folder does not exist in the project root: {root_folder}")
            return None
        return file_have_folder
    
    def get_file_share_folder(self):
        """Lấy đường dẫn đến thư mục FileShare."""
        root_folder = os.getcwd() 
        file_share_folder = os.path.join(root_folder, "FileShare")
        if not os.path.exists(file_share_folder):
            print(f"'Fileshare' folder does not exist in the project root: {root_folder}")
            return None
        return file_share_folder
    
    def rarest_first_with_blocks(self, my_bitfield, num_pieces, piece_size, block_size, total_file_size, hashcode):
    # Tạo bảng đếm số lần xuất hiện của từng piece
        piece_count = [0] * num_pieces
        piece_to_peer_map = {i: [] for i in range(num_pieces)}

        # Lọc chỉ các file_info có hashcode tương ứng
        relevant_file_info = [file_info for file_info in self.file_info_array if file_info["infohash"] == hashcode]

        # Tính toán thông tin từ relevant_file_info
        for file_info in relevant_file_info:
            for peer_ip, bitfield in file_info["mapping"].items():
                for i, bit in enumerate(bitfield):
                    if bit == '1':
                        piece_count[i] += 1
                        piece_to_peer_map[i].append(peer_ip)

    # Lọc các pieces mà client A chưa có
        missing_pieces = [i for i, bit in enumerate(my_bitfield) if bit == '0']
        
        available_pieces = [i for i, bit in enumerate(my_bitfield) if bit == '1']
        
        
        temp_list = list(self.sent_requests_queue.queue)
        for request in temp_list:
            if request['hashcode'] == hashcode:
                if request['pieceinfo']['pieceindex'] in available_pieces:
                    with self.lock:
                        self.sent_requests_queue.queue.remove(request)  
                    
                    
        # Sắp xếp các pieces theo độ hiếm (rarest first)
        rarest_pieces = sorted(missing_pieces, key=lambda x: piece_count[x])

    # Gán blocks cho các peers
        download_plan = []
        for piece in rarest_pieces:
            peers_with_piece = piece_to_peer_map[piece]
            if not peers_with_piece:
                continue  # Không có peer nào có piece này, bỏ qua

            # Tính toán kích thước thực tế của piece (xử lý piece cuối cùng)
            piece_start = piece * piece_size
            if piece_start + piece_size > total_file_size:
                actual_piece_size = total_file_size - piece_start
            else:
                actual_piece_size = piece_size

            # Tính số blocks của piece hiện tại
            num_blocks = (actual_piece_size + block_size - 1) // block_size

            block_to_peer = {}
            for block_index in range(num_blocks):
                # Chọn peer theo round-robin
                peer = peers_with_piece[block_index % len(peers_with_piece)]
                block_to_peer[block_index] = peer

            # Thêm piece vào kế hoạch tải
            download_plan.append({
                "piece": piece,
                "actual_piece_size": actual_piece_size,  # Kích thước thật của piece
                "block_to_peer": block_to_peer
            })

        return download_plan

   
if __name__ == "__main__":
    my_peer = peer()
    try:
        peer_thread = Thread(target=my_peer.client_program)
        peer_thread.start()

        while True:
            command = input("Peer> ")
            if command == "test":
                print("The program is running normally.")
            elif command.startswith("tr"):
                server_host = "192.168.1.18" 
                server_port = 22236 
                my_peer.connect_to_tracker(server_host, server_port)
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
            elif command == "get":
                my_peer.getFileInRes()
            elif command == "send": #! WORKING ON THIS
                my_peer.send_metainfo_to_tracker(server_host, server_port)
            elif command == "have": #! WORKING ON THIS
                flag = True
                torrent_path = input("Enter torrent path: ")
                
                current_path = os.getcwd()
                full_path = os.path.join(current_path, torrent_path)
                if not os.path.isfile(full_path):
                    flag = False
                    print("You dont have the torrent file of this file")   
                else:                          
                    downloadfile = File("",torrent_path)   
                
                    hash_info = downloadfile.meta_info_from_torrent.info_hash
                    for file in my_peer.fileInRes:     
                        if hash_info == file.meta_info_from_torrent.info_hash:
                            flag = False
                            print("The file you want already exists in the list, please try again")                             
                            break
                        
                if flag:
                    my_peer.fileInRes.append(downloadfile)
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
        file_share_folder = my_peer.get_file_share_folder()
        for filename in os.listdir(file_share_folder):
            file_path = os.path.join(file_share_folder, filename)
            try:
                shutil.rmtree(file_path)

            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
                
        current_path = os.getcwd()
        for item in os.listdir(current_path):
            folder_path = os.path.join(current_path, item)
 
            if os.path.isdir(folder_path) and item.startswith("my_own_respo_"):
                try:
                    shutil.rmtree(folder_path)
                except Exception as e:
                    print(f"Failed to delete {folder_path}: {e}")
                    
    my_peer.shutdown_peer()
    peer_thread.join(timeout=5)
    sys.exit(0)
