from qt_application_backend import ( Connector, MessageLogger,convert_to_binary_string)
import sys
import os
from collections import deque
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (
    QPushButton, QTextBrowser, QVBoxLayout, 
    QLabel, QLineEdit, QRadioButton, QPlainTextEdit, QDialog
)
import threading
from PyQt5.QtCore import pyqtSignal, QObject

#*********************************************************************************************************
class PopupWindow(QDialog):
    # Pop Up Window for advanced Socket settings
    def __init__(self, connector: Connector):
        super().__init__()

        self.my_connector = connector
        self.UDP_IP, self.shared_UDP_port = self.my_connector.get_UDP_socket_info()

        self.setWindowTitle('Popup')
        layout = QVBoxLayout()

        self.label1 = QLabel()
        self.label1.setText("UDP IP: default value 0.0.0.0")
        self.edit1 = QLineEdit()
        self.edit1.setText(self.UDP_IP)

        self.label2 = QLabel()
        self.label2.setText("UDP Port: default value 4210")
        self.edit2 = QLineEdit()
        self.edit2.setText(str(self.shared_UDP_port))

        layout.addWidget(self.label1)
        layout.addWidget(self.edit1)
        layout.addWidget(self.label2)
        layout.addWidget(self.edit2)

        update_button = QPushButton('Update')
        update_button.clicked.connect(self.update_socket)
        layout.addWidget(update_button)

        self.setLayout(layout)

    def update_socket(self):
        in_UDP_IP = self.edit1.text()
        UPD_Port = int(self.edit2.text())
        self.my_connector.update_UDP_socket(in_UDP_IP, UPD_Port )

#*********************************************************************************************************
class MessageReceiver(QObject):
    # Multithreading Object for non blocking recieving messages
    deque_updated_rec_msg = pyqtSignal(deque)
    deque_updated_log_msg = pyqtSignal(deque)

    def __init__(self, connector: Connector, message_logger: MessageLogger):
        super().__init__()
        self.my_connector = connector
        self.my_msg_logger = message_logger
        self.recent_message_deque = deque(maxlen=10)
        self.logging_message_deque = deque()
        self.is_running = False
        self.is_logging = False
        self.max_numb_of_logged_msg = 0
        self.numb_of_logged_msg = 0

    def run(self):
        while self.is_running:
            message_flag, dict_message =  self.my_connector.recieve_message()
            self.my_msg_logger.log_recent_message(message_flag, dict_message)
            self.recent_message_deque = self.my_msg_logger.get_recent_messages()
            self.deque_updated_rec_msg.emit(self.recent_message_deque)

            if self.is_logging:
                if 1 == message_flag:
                    self.my_msg_logger.log_exact_message(message_flag, dict_message)
                    self.logging_message_deque = self.my_msg_logger.get_exact_messages()
                    self.deque_updated_log_msg.emit(self.logging_message_deque)

                    self.numb_of_logged_msg +=1
            if self.is_logging and self.numb_of_logged_msg >= self.max_numb_of_logged_msg:
                self.stop_logging()

    def start(self):
        self.my_connector.toggle_recieving_message(True)
        self.is_running = True

    def stop(self):
        self.my_connector.toggle_recieving_message(False)
        self.is_running = False

    def update_max_numb_of_log_msg(self, input_max_numb_of_logged_msg):
        self.max_numb_of_logged_msg = input_max_numb_of_logged_msg
    
    def start_logging(self):
        self.is_logging = True
        self.numb_of_logged_msg = 0
        self.logging_message_deque.clear()
        self.my_msg_logger.clear_exact_messages()
    
    def stop_logging(self):
        self.is_logging = False
        self.numb_of_logged_msg = 0

