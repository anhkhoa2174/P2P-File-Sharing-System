# pip install bencodepy
import bencodepy

class Metainfo:
    def __init__(self):
        self.fileName = None
        self.length = None
        self.pieceLength = None
        self.pieces = []
        self.numOfPieces = None

def parse_torrent(file_path):
    with open(file_path, 'rb') as torrent_file:
        torrent_data = bencodepy.decode(torrent_file.read())
    info = torrent_data[b'info']

    metainfo = Metainfo()
    metainfo.fileName = info[b'name'].decode('utf-8')
    metainfo.length = info[b'length']
    metainfo.pieceLength = info[b'piece length']
    pieces_data = info[b'pieces']
    metainfo.pieces = [pieces_data[i:i+20].hex() for i in range(0, len(pieces_data), 20)]
    metainfo.numOfPieces = len(metainfo.pieces)

    return metainfo

def print_metainfo(metainfo):
    print(f"File Name: {metainfo.fileName}")
    print(f"File Length: {metainfo.length} bytes")
    print(f"Piece Length: {metainfo.pieceLength} bytes")
    print(f"Number of Pieces: {metainfo.numOfPieces}")
    print(f"Pieces (SHA-1 hashes): {metainfo.pieces}")

torrent_file_path = r"C:\Users\duyhu\Downloads\test.txt.torrent"
metainfo = parse_torrent(torrent_file_path)
print_metainfo(metainfo)