import socket
import pickle
import time
import os
import argparse
from threading import Thread, Event
# global
client_list = []
filename1 = "file.png"
client_port = 5000
stop_event = Event()

# Get client IP
def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Not for communication with clients but simply to discover the server’s outward-facing IP address.
    try:
       s.connect(('8.8.8.8',1))
       ip = s.getsockname()[0]
       print(ip)
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip

def start_listener():
    client_ip = get_host_default_interface_ip()
    client_socket = socket.socket()
    client_socket.bind((client_ip, client_port))
    client_socket.listen(10)
    print(f"Listening for peer connections on port {client_port}")
    
    # client_socket = socket.socket()
    # client_socket.bind(("0.0.0.0", client_port))
    # client_socket.listen(10)
    # print(f"Listening for peer connections on port {client_port}")
    
    while True:
        conn, addr = client_socket.accept()
        receive_request(conn, addr)
    # while True:
    #     try:
    #         conn, addr = client_socket.accept()
    #         print(f"Connected by peer at {addr}")
    #         threads = Thread(target=receive_request, args=(conn, addr))
    #         threads.start()
    #     except RuntimeError:
    #         print("Error: Could not create thread - the interpreter might be shutting down.")
    #         break

def receive_request(conn, addr):
    print(f"Connection established with {addr}")
    
    # Nhận yêu cầu từ peer, tên file cần tải
    filename = conn.recv(1024).decode()  # Nhận tên file từ client
    if(filename == filename1):print("fffffffffffffffffffffffffffff")
    if filename:
        print(f"Client requested file: {filename}")
        send_file(conn, filename)  # Gửi file khi nhận yêu cầu từ client
    else:
        print("No file requested by client.")
    
    conn.close()

def send_file(conn, filename):
    # current_directory = os.getcwd()  # Lấy thư mục hiện tại
    # print(f"Current directory: {current_directory}")
    # print("Files in the current directory:")
    # for file in os.listdir(current_directory):
    #     print(file)
    # Đọc nội dung file
    #filename3="file.png"
    
    try:
        with open(filename, "rb") as f:
            file_data = f.read()

        # Tính toán kích thước của file
        file_size = len(file_data)

        # Gửi kích thước file trước, dùng 4 byte để chứa số nguyên
        conn.sendall(file_size.to_bytes(4, 'big'))

        # Gửi file
        conn.sendall(file_data)
        print(f"File {filename} has been sent to the client.")

    except FileNotFoundError:
        print(f"File {filename} not found.")
        conn.sendall(b"ERROR")  # Gửi tín hiệu lỗi nếu không tìm thấy file
        
def download_file(conn, filename):
    #request
    conn.sendall(filename.encode())  # Gửi tên file dưới dạng bytes
    
    file_size_data = conn.recv(4)  # Nhận kích thước file (4 byte) từ peer
    file_size = int.from_bytes(file_size_data, 'big') 
    
    print(f"File size to receive: {file_size} bytes")
        
    received_size = 0
    with open(f"received_file.png", "wb") as f:  # Mỗi client sẽ lưu file khác nhau
        while True:
            data = conn.recv(1024)  # Nhận 1024 byte dữ liệu mỗi lần
            if not data:
                break  
            f.write(data) 
            
            received_size += len(data)  

             # Cập nhật tiến trình tải
            percent = (received_size / file_size) * 100
            print(f"\rDownload progress: {percent:.2f}%", end="") 
    print("\nFile download complete.")
    
    
def client_program():
    thread = Thread(target=start_listener, args=())
    thread.start()

    # Demo sleep time for fun (dummy command)
    # for i in range(0,3):
    #     print('Let me, ID={:d} sleep in {:d}s'.format(tid,3-i))
    #     time.sleep(1)
 
    # print('OK! I am ID={:d} done here'.format(tid))

# Connect to the Tracker
def connect_to_tracker(server_host, server_port):
    tracker_socket = socket.socket()
    tracker_socket.connect((server_host, server_port))

    # Client metainfo
    client_ip, client_port = tracker_socket.getsockname()
    print(f"Client IP: {client_ip}, Client Port: {client_port}")

    # Receive the clients list from the Tracker
    client_list = tracker_socket.recv(4096)
    client_list = pickle.loads(client_list)
    
    return client_list
  

# Connect to other peers
def connect_to_peers(client_list):
    filename = input("Enter the name of the file you want to download: ")
    for peer_ip, peer_port in client_list:
        try:
            peer_socket = socket.socket()
            peer_socket.connect((peer_ip, client_port))
            print(f"Connected to peer {peer_ip}:{client_port}")
            download_file(peer_socket, filename)

        except ConnectionRefusedError:
            print(f"Could not connect to peer {peer_ip}:{client_port}")
            
    # command = input("nhập lệnh download để download: ")
    # if command.lower() == "download":
    
    
      

def connect_server(threadnum, server_host, server_port):
    # Create "threadnum" of Thread to parallelly connnect
    threads = [Thread(target=client_program, args=(i, server_host, server_port)) for i in range(0,threadnum)]
    [t.start() for t in threads]
    # TODO: wait for all threads to finish
    [t.join() for t in threads]


def client_terminal():
    print("Client Terminal started.")
    while True:
        command = input("> ")
        if command == "test":
            print("The program is running normally.")
        elif command.startswith("connect_tracker"):
            parts = command.split()
            if len(parts) == 3:
                server_host = parts[1]
                try:
                    server_port = int(parts[2])
                    client_list= connect_to_tracker(server_host, server_port)
                except ValueError:
                    print("Invalid port.")
            else:
                print("Usage: connect_tracker <IP> <Port>")
        elif command == "start":
            connect_to_peers(client_list)
        elif command == "exit":
            print("Exiting Tracker Terminal.")
            stop_event.set()
            break
        
if __name__ == "__main__":
    # python3 client_1.py --server-ip 192.168.1.7 --server-port 22236 --client-num 1
    # parser = argparse.ArgumentParser(
    #                     prog='Client',
    #                     description='Connect to pre-declard server',
    #                     epilog='!!!It requires the server is running and listening!!!')
    # parser.add_argument('--server-ip')
    # parser.add_argument('--server-port', type=int)
    # parser.add_argument('--client-num', type=int)
    # args = parser.parse_args()
    # server_host = args.server_ip
    # server_port = args.server_port
    # cnum = args.client_num
    # connect_server(cnum, server_host, server_port)
    
    thread_1 = Thread(target=client_program)
    thread_1.start()
    
    try:
        client_terminal()
    except KeyboardInterrupt:
        stop_event.set()