#*********************************************************************************************************
class ConnectorApp(QtWidgets.QMainWindow):
    # main window of the Connector Application
    def __init__(self):
        super(ConnectorApp, self).__init__()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(current_dir, 'qt_application.ui') # loading .ui file from QT5 Designer
        uic.loadUi(ui_path, self)

        self.init_backend()
        self.init_variables()
        self.initUI()

    def init_backend(self):
        self.my_connector = Connector()
        self.my_msg_logger = MessageLogger()
        self.my_message_receiver = MessageReceiver(self.my_connector,self.my_msg_logger)
        self.my_message_receiver.deque_updated_rec_msg.connect(self.display_rec_message_deque)
        self.my_message_receiver.deque_updated_log_msg.connect(self.display_log_message_deque)
    
    def init_variables(self):
        self.IPv4_blacklist_elements= 0
        self.IPv4_whitlist_elements= 0
        self.canid_blacklist_elements= 0
        self.canid_whitlist_elements= 0

    def initUI(self):
        # init live view of recieved messages, logged messages and info texts
        self.textBrowser_rec_msg = self.findChild(QTextBrowser, 'textBrowser_rec_msg')
        self.textBrowser_log_msg = self.findChild(QTextBrowser, 'textBrowser_log_msg')

        self.textBrowser_rec_msg.setText("Here, received filtered messages will be continuously displayed.")
        self.textBrowser_log_msg.setText("Here, logged filtered messages will be displayed.")

        self.pushButton_start_stop = self.findChild(QPushButton, 'pushButton_start_stop')
        self.pushButton_start_stop.clicked.connect(self.toggle_button_text_start_stop)
        self.pushButton_start_stop.setStyleSheet('''
                QPushButton { 
                    background-color: lightgreen;
                } 
                QPushButton:hover { 
                    background-color: green;
                }
            ''')

        self.pushButton_update_max_log_msg = self.findChild(QPushButton, 'pushButton_update_max_log_msg')
        self.pushButton_update_max_log_msg.clicked.connect(self.pushed_pushButton_update_max_log_msg)

        self.pushButton_start_recording = self.findChild(QPushButton, 'pushButton_start_recording')
        self.pushButton_start_recording.clicked.connect(self.pushed_pushButton_start_recording)

        self.lineEdit_max_log_msg = self.findChild(QLineEdit, 'lineEdit_max_log_msg')
        self.lineEdit_max_log_msg.setText("Number of messages")

        # init update Socket
        self.pushButton_Advanced_Settings = self.findChild(QPushButton, 'pushButton_Advanced_Settings')
        self.pushButton_Advanced_Settings.clicked.connect(self.open_popup_update_socket)

        # init IPv4 filter
        self.pushButton_clear_IPv4_filter = self.findChild(QPushButton, 'pushButton_clear_IPv4_filter')
        self.pushButton_clear_IPv4_filter.clicked.connect(self.pushed_pushButton_clear_IPv4_filter)
            # blacklist
        self.radioButton_enable_IPv4_blacklist = self.findChild(QRadioButton, 'radioButton_enable_IPv4_blacklist')
        self.radioButton_enable_IPv4_blacklist.clicked.connect(self.my_connector.enable_blacklist_IPv4_address)

        self.lineEdit_add_IPv4_blacklist = self.findChild(QLineEdit, 'lineEdit_add_IPv4_blacklist')

        self.pushButton_add_IPv4_blacklist = self.findChild(QPushButton, 'pushButton_add_IPv4_blacklist')
        self.pushButton_add_IPv4_blacklist.clicked.connect(self.pushed_pushButton_add_IPv4_blacklist)

        self.textBrowser_IPv4_blacklist = self.findChild(QTextBrowser, 'textBrowser_IPv4_blacklist')
        self.textBrowser_IPv4_blacklist.setText("Here, blacklisted IPv4 adresses will be listed.\nCurrently the blacklist is empty.")
            #whitelist
        self.radioButton_enable_IPv4_whitelist = self.findChild(QRadioButton, 'radioButton_enable_IPv4_whitelist')
        self.radioButton_enable_IPv4_whitelist.clicked.connect(self.my_connector.enable_whitelist_IPv4_address)

        self.lineEdit_add_IPv4_whitelist = self.findChild(QLineEdit, 'lineEdit_add_IPv4_whitelist')

        self.pushButton_add_IPv4_whitelist = self.findChild(QPushButton, 'pushButton_add_IPv4_whitelist')
        self.pushButton_add_IPv4_whitelist.clicked.connect(self.pushed_pushButton_add_IPv4_whitelist)

        self.textBrowser_IPv4_whitelist = self.findChild(QTextBrowser, 'textBrowser_IPv4_whitelist')
        self.textBrowser_IPv4_whitelist.setText("Here, whitelisted IPv4 adresses will be listed.\nCurrently the whitelist is empty.")

        # init CAN-ID filter
        self.pushButton_clear_canid_filter = self.findChild(QPushButton, 'pushButton_clear_canid_filter')
        self.pushButton_clear_canid_filter.clicked.connect(self.pushed_pushButton_clear_canid_filter)
            # blacklist
        self.radioButton_enable_canid_blacklist = self.findChild(QRadioButton, 'radioButton_enable_canid_blacklist')
        self.radioButton_enable_canid_blacklist.clicked.connect(self.my_msg_logger.enable_blacklist_msgID)

        self.lineEdit_add_canid_blacklist = self.findChild(QLineEdit, 'lineEdit_add_canid_blacklist')

        self.pushButton_add_canid_blacklist = self.findChild(QPushButton, 'pushButton_add_canid_blacklist')
        self.pushButton_add_canid_blacklist.clicked.connect(self.pushed_pushButton_add_canid_blacklist)

        self.textBrowser_canID_blacklist = self.findChild(QTextBrowser, 'textBrowser_canID_blacklist')
        self.textBrowser_canID_blacklist.setText("Here, blacklisted CAN-IDs will be listed.\nCurrently the blacklist is empty.\nInput CAN-ID as Integer from 0x000 to 0x7FF.")
            #whitelist
        self.radioButton_enable_canid_whitelist = self.findChild(QRadioButton, 'radioButton_enable_canid_whitelist')
        self.radioButton_enable_canid_whitelist.clicked.connect(self.my_msg_logger.enable_whitelist_msgID)

        self.lineEdit_add_canid_whitelist = self.findChild(QLineEdit, 'lineEdit_add_canid_whitelist')

        self.pushButton_add_canid_whitelist = self.findChild(QPushButton, 'pushButton_add_canid_whitelist')
        self.pushButton_add_canid_whitelist.clicked.connect(self.pushed_pushButton_add_canid_whitelist)

        self.textBrowser_canID_whitelist = self.findChild(QTextBrowser, 'textBrowser_canID_whitelist')
        self.textBrowser_canID_whitelist.setText("Here, whitelisted CAN-IDs will be listed.\nCurrently the whitelist is empty.\nInput CAN-ID as Integer from 0x000 to 0x7FF.")

        # sending CAN message
        self.plainTextEdit_target_ESP_IPv4_adress = self.findChild(QPlainTextEdit, 'plainTextEdit_target_ESP_IPv4_adress')
        self.plainTextEdit_target_ESP_IPv4_adress.setPlainText('192.168.0.240')

        self.plainTextEdit_target_can_id = self.findChild(QPlainTextEdit, 'plainTextEdit_target_can_id')
        self.plainTextEdit_target_can_id.setPlainText('69')

        self.plainTextEdit_hexadecimal_pair_0 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_0')
        self.plainTextEdit_hexadecimal_pair_0.setPlainText('00')
        self.plainTextEdit_hexadecimal_pair_1 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_1')
        self.plainTextEdit_hexadecimal_pair_1.setPlainText('00')
        self.plainTextEdit_hexadecimal_pair_2 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_2')
        self.plainTextEdit_hexadecimal_pair_2.setPlainText('00')
        self.plainTextEdit_hexadecimal_pair_3 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_3')
        self.plainTextEdit_hexadecimal_pair_3.setPlainText('00')
        self.plainTextEdit_hexadecimal_pair_4 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_4')
        self.plainTextEdit_hexadecimal_pair_4.setPlainText('00')
        self.plainTextEdit_hexadecimal_pair_5 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_5')
        self.plainTextEdit_hexadecimal_pair_5.setPlainText('00')
        self.plainTextEdit_hexadecimal_pair_6 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_6')
        self.plainTextEdit_hexadecimal_pair_6.setPlainText('00')
        self.plainTextEdit_hexadecimal_pair_7 = self.findChild(QPlainTextEdit, 'plainTextEdit_hexadecimal_pair_7')
        self.plainTextEdit_hexadecimal_pair_7.setPlainText('00')

        self.pushButton_send_can_msg = self.findChild(QPushButton, 'pushButton_send_can_msg')
        self.pushButton_send_can_msg.clicked.connect(self.pushed_pushButton_send_can_msg)
        self.pushButton_send_can_msg.setStyleSheet('''
                QPushButton { 
                    background-color: lightgreen;
                } 
                QPushButton:hover { 
                    background-color: green;
                }
            ''')
    
    #************************************************************************************
    # Methods for sending single messages
    def pushed_pushButton_send_can_msg(self):
        self.my_connector.updated_target_IP(self.plainTextEdit_target_ESP_IPv4_adress.toPlainText())

        hex_string_can_id = self.plainTextEdit_target_can_id.toPlainText()
        int_value_can_id = int(hex_string_can_id, 16)

        can_data_str = (self.plainTextEdit_hexadecimal_pair_0.toPlainText() + 
                        self.plainTextEdit_hexadecimal_pair_1.toPlainText() + 
                        self.plainTextEdit_hexadecimal_pair_2.toPlainText() + 
                        self.plainTextEdit_hexadecimal_pair_3.toPlainText() + 
                        self.plainTextEdit_hexadecimal_pair_4.toPlainText() + 
                        self.plainTextEdit_hexadecimal_pair_5.toPlainText() + 
                        self.plainTextEdit_hexadecimal_pair_6.toPlainText() + 
                        self.plainTextEdit_hexadecimal_pair_7.toPlainText())
        binary_can_data_str = convert_to_binary_string(can_data_str)
        
        self.my_connector.send_message(int_value_can_id, binary_can_data_str)

    #************************************************************************************
    # Methods for updating the Socket for recieving messages
    def open_popup_update_socket(self):
        popup = PopupWindow(self.my_connector)
        popup.exec_()
    
    #************************************************************************************
    # Methods for the live view of recieved can messages and the logging of messages
    def toggle_button_text_start_stop(self):
        current_text = self.pushButton_start_stop.text()
        if current_text == 'Start':
            self.my_message_receiver.start()
            self.my_thread = threading.Thread(target=self.my_message_receiver.run)
            self.my_thread.start()  # Startet den Thread

            self.pushButton_start_stop.setText('Stop')
            self.pushButton_start_stop.setStyleSheet('''
                QPushButton { 
                    background-color: lightcoral;
                } 
                QPushButton:hover { 
                    background-color: red;
                } 
                QPushButton[text="Stop"]:hover { 
                    background-color: red;
                }
            ''')
        else:
            self.my_message_receiver.stop()
            self.my_thread.join()  # Wartet darauf, dass der Thread beendet wird

            self.pushButton_start_stop.setText('Start')
            self.pushButton_start_stop.setStyleSheet('''
                QPushButton { 
                    background-color: lightgreen;
                } 
                QPushButton:hover { 
                    background-color: green;
                } 
                QPushButton[text="Start"]:hover { 
                    background-color: green;
                }
            ''')

    def pushed_pushButton_update_max_log_msg(self):
        new_max_numb_of_log_msg = int(self.lineEdit_max_log_msg.text())
        self.my_message_receiver.update_max_numb_of_log_msg(new_max_numb_of_log_msg)
        self.my_msg_logger.update_exact_message_count(new_max_numb_of_log_msg)

    def pushed_pushButton_start_recording(self):
        self.textBrowser_log_msg.clear()
        self.my_message_receiver.start_logging()

    def display_rec_message_deque(self, message_deque):
        self.textBrowser_rec_msg.clear()
        try:
            for message in message_deque:
                print_string = "ID:" +  str(message["ID"])  +"\tData:" + str(message["Data"]) + "\tExt:" + str(message["Ext"]) + "\tRTR:" + str(message["RTR"]) + "\tTime stamp: " + message["Time"]
                self.textBrowser_rec_msg.append(print_string)
        except:
            pass
    
    def display_log_message_deque(self, message_deque):
        self.textBrowser_log_msg.clear()
        try:
            for message in message_deque:
                print_string = "ID:" +  str(message["ID"])  +"\tData:" + str(message["Data"]) + "\tExt:" + str(message["Ext"]) + "\tRTR:" + str(message["RTR"]) + "\tTime stamp: " + message["Time"]
                self.textBrowser_log_msg.append(print_string)
        except:
            pass

    #************************************************************************************
    # IPv4 adress filter methods
    def pushed_pushButton_clear_IPv4_filter(self):
        self.my_connector.blacklist_clear_IPv4_addresses()
        self.my_connector.whitelist_clear_IPv4_addresses()
        self.textBrowser_IPv4_blacklist.setText("Here, blacklisted IPv4 adresses will be listed.\nCurrently the blacklist is empty.")
        self.textBrowser_IPv4_whitelist.setText("Here, whitelisted IPv4 adresses will be listed.\nCurrently the whitelist is empty.")
        self.IPv4_blacklist_elements= 0
        self.IPv4_whitlist_elements= 0

    def pushed_pushButton_add_IPv4_blacklist(self):
        new_IPv4_address = (self.lineEdit_add_IPv4_blacklist.text())
        self.my_connector.blacklist_add_IPv4_address(new_IPv4_address)
        if 0 == self.IPv4_blacklist_elements:
            self.textBrowser_IPv4_blacklist.setText(new_IPv4_address)
            self.IPv4_blacklist_elements= 1
        else: 
            self.textBrowser_IPv4_blacklist.append(new_IPv4_address)

    def pushed_pushButton_add_IPv4_whitelist(self):
        new_IPv4_address = (self.lineEdit_add_IPv4_whitelist.text())
        self.my_connector.whitelist_add_IPv4_address(new_IPv4_address)
        if 0 == self.IPv4_whitlist_elements:
            self.textBrowser_IPv4_whitelist.setText(new_IPv4_address)
            self.IPv4_whitlist_elements= 1
        else:
            self.textBrowser_IPv4_whitelist.append(new_IPv4_address)            
    
    #************************************************************************************
    # CAN ID filter methods
    def pushed_pushButton_clear_canid_filter(self):
        self.my_msg_logger.blacklist_clear_msgIDs()
        self.my_msg_logger.whitelist_clear_msgIDs()
        self.textBrowser_canID_blacklist.setText("Here, blacklisted CAN-IDs will be listed.\nCurrently the blacklist is empty.\nInput CAN-ID as Integer from 0x000 to 0x7FF.")
        self.textBrowser_canID_whitelist.setText("Here, whitelisted CAN-IDs will be listed.\nCurrently the whitelist is empty.\nInput CAN-ID as Integer from 0x000 to 0x7FF.")
        self.canid_blacklist_elements= 0
        self.canid_whitlist_elements= 0

    def pushed_pushButton_add_canid_blacklist(self):
        new_canid = int(self.lineEdit_add_canid_blacklist.text())
        self.my_msg_logger.blacklist_add_msgID(new_canid)
        if 0 == self.canid_blacklist_elements:
            self.textBrowser_canID_blacklist.setText(str(new_canid))
            self.canid_blacklist_elements= 1
        else: 
            self.textBrowser_canID_blacklist.append(str(new_canid))

    def pushed_pushButton_add_canid_whitelist(self):
        new_canid = int(self.lineEdit_add_canid_whitelist.text())
        self.my_msg_logger.whitelist_add_msgID(new_canid)
        if 0 == self.canid_whitlist_elements:
            self.textBrowser_canID_whitelist.setText(str(new_canid))
            self.canid_whitlist_elements= 1
        else:
            self.textBrowser_canID_whitelist.append(str(new_canid))  

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWin = ConnectorApp()
    mainWin.show()
    sys.exit(app.exec_())