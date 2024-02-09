import socket
UDP_IP = "192.168.42.125" 
SHARED_UDP_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
sock.connect((UDP_IP, SHARED_UDP_PORT))
def loop():
    while True:
        data = sock.recv(2048)
        print(data)
if __name__ == "__main__":
    sock.send('Hello'.encode())
    loop()