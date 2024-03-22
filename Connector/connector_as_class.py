import socket
import time
from struct import pack, unpack
from collections import deque

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
    data = data[:8]
    data_hex = ' '.join([format(byte, '02X') for byte in data]) # Convert data to hex string
    # Unpack flags
    ext_flag, rtr_flag = unpack('BB', message[23:25])

    # Create a dictionary with the decoded message components
    decoded_message = {
        "ID": can_id,
        "Data": data_hex,
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
class Connector:
    def __init__(self):

        self.target_IP = "192.168.0.240"  # Target IP to send messages to and from.
        self.UDP_IP = "0.0.0.0"  # Listen on all network interfaces.
        self.shared_UDP_port = 4210  # Designated UDP port for communication.
        self.recieve_flag = True  # Flag to control message receiving.
        self.whitelist_enabled = False  # Flag to enable whitelist filtering.
        self.blacklist_enabled = False  # Flag to enable blacklist filtering.
        self.whitelist_IPs = set()  # Set of whitelisted IP addresses.
        self.blacklist_IPs = set()  # Set of blacklisted IP addresses.

        # setup UDP socket with default values
        self.update_UDP_socket(self.UDP_IP)
        self.enable_blacklist_IPv4_address()

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

        return_flag = -1 
        return_message = None

        if True == self.recieve_flag:
            self.sock.settimeout(1.0)  # set timeout to 1 second for non-blocking receive

            try:
                rec_data, addr = self.sock.recvfrom(2048)  # attempt to receive data.
                if self.blacklist_enabled and addr[0] in self.blacklist_IPs:
                    # Message is from a blacklisted IP.
                    print(f"Blocked message from blacklisted IP {addr[0]}")
                    return_flag = 0  # special flag indicating blocked message.
                elif not self.whitelist_enabled or addr[0] in self.whitelist_IPs:
                    # blacklist enabled or message is allowed through whitelist filter.
                    decoded_message = decode_caneth_message(rec_data)
                    return_message = decoded_message
                    return_flag = 1  # flag indicating successful message reception.
                else:
                    # message is from a non-whitelisted IP when whitelist is enabled.
                    print(f"Ignored message from non-whitelisted IP {addr[0]}")
                    return_flag = 2  # flag indicating message ignored.
            except socket.timeout:
                # no data received within timeout period.
                pass

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

    def enable_whitelist_IPv4_address(self):
        # FUNC: enables or disables whitelist filtering for IPv4 adresses 
        # INPUT: ---
        # RETURN: ---
        self.whitelist_enabled = True
        self.blacklist_enabled = False

    def whitelist_add_IPv4_address(self, input_IPv4_address):
        # FUNC: adds an IPv4 address to the whitelist
        # INPUT: input_IPv4_address as string; e.g.: "192.168.0.240"
        # RETURN: ---
        self.whitelist_IPs.add(input_IPv4_address)

    def whitelist_remove_IPv4_address(self, input_IPv4_address):
        # FUNC: removes an IPv4 address from the whitelist
        # INPUT: input_IPv4_address as string
        # RETURN: ---
        self.whitelist_IPs.discard(input_IPv4_address)

    def enable_blacklist_IPv4_address(self):
        # FUNC: enables blacklist filtering for IPv4 adresses 
        # INPUT: ---
        # RETURN: ---
        self.whitelist_enabled = False
        self.blacklist_enabled = True
        

    def blacklist_add_IPv4_address(self, input_IPv4_address):
        # FUNC: adds an IPv4 address to the blacklist
        # INPUT: input_IPv4_address as string
        # RETURN: ---
        self.blacklist_IPs.add(input_IPv4_address)
    
    def blacklist_remove_IPv4_address(self, input_IPv4_address):
        # FUNC: removes an IPv4 address from the blacklist
        # INPUT: input_IPv4_address as string
        # RETURN: ---
        self.blacklist_IPs.discard(input_IPv4_address)

#*********************************************************************************************************
#from collections import deque
class MessageLogger:
    def __init__(self, max_recent_messages=10, exact_message_count=10):
        # FUNC: initialize the MessageLogger class
        # INPUT: max_recent_messages (int, optional): Maximum number of recent messages to be stored. Defaults to 10.
        #        exact_message_count (int, optional): Exact number of messages to be stored. Defaults to 10.
        # RETURN: ---
        self.max_recent_messages = max_recent_messages  # Maximum number of recent messages
        self.recent_messages = deque(maxlen=max_recent_messages) if max_recent_messages else []  # Recent messages deque

        self.exact_message_count = exact_message_count  # Exact number of messages to be stored
        self.exact_messages = deque(maxlen=exact_message_count) if exact_message_count else []  # Exact messages deque

    def log_recent_message(self, message_flag, message):
        # FUNC: Log a recent message
        # INPUT: message (dict): The message to be logged
        # RETURN: ---
        #print("LOG recent: ", "ID:", message["ID"], "\tData:", message["Data"], "\tExt:", message["Ext"], "\tRTR:", message["RTR"] )
        if 1 == message_flag:
            self.recent_messages.append(message)  # Append the message to the recent messages deque
        else:
            pass

    def log_exact_message(self, message_flag, message):
        # FUNC: Log a exact message
        # INPUT: message (dict): The message to be logged
        # RETURN: ---
        #print("LOG Exact: ", "ID:", message["ID"], "\tData:", message["Data"], "\tExt:", message["Ext"], "\tRTR:", message["RTR"] )
        if 1 == message_flag:
            self.exact_messages.append(message)  # Append the message to the exact messages deque
        else:
            pass

    def clear_recent_messages(self):
        # FUNC: Clear all stored recent messages
        # INPUT: ---
        # RETURN: ---
        self.recent_messages.clear()  # Clear the recent messages deque

    def clear_exact_messages(self):
        # FUNC: Clear all stored exact messages
        # INPUT: ---
        # RETURN: ---
        self.exact_messages.clear()  # Clear the exact messages deque

    def update_max_recent_messages(self, new_max_recent):
        # FUNC: Update the maximum number of recent messages to be stored
        # INPUT: new_max_recent (int): New maximum number of recent messages
        # RETURN: ---
        self.max_recent_messages = new_max_recent  # Update the maximum number of recent messages
        self.recent_messages = deque(self.recent_messages, maxlen=new_max_recent)  # Reinitialize the deque with updated max length

    def update_exact_message_count(self, new_exact_count):
        # FUNC: Update the maximum number of exact messages to be stored
        # INPUT:  new_exact_count (int): New exact number of messages
        # RETURN: ---
        self.exact_message_count = new_exact_count  # Update the exact number of messages
        self.exact_messages = deque(self.exact_messages, maxlen=new_exact_count)  # Reinitialize the deque with updated max length
    
    def get_recent_messages(self):
        # FUNC: Get all recent stored messages
        # INPUT:  ---
        # RETURN: deque: Deque containing all recent messages
        return self.recent_messages
    
    def get_exact_messages(self):
        # FUNC: Get all exact stored messages
        # INPUT:  ---
        # RETURN: deque: Deque containing all exact messages
        return self.exact_messages

#*********************************************************************************************************
def loop():
    last_send_time = time.time()
    my_connector = Connector()
    my_msg_logger = MessageLogger()

    test_num = 0
    while True:

        message_flag, dict_message = my_connector.recieve_message()

        if 1 == message_flag: # printing recieved message information
            print("Received CANETH Message: ", "ID:", dict_message["ID"], "\tData:", dict_message["Data"], "\tExt:", dict_message["Ext"], "\tRTR:", dict_message["RTR"] )
        elif 0 == message_flag:
            print("Recieved message's IPv4 adress is blacklisted")
        elif 2 == message_flag:
            print("Recieved message's IPv4 adress is not whitlisted")
        elif -1 == message_flag:
            print("No message recieved")
            time.sleep(0.1)
        else:
            print("message flag invalid.")

        # Send a CANETH message every 5 seconds
        if time.time() - last_send_time >= 2:
            
            if False:
                print("TEST: ", test_num, " *********************************************************************")
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
                    # expected: enabeld recieving messages and print statement: "Recieving messages enabled"
                    # result:   passed
                    my_connector.toggle_recieving_message(True)
                elif 9 == test_num:
                    # testing_  enabeling empty whitelist
                    # expected: recieved message's IPv4 adress is not whitlisted; message_flag =2
                    # result:   passed
                    my_connector.enable_whitelist_IPv4_address()
                elif 10 == test_num:
                    # testing_  adding a valid IPv4 adress to the whitelist
                    # expected: recieved message's IPv4 adress is not whitlisted; message_flag =1
                    # result:   passed
                    my_connector.whitelist_add_IPv4_address("192.168.0.240")
                elif 11 == test_num:
                    # testing_  removing a valid IPv4 adress from the whitelist
                    # expected: recieved message's IPv4 adress is not whitlisted; message_flag =2
                    # result:   passed
                    my_connector.whitelist_remove_IPv4_address("192.168.0.240")
                elif 12 == test_num:
                    # testing_  enabeling empty blacklist
                    # expected: recieved message's IPv4 adress is not blacklisted, message_flag =1
                    # result:   passed
                    my_connector.enable_blacklist_IPv4_address()
                elif 13 == test_num:
                    # testing_  adding valid IPv4 adress to blacklist
                    # expected: recieved message's IPv4 adress is blacklisted, message_flag =0
                    # result:   passed
                    my_connector.blacklist_add_IPv4_address("192.168.0.240")
                elif 14 == test_num:
                    # testing_  removing valid IPv4 adress from blacklist
                    # expected: recieved message's IPv4 adress is not blacklisted, message_flag =1
                    # result:   passed
                    my_connector.blacklist_remove_IPv4_address("192.168.0.240")
                else:
                    pass

                test_num+=1

                # sending test message
                binary_string = convert_to_binary_string(test_input)
                can_id_hex = 0x123
                my_connector.send_message(can_id_hex, binary_string)

                last_send_time = time.time()
                print("Sent CANETH message")

            
        # Testing the MessageLogger class
        if True:
            if 0 == test_num:
                    # testing:  updating the recent message count
                    # expected: exact message count updated to 5
                    # result:   passed
                my_msg_logger.update_max_recent_messages(5)
            
                    # testing:  updating the exact message count
                    # expected: exact message count updated to 8
                    # result:   passed
                my_msg_logger.update_exact_message_count(8)

                # testing:  adding a message to the recent message memory
                # expected: when printed: last 5 messages displayed
                # result:   passed
            my_msg_logger.log_recent_message(message_flag, dict_message)

                # testing:  adding a message to the exact message memory
                # expected: when printed: first 8 messages displayed
                # result:   passed
            my_msg_logger.log_exact_message(message_flag, dict_message)

            if 15 == test_num:
                # print all recent messages
                print("Recent Messages:")
                for message in my_msg_logger.get_recent_messages():
                    print("Received CANETH Message: ", "ID:", message["ID"], "\tData:", message["Data"], "\tExt:", message["Ext"], "\tRTR:", message["RTR"])

                # print all exact messages
                print("Exact Messages:")
                for message in my_msg_logger.get_exact_messages():
                    print("Received CANETH Message: ", "ID:", message["ID"], "\tData:", message["Data"], "\tExt:", message["Ext"], "\tRTR:", message["RTR"])
                
                break

            test_num += 1

#*********************************************************************************************************
if __name__ == "__main__":
    loop()    