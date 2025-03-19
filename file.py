import socket
import threading
import math
import tool
import os
from tool import *
#from piece import *
from threading import Thread
from tool import *


PIECE_LENGTH = 1024 * 512  # 16KB mỗi piece (tùy chỉnh theo nhu cầu)
BLOCK_LENGTH = 1024 * 8

def sha1_hash(data):
    import hashlib
    return hashlib.sha1(data).digest()

def split_into_pieces(file_path, piece_length):
    with open(file_path, 'rb') as f:
        while True:
            piece = f.read(PIECE_LENGTH)
            if not piece:
                break
            yield piece

class Metainfo:
    def __init__(self, path):
        if path:
            self.fileName = os.path.basename(path)
            self.length = os.path.getsize(path)
            self.pieceLength = PIECE_LENGTH

            pieces = split_into_pieces(path, self.pieceLength)
            self.piecesList = [sha1_hash(piece).hex() for piece in pieces] #piece list chứa hashcode của từng piece
            self.pieces = ''.join(self.piecesList)
            self.filePath = path
            self.numOfPieces = math.ceil(self.length / self.pieceLength)

            # Tạo info_hash từ metadata
            info_dict = {
                "fileName": self.fileName,
                "length": self.length,
                "pieceLength": self.pieceLength,
                "pieces": self.pieces
            }
            self.info_hash = hashlib.sha1(str(info_dict).encode()).hexdigest()
        else:
            self.fileName = None
            self.length = None
            self.pieceLength = None
            self.piecesList = None
            self.pieces = None
            self.info_hash = None
            self.numOfPieces = None
            self.filePath = None

class MetainfoTorrent:
    def __init__(self, torrent_txt_path):
        if torrent_txt_path:
            self._parse_torrent_file(torrent_txt_path)
        else:
            self.fileName = None
            self.length = None
            self.pieceLength = None
            self.piecesList = None
            self.pieces = None
            self.info_hash = None
            self.numOfPieces = None
            self.filePath = None

    def _extract_value(self,content, key):

        for line in content.splitlines():
            if line.startswith(key):
                return line.split(':', 1)[1].strip()  # Tách giá trị sau dấu ":" và loại bỏ khoảng trắng.
        raise ValueError(f"Key '{key}' not found in the content.")

    def _parse_torrent_file(self, torrent_txt_path):
        with open(torrent_txt_path, 'r') as f:
            content = f.read()
        
            # Trích xuất thông tin cơ bản từ tệp torrent
            self.fileName = self._extract_value(content, 'File Name')
            self.length = int(self._extract_value(content, 'File Length').split()[0])  
            self.pieceLength = int(self._extract_value(content, 'Piece Length').split()[0])
            self.numOfPieces = int(self._extract_value(content, 'Number of Pieces'))
        
            # Trích xuất chuỗi các hash SHA-1 của từng mảnh
            pieces_hex_str = self._extract_value(content, 'SHA-1 Hashes of Pieces')
        
            # Lưu hash của từng mảnh vào self.piecesList
            self.piecesList = [pieces_hex_str[i:i+40] for i in range(0, len(pieces_hex_str), 40)]
    
            # Nối các hash của từng mảnh lại với nhau để tạo ra self.pieces
            self.pieces = ''.join(self.piecesList)
            
            self.filePath = torrent_txt_path

            # Tạo info hash từ metadata (fileName, length, pieceLength, piecesList)
            info_dict = {
                "fileName": self.fileName,
                "length": self.length,
                "pieceLength": self.pieceLength,
                "pieces": ''.join(self.piecesList)
            }
            self.info_hash = hashlib.sha1(str(info_dict).encode()).hexdigest()
        
