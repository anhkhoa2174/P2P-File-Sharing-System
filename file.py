import os
import math
import tool
import os
from tool import *



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
    
        
    

