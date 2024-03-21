import socket
import time
from struct import pack, unpack

#*********************************************************************************************************
def encode_caneth_message(can_id_hex, data_hex, ext_flag=False, rtr_flag=False):
    # FUNC: encoding an caneth message
    # INPUT:    can_id_hex as hex-number between  0x000 and 0x7FF 
    #           data_byte_string as byte-string; e.g.: b'\x01\x02\x03\x04\x05\xFD\xFE\xFF'
    # RETURN: message as string

    magic_id = b'ISO11898'  # CANETH protocol magic identifier
    protocol_version = 1
    frame_count = 1

    # Ensure the CAN data is 8 bytes long
    data_padded = data_hex.ljust(8, b'\x00')
        
    # Creating the message buffer with the specified structure
    message = pack('8sBB', magic_id, protocol_version, frame_count)
    message += pack('I', can_id_hex)
    message += pack('B', len(data_hex))
    message += data_padded[:8]  # Ensure only the first 8 bytes are included
    message += pack('BB', ext_flag, rtr_flag)
        
    return message

#*********************************************************************************************************
def decode_caneth_message(message):
    # FUNC: decoding an caneth message
    # INPUT:    can_id_hex as hex-number between  0x000 and 0x7FF 
    #           data_byte_string as byte-string; e.g.: b'\x01\x02\x03\x04\x05\xFD\xFE\xFF'
    # RETURN: dictionary

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
    
    # Create a dictionary with the decoded message components
    decoded_message = {
        "ID": can_id,
        "Data": data[:8],
        "Ext": bool(ext_flag),
        "RTR": bool(rtr_flag)
    }
    # Print the decoded message
    #print(f"Received CANETH Message: ID={can_id}, Data={data[:8]}, Ext={bool(ext_flag)}, RTR={bool(rtr_flag)}")
    
    return decoded_message
# Test status: successfull tested

#*********************************************************************************************************
def convert_to_binary_string(input_string):
    # FUNC: converting a string to a binary-string
    # INPUT: input_string as string; e.g.: "01 02 03 04 05 FD FE FF"
    # RETURN: binary_string

    print("INPUT: \t", input_string)
    hex_string = input_string.replace(' ', '')  # removing spaces
    if len(hex_string) % 2 != 0:    # catching error due to invalid hex_string length  
        hex_string = hex_string[:-1] + '0' + hex_string[-1]
    hex_string = hex_string[:16]  
    print("HEX: \t",hex_string)
    binary_string = bytes.fromhex(hex_string)
    print("BINARY-HEX: \t",binary_string)

    return binary_string
# Test status: successfull tested

#*********************************************************************************************************
class connector:
    def __init__(self):

        self.target_IP = "192.168.0.240" # Target IP to send messages to and receive messages from
        self.UDP_IP = "0.0.0.0"  # Listen on all interfaces
        self.shared_UDP_port = 4210
        self.recieve_flag = True

        # setup UDP socket with default values
        self.update_UDP_socket(self.UDP_IP)
    
    def update_UDP_socket(self, input_UDP_IP):
        # FUNC: updating the UDP socket with the new UDP_IP the connector should listen
        # INPUT: input_UDP_IP as string;     e.g.: "0.0.0.0"
        # RETURN: ---
        self.UDP_IP = input_UDP_IP

        # updating UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.shared_UDP_port))
    
    def updated_target_IP(self, input_target_IP):
        # FUNC: updating the target IP
        # INPUT: ininput_target_IP as string;     e.g.: "192.168.0.240"
        # RETURN: ---
        self.target_IP = input_target_IP

    def send_message(self, input_can_id_hex, input_can_data_hex):
        # FUNC: sending a caneth message
        # INPUT:    input_can_id_hex as hex-number;     e.g.: 0x123
        #           input_can_data_hex as byte-string;  e.g.: b'\x01\x02\x03\x04\x05\xFH\xFG\xFF'
        # RETURN: ---

        encoded_message = encode_caneth_message(input_can_id_hex, input_can_data_hex)
        self.sock.sendto(encoded_message, (self.target_IP, self.shared_UDP_port))
    # Test status: successfull tested
    
    def recieve_message(self):
        # FUNC: recieving a caneth message and decoding it
        # INPUT: ---
        # RETURN: message
        
        return_flag = 0
        return_message = None

        if True == self.recieve_flag:
            self.sock.settimeout(1.0)  # Set timeout to 1 second for non-blocking receive
            try:
                rec_data, addr = self.sock.recvfrom(2048)
                if addr[0] == self.target_IP:  # Check if the message is from the target IP
                    decoded_message = decode_caneth_message(rec_data)
                    return_message = decoded_message
                    return_flag = 1
                else:
                    print(f"Ignored message from {addr[0]}")
                    return_flag = 2
            except socket.timeout:
                return_flag = 0
                pass  # No data received, just continue

        return return_flag, return_message
    # Test status: successfull tested
    
    def toggle_recieving_message(self, input_rec_flag):
        # FUNC: toggeling to recieve messages on and off
        # INPUT: input_rec_falg as boolean
        # RETURN: ---
        self.recieve_flag =  input_rec_flag
        if True == self.recieve_flag:
            print("Recieving messages enabled")
        elif False == self.recieve_flag:
            print("Recieving messages diabeld")
    # Test status: successfull tested
    
    def filter_add_IPv4_adress(self):
        pass

    def filter_remove_IPv4_adress(self):
        pass

