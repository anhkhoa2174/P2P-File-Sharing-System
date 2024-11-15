import socket
import time
import argparse
import mmap
from threading import Thread

def new_server_incoming(conn, addr):
    print(addr)

def thread_server(host, port):
    print("Thread server listening on: {}:{}".format(host, port))
    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)
    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_server_incoming, args=(addr, conn))
        nconn.start()

def thread_client(id, serverip, serverport, peerip, peerport):
    print("Thread ID {:d} connecting to {}:{:d}".format(id, serverip, serverport))
    
def thread_agent(time_fetching, filepath):
    print(filepath)

    with open(filepath, mode="w+", encoding="utf-8") as f:
        f.truncate(100)
        f.close()
    
    while True:
        with open(filepath, mode="r+", encoding="utf-8") as file_obj:
            with mmap.mmap(file_obj.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_obj:
                text = mmap_obj.read()
                print(text.decode("utf-8"))
            file_obj.close()
        
        with open(filepath, mode="w+", encoding="utf-8") as wfile_obj:
            wfile_obj.truncate(0)
            wfile_obj.truncate(100)
            with mmap.mmap(wfile_obj.fileno(), length=0, access=mmap.ACCESS_WRITE) as mmap_wobj:
                text = f"done"
                mmap_wobj.write(text.encode("utf-8"))
            
            wfile_obj.close()
        
        time.sleep(time_fetching)
    
    exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='node', description='Node connect to predeclared server', epilog='<-- !!! It requires the server is running and lisstening !!!')
    parser.add_argument('--server-ip')
    parser.add_argument('--server-port', type=int)
    parser.add_argument('--agent-path')

    args = parser.parse_args()
    serverip = args.server_ip
    serverport = args.server_port
    agentpath = args.agent_path

    peerip = get_host_default_interface_ip()
    peerport = 33357
    tserver = Thread(target=thread_server, args=(peerip, 33357))
    tclient = Thread(target=thread_client, args=(1, serverip, serverport, peerip, peerport))
    tagent = Thread(target=thread_agent, args=(2, agentpath))

    tserver.start()

    tclient.start()
    tclient.join()

    tagent.start()

    tserver.join()