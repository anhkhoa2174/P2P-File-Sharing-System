import os
import math
import tool
import os
from tool import *


PIECE_LENGTH = 1024 * 512  # 16KB mỗi piece (tùy chỉnh theo nhu cầu)

def sha1_hash(data):
    import hashlib
    return hashlib.sha1(data).digest()

def split_into_pieces(file_path, piece_length):
    with open(file_path, 'rb') as f:
        while True:
            piece = f.read(piece_length)
            if not piece:
                break
            yield piece

# class Metainfo:
#     def __init__(self, path):
#         self.fileName = os.path.basename(path)
#         self.length =  os.path.getsize(path)
#         self.pieceLength = PIECE_LENGTH

#         pieces = split_into_pieces(path, self.pieceLength)
#         self.pieces = b''.join(sha1_hash(piece) for piece in pieces).hex()

#         self.numOfPieces = math.ceil(self.length/self.pieceLength)


class Metainfo:
    def __init__(self, path):
        if path:
            self.fileName = os.path.basename(path)
            self.length = os.path.getsize(path)
            self.pieceLength = PIECE_LENGTH

            pieces = split_into_pieces(path, self.pieceLength)
            self.pieces = [sha1_hash(piece).hex() for piece in pieces]

            self.numOfPieces = math.ceil(self.length / self.pieceLength)
        else:
            self.fileName = None
            self.length = None
            self.pieceLength = None
            self.pieces = None
            self.numOfPieces = None

class MetainfoTorrent:
    def __init__(self, torrent_txt_path):
        if torrent_txt_path:
            self._parse_torrent_file(torrent_txt_path)
        else:
            self.fileName = None
            self.length = None
            self.pieceLength = None
            self.pieces = None
            self.numOfPieces = None

    def _parse_torrent_file(self, torrent_txt_path):
        with open(torrent_txt_path, 'r') as f:
            content = f.read()
            self.fileName = self._extract_value(content, 'File Name')
            self.length = int(self._extract_value(content, 'File Length').split()[0])  
            self.pieceLength = int(self._extract_value(content, 'Piece Length').split()[0])
            self.numOfPieces = int(self._extract_value(content, 'Number of Pieces'))
            
            pieces_hex_str = self._extract_value(content, 'SHA-1 Hashes of Pieces')
            self.pieces = [pieces_hex_str[i:i+40] for i in range(0, len(pieces_hex_str), 40)]
        
class File:
    def __init__(self, path, torrent_txt_path):
        self.meta_info = Metainfo(path)
        self.meta_info_from_torrent = MetainfoTorrent(torrent_txt_path)

        self.piece_idx_downloaded = []  
        self.piece_idx_not_downloaded = []
        self.downloadedBytes = self.meta_info.length if self.meta_info.length else 0
        self.sentMetaInfo = False #! WORKING ON THIS
        self.bitFieldMessage = []

    def _initialize_piece_states(self):
        if self.meta_info_from_torrent.pieces and self.meta_info.pieces:
            for idx, piece_hash in enumerate(self.meta_info.pieces):
                if piece_hash in self.meta_info_from_torrent.pieces:
                    self.piece_idx_downloaded.append(idx)
                else:
                    self.piece_idx_not_downloaded.append(idx)
            self._create_bit_field_message()

    def _create_bit_field_message(self):
        bit_field = ['1' if idx in self.piece_idx_downloaded else '0' for idx in range(self.meta_info.numOfPieces)]
        self.bitFieldMessage = ''.join(bit_field)

        
    

