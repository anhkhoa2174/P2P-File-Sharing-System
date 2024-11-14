import socket
import threading
import os
import tool
from file import File
import random
from threading import Thread

PEER_IP = tool.get_host_default_interface_ip()
LISTEN_DURATION = 5
PORT_FOR_PEER= random.randint(12600, 22000)
CODE = 'utf-8'

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

         # A socket for listening from other peers in the network
        self.peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peerSocket.bind((self.peerIP, self.portForPeer))
        
         # A socket for listening from server only in the network is created
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((self.peerIP, self.portForTracker))
        print(f"a peer with IP address {self.peerIP}, ID {self.portForTracker} has been created")


    @property # This creates an own respo for peer to save metainfo file
    def peerOwnRes(self):
        peerOwnRes = "my_own_respo_" + str(self.peerID)
        os.makedirs(peerOwnRes, exist_ok=True)
        peerOwnRes += "/"
        return peerOwnRes
    
    def getFileInRes(self) -> list:
        ownRespository = os.listdir("peer_respo")
        files = []
        if len(ownRespository) == 0:
            return files
        else: 
            for name in ownRespository:
                if(os.path.getsize("peer_respo/" + name) == 0):
                    os.remove("peer_respo/" + name)
                else:
                    # files.append(File(self.peerOwnRes+name))


                    # Testing creating metainfo
                    file_obj = File("peer_respo/"+name)
                    files.append(file_obj)
                    
                    # Get metainfo and save into a text file
                    self.save_metainfo_to_txt(file_obj.meta_info)
        return files
    def save_metainfo_to_txt(self, metainfo):
        # The path to txt file that saves metainfo of a specific file
        file_path = os.path.join(self.peerOwnRes, f"{metainfo.fileName}_metainfo.txt")
        
        # Write metainfo into file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"File Name: {metainfo.fileName}\n")
            file.write(f"File Length: {metainfo.length} bytes\n")
            file.write(f"Piece Length: {metainfo.pieceLength} bytes\n")
            file.write(f"Number of Pieces: {int(metainfo.numOfPieces)}\n")
            file.write(f"SHA-1 Hashes of Pieces: {metainfo.pieces.hex()}\n")
        
        print(f"Metainfo for {metainfo.fileName} has been saved to {file_path}")


peer_instance = peer()


peer_instance.getFileInRes()
 