#*********************************************************************************************************
def loop():
    last_send_time = time.time()
    my_connector = connector()
    test_num = 0
    while True:

        message_flag, dict_message = my_connector.recieve_message()
        if 1 == message_flag: # printing recieved message information
            print("Received CANETH Message: ", "ID:", dict_message["ID"], "\tData:", dict_message["Data"], "\tExt:", dict_message["Ext"], "\tRTR:", dict_message["RTR"] )
        elif 0 == message_flag:
            print("No message received.")
            time.sleep(0.1)
        elif 2 == message_flag:
            print("target id not valid")
        else:
            print("message falg invalid.")

        # Send a CANETH message every 5 seconds
        if time.time() - last_send_time >= 2:
            
            # Testing differen sent messages from the connector_class to the canDevice via ESP32
            if 0 == test_num:
                # testing:  input data size greater than a hexadecimal byte
                # expected: sent binary-string is reduced to the size of a hexadecimal byte (first 16 digits)
                # result:   passed
                test_input = "00 00 00 00 00 00 00 00 00"
            elif 1 == test_num:
                # testing_  input data size smaller than a hexadecimal byte and even number of digits
                # expected: sent binary-string is reduced to the input size
                # result:   passed
                test_input = "00"
            elif 2 == test_num:
                # testing_  input data size smaller than a hexadecimal byte with white space and even number of digits
                # expected: sent binary-string is reduced to the input size and equal to input without whitespaces
                # result:   passed 
                test_input = "01 02 03 04 "
            elif 3 == test_num:
                # testing_  input data size smaller than a hexadecimal byte without white space and even number of digits
                # expected: sent binary-string is reduced to the input size and equal to input with whitespaces
                # result:   passed 
                test_input = "01020304"
            elif 4 == test_num:
                # testing_  input data size smaller than a hexadecimal byte with white space and odd number of digits
                # expected: sent binary-string is reduced to the input size with added 0 at the second last digit and equal to input without whitespaces
                # result:   passed 
                test_input = "01 2"
            elif 5 == test_num:
                # testing_  input data size smaller than a hexadecimal byte with whiteout space and odd number of digits
                # expected: sent binary-string is reduced to the input sizew ith added 0 at the second last digit and equal to input with whitespaces
                # result:   passed  
                test_input = "012"
            elif 6 == test_num: 
                # testing_  input data tested for input value from 00 to FF
                # expected: input data passed to binary-string
                # result:   passed
                test_input = "00 01 02 03 04 FD FE FF"
            elif 7 == test_num:
                # testing_  disabeling recieving messages
                # expected: disabeld recieving message and print statement when messag: "recieving messages disabeled"
                # result:   passed
                my_connector.toggle_recieving_message(False)
            elif 8 == test_num:
                # testing_  enabeling recieving messages
                # expected: enabeld recieving messages and print statement:
                # result:   passed
                my_connector.toggle_recieving_message(True)
            else:
                break
            
            test_num+=1

            # sending test message
            binary_string = convert_to_binary_string(test_input)
            can_id_hex = 0x123
            my_connector.send_message(can_id_hex, binary_string)

            last_send_time = time.time()
            print("Sent CANETH message")

#*********************************************************************************************************
if __name__ == "__main__":
    loop()    