class File:
    def __init__(self, path, torrent_txt_path):
        self.meta_info = Metainfo(path)
        self.meta_info_from_torrent = MetainfoTorrent(torrent_txt_path)
        self.lock = threading.Lock()
        self.piece_idx_downloaded = []  
        self.piece_idx_not_downloaded = []
        self.downloadedBytes = self.meta_info.length if self.meta_info.length else 0
        self.sentMetaInfo = False #! WORKING ON THIS
        self.bitFieldMessage = []
        self.filePath = path
        #self.piece_List = [] 
        self.flag = []
        
        
    def _initialize_piece_states(self):
        with self.lock:     
            self.piece_idx_downloaded = ["placeholder"]  
            self.piece_idx_not_downloaded = ["placeholder"]
            pieces_from_file = list(split_into_pieces(self.filePath, self.meta_info.pieceLength))
            
            for idx, piece in enumerate(pieces_from_file):
                piece_hash = sha1_hash(piece).hex()
                if piece_hash in self.meta_info_from_torrent.pieces:
                    
                    self.piece_idx_downloaded.append(idx)
                else:
                    self.piece_idx_not_downloaded.append(idx)

            self._create_bit_field_message()

        self.piece_idx_downloaded.remove("placeholder")
        self.piece_idx_not_downloaded.remove("placeholder")
        
    def update_flag(self, ip):
        with self.lock:  
            found = False
            for flag in self.flag:
                
                if flag[0] == ip:
                    flag[1] = not flag[1]
                    found = True
                    return

            if not found:
                self.flag.append([ip, False])  # Thêm phần tử mới nếu không tìm thấy IP trong danh sách
            
    def _create_bit_field_message(self):
        self.bitFieldMessage = []
        bit_field = ['1' if idx in self.piece_idx_downloaded else '0' for idx in range(self.meta_info.numOfPieces)]
        self.bitFieldMessage = ''.join(bit_field)

    def print_file_information(self): #! DUNG DE TEST
        print(f"Downloaded Pieces Index: {self.piece_idx_downloaded}")
        print(f"Not Downloaded Pieces Index: {self.piece_idx_not_downloaded}")
        print(f"Downloaded Bytes: {self.downloadedBytes}")
        print(f"Bitfield Message: {self.bitFieldMessage}")
        
    # split a file to share     
    def split_file(self, file_name, file_size, piece_size):
 
        # Đường dẫn các folder trong dự án
        root_folder = os.getcwd()  # Thư mục gốc của project
        file_have_folder = os.path.join(root_folder, "peer_respo")
        file_share_folder = os.path.join(root_folder, "FileShare")
        
        # Đảm bảo các folder peer_respo và Fileshare tồn tại
        if not os.path.exists(file_have_folder):
            print(f"'peer_respo' folder does not exist in the project root: {root_folder}")
            return None
        if not os.path.exists(file_share_folder):
            print(f"'FileShare' folder does not exist in the project root: {root_folder}")
            return None
        
        # Kiểm tra xem file có trong folder peer_respo không
        file_path = os.path.join(file_have_folder, file_name)
        if not os.path.exists(file_path):
            print(f"File '{file_name}' not found in 'peer_respo'.")
            return None

        # Tạo folder mới trong Fileshare với tên là file
        output_folder = os.path.join(file_share_folder, os.path.splitext(file_name)[0])
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        else :
            return None

        try:
            with open(file_path, "rb") as f: 
                num_pieces = (file_size // piece_size) + (1 if file_size % piece_size != 0 else 0)  
                
                for i in range(num_pieces):
                    # Đặt tên cho từng piece
                    piece_path = os.path.join(output_folder, f"piece{i}")
                                 
                    if(file_size <= piece_size):
                        piece_data = f.read(file_size)
                        with open(piece_path, "wb") as piece_file:
                            piece_file.write(piece_data)
                    else:     
                        if i < num_pieces-1:
                            piece_data = f.read(piece_size)
                            with open(piece_path, "wb") as piece_file:
                                piece_file.write(piece_data)
                        
                        else:
                            piece_data = f.read(file_size - piece_size * (num_pieces-1))
                            with open(piece_path, "wb") as piece_file:
                                piece_file.write(piece_data)

            return output_folder
        
        except Exception as e:
            print(f"Error splitting file '{file_name}': {e}")
            return None
        
  
