import os
import math
import tool
import hashlib
import os
from tool import *

def split_into_pieces(file_path, piece_length):
#    """Split the file into pieces of the given length and return a list of pieces."""
    pieces = []
    with open(file_path, 'rb') as f:
        while True:
            piece = f.read(piece_length)
            if not piece:
                break
            pieces.append(piece)
    return pieces

def sha1_hash(piece):
#   """Compute SHA-1 hash of a piece."""
    sha1 = hashlib.sha1()
    sha1.update(piece)
    return sha1.digest()


class Metainfo:
    def __init__(self, path):
        self.fileName = os.path.basename(path)
        self.length =  os.path.getsize(path)
        self.pieceLength = PIECE_LENGTH

        pieces = split_into_pieces(path, self.pieceLength)
        self.pieces = b''.join(sha1_hash(piece) for piece in pieces).hex()

        self.numOfPieces = math.ceil(self.length/self.pieceLength)
        
      
class File:
    def __init__(self, path):
        self.meta_info = Metainfo(path)
        self.piece_idx_downloaded = []
        self.piece_idx_not_downloaded = []
        self.downloadedBytes = []
    
        
    

