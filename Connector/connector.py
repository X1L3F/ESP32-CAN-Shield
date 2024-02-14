import socket
import time
from struct import pack, unpack

UDP_IP = "0.0.0.0"  # Listen on all interfaces
SHARED_UDP_PORT = 4210
#TODO : get Ip from first message
TARGET_IP = "192.168.42.125"  # Target IP to send messages to and receive messages from

# Setup UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, SHARED_UDP_PORT))

def encode_caneth_message(can_id, data, ext_flag=False, rtr_flag=False):
    """Encode a CAN message into the CANETH format."""
    magic_id = b'ISO11898'  # CANETH protocol magic identifier
    protocol_version = 1
    frame_count = 1
    # Ensure the CAN data is 8 bytes long
    data_padded = data.ljust(8, b'\x00')
    
    # Creating the message buffer with the specified structure
    message = pack('8sBB', magic_id, protocol_version, frame_count)
    message += pack('I', can_id)
    message += pack('B', len(data))
    message += data_padded[:8]  # Ensure only the first 8 bytes are included
    message += pack('BB', ext_flag, rtr_flag)
    
    return message

def decode_caneth_message(message):
    """Decode a CANETH format message and print its components."""
    # Unpack the initial part of the message
    magic_id, protocol_version, frame_count = unpack('8sBB', message[:10])
    # Verify magic ID
    if magic_id != b'ISO11898':
        print("Invalid magic identifier")
        return
    # Unpack the CAN ID and data length
    can_id, = unpack('I', message[10:14])
    data_length, = unpack('B', message[14:15])
    # Extract the data; assuming it might not always be 8 bytes, use data_length to determine actual data
    data = message[15:15+data_length]
    # Unpack flags
    ext_flag, rtr_flag = unpack('BB', message[23:25])
    
    # Print the decoded message
    print(f"Received CANETH Message: ID={can_id}, Data={data[:8]}, Ext={bool(ext_flag)}, RTR={bool(rtr_flag)}")

def loop():
    last_send_time = time.time()
    while True:
        # Non-blocking receive
        sock.settimeout(1.0)  # Set timeout to 1 second for non-blocking receive
        try:
            data, addr = sock.recvfrom(2048)
            if addr[0] == TARGET_IP:  # Check if the message is from the target IP
                decode_caneth_message(data)
            else:
                print(f"Ignored message from {addr[0]}")
        except socket.timeout:
            pass  # No data received, just continue

        # Send a CANETH message every 5 seconds
        if time.time() - last_send_time >= 5:
            can_id = 0x123
            can_data = b'\x01\x02\x03\x04\x05\x06\x07\x08'
            message = encode_caneth_message(can_id, can_data)
            sock.sendto(message, (TARGET_IP, SHARED_UDP_PORT))
            last_send_time = time.time()
            print("Sent CANETH message")

if __name__ == "__main__":
    loop()
