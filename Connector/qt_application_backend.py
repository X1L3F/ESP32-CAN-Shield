import socket
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
# Test status: successfull tested

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
    return decoded_message
# Test status: successfull tested

#*********************************************************************************************************
def convert_to_binary_string(input_string):
    # FUNC: converting a string to a binary-string
    # INPUT: input_string as string; e.g.: "01 02 03 04 05 FD FE FF"
    # RETURN: binary_string
    hex_string = input_string.replace(' ', '')  # removing spaces
    if len(hex_string) % 2 != 0:    # catching error due to invalid hex_string length  
        hex_string = hex_string[:-1] + '0' + hex_string[-1]
    hex_string = hex_string[:16]  
    binary_string = bytes.fromhex(hex_string)

    return binary_string
# Test status: successfull tested

#*********************************************************************************************************
class Connector:
    def __init__(self):

        self.target_IP = "192.168.0.240"  # Target IP to send messages to.
        self.UDP_IP = "0.0.0.0"  # Listen on all network interfaces.
        self.shared_UDP_port = 4210  # Designated UDP port for communication. Recommenadtion: Using Userports from 1024 to 49151 for IPv4
        self.recieve_flag = False  # Flag to control message receiving.
        self.whitelist_enabled = False  # Flag to enable whitelist filtering.
        self.blacklist_enabled = False  # Flag to enable blacklist filtering.
        self.whitelist_IPs = set()  # Set of whitelisted IP addresses.
        self.blacklist_IPs = set()  # Set of blacklisted IP addresses.

        # setup UDP socket with default values
        self.update_UDP_socket(self.UDP_IP, self.shared_UDP_port)
        self.enable_blacklist_IPv4_address()

    def update_UDP_socket(self, input_UDP_IP, input_shared_UDP_port):
        # FUNC: updating the UDP socket with the new UDP_IP the connector should listen
        # INPUT: input_UDP_IP as string;     e.g.: "0.0.0.0"
        #        input_shared_UDP_port as int
        # RETURN: ---
        self.UDP_IP = input_UDP_IP
        self.shared_UDP_port = input_shared_UDP_port
        # updating UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.shared_UDP_port))
    
    def get_UDP_socket_info(self):
        # FUNC: returns the current Socket information
        # INPUT: ---
        # RETURN: UDP_IP as string;     e.g.: "0.0.0.0"
        #        shared_UDP_port as int
        return self.UDP_IP, self.shared_UDP_port

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
                    # Message is from a blacklisted IP
                    return_flag = 0  # special flag indicating blocked message.
                elif not self.whitelist_enabled or addr[0] in self.whitelist_IPs:
                    # blacklist enabled or message is allowed through whitelist filter.
                    decoded_message = decode_caneth_message(rec_data)
                    return_message = decoded_message
                    return_flag = 1  # flag indicating successful message reception.
                else:
                    # message is from a non-whitelisted IP when whitelist is enabled.
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

    def whitelist_clear_IPv4_addresses(self):
        # FUNC: removes all IPv4 addresses from the whitelist
        # RETURN: ---
        self.whitelist_IPs.clear()

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

    def blacklist_clear_IPv4_addresses(self):
        # FUNC: removes all IPv4 addresses from the blacklist
        # RETURN: ---
        self.blacklist_IPs.clear()

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

        self.whitelist_enabled = False
        self.blacklist_enabled = True
        self.whitelist_IDs = set()  # Set of whitelisted IP addresses.
        self.blacklist_IDs = set()  # Set of blacklisted IP addresses.

    def log_recent_message(self, message_flag, message):
        # Funktion: Protokollieren einer kürzlich empfangenen Nachricht
        # Eingabe:    message_flag (int): Wenn 1, dann Nachricht von gültiger IPv4-Adresse
        #            message (dict): Die zu protokollierende Nachricht
        # Rückgabe: ---
        if 1 == message_flag:
            if self.blacklist_enabled and message["ID"] in self.blacklist_IDs:
                # Message from blacklisted ID
                return
            if (not self.whitelist_enabled) or (self.whitelist_enabled and message["ID"] in self.whitelist_IDs):
                self.recent_messages.append(message)
            else:
                # Message not from an whitelisted ID
                pass
        else:
            pass

    def log_exact_message(self, message_flag, message):
        # Funktion: Protokollieren einer exakten Nachricht
        # Eingabe:    message_flag (int): Wenn 1, dann Nachricht von gültiger IPv4-Adresse
        #            message (dict): Die zu protokollierende Nachricht
        # Rückgabe: ---
        if len(self.exact_messages) >= self.exact_message_count:
            # exact message count limit is exceeded
            return

        if 1 == message_flag:
            if self.blacklist_enabled and message["ID"] in self.blacklist_IDs:
                # Message from blacklisted ID
                return
            if (not self.whitelist_enabled) or (self.whitelist_enabled and message["ID"] in self.whitelist_IDs):
                self.exact_messages.append(message)
            else:
                # Message not from an whitelisted ID
                pass
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
    
    def enable_whitelist_msgID(self):
        # FUNC: enables or disables whitelist filtering for ID
        # INPUT: ---
        # RETURN: ---
        self.whitelist_enabled = True
        self.blacklist_enabled = False

    def whitelist_add_msgID(self, input_msgID):
        # FUNC: adds an ID to the whitelist
        # INPUT: input_msgID as int
        # RETURN: ---
        self.whitelist_IDs.add(input_msgID)

    def whitelist_remove_msgID(self, input_msgID):
        # FUNC: removes an ID from the whitelist
        # INPUT: input_msgID as int
        # RETURN: ---
        self.whitelist_IDs.discard(input_msgID)
    
    def whitelist_clear_msgIDs(self):
        # FUNC: removes all IDs from the whitelist
        # RETURN: ---
        self.whitelist_IDs.clear()

    def enable_blacklist_msgID(self):
        # FUNC: enables blacklist filtering for ID 
        # INPUT: ---
        # RETURN: ---
        self.whitelist_enabled = False
        self.blacklist_enabled = True        

    def blacklist_add_msgID(self, input_msgID):
        # FUNC: adds an ID to the blacklist
        # INPUT: input_msgID as int
        # RETURN: ---
        self.blacklist_IDs.add(input_msgID)
    
    def blacklist_remove_msgID(self, input_msgID):
        # FUNC: removes an ID from the blacklist
        # INPUT: input_msgID as int
        # RETURN: ---
        self.blacklist_IDs.discard(input_msgID)
    
    def blacklist_clear_msgIDs(self):
        # FUNC: removes all IDs from the blacklist
        # RETURN: ---
        self.blacklist_IDs.clear()

#*********************************************************************************************************