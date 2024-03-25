from qt_application_backend import ( Connector, MessageLogger,convert_to_binary_string)
import sys
import os
import time
from collections import deque
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextBrowser, QVBoxLayout, 
    QWidget, QLabel, QLineEdit, QRadioButton, QTextEdit, QScrollArea
)
import threading
from PyQt5.QtCore import pyqtSignal, QObject

#*********************************************************************************************************
def loop():
    my_connector = Connector()
    my_msg_logger = MessageLogger()

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

        # sending test message
        test_input = "00 01 02 03 04 FD FE FF"
        binary_string = convert_to_binary_string(test_input)
        can_id_hex = 0x123
        my_connector.send_message(can_id_hex, binary_string)

        # print all recent messages       
        for message in my_msg_logger.get_recent_messages():
            print("Received CANETH Message: ", "ID:", message["ID"], "\tData:", message["Data"], "\tExt:", message["Ext"], "\tRTR:", message["RTR"])

        # print all exact messages
        for message in my_msg_logger.get_exact_messages():
            print("Received CANETH Message: ", "ID:", message["ID"], "\tData:", message["Data"], "\tExt:", message["Ext"], "\tRTR:", message["RTR"])
                      
        my_msg_logger.log_recent_message(message_flag, dict_message)
        my_msg_logger.log_exact_message(message_flag, dict_message)

#*********************************************************************************************************
class MessageReceiver(QObject):
    deque_updated_rec_msg = pyqtSignal(deque)
    deque_updated_log_msg = pyqtSignal(deque)

    def __init__(self, connector: Connector, message_logger: MessageLogger):
        super().__init__()
        self.my_connector = connector
        self.my_msg_logger = message_logger
        self.recent_message_deque = deque(maxlen=10)  # Begrenzt die Größe der Queue
        self.logging_message_deque = deque()
        self.is_running = False
        self.is_logging = False
        self.max_numb_of_logged_msg = 0
        self.numb_of_logged_msg = 0

    def run(self):
        while self.is_running:
            # Hier Logik zum Empfangen von Nachrichten einfügen
            # Beispiel:
            message_flag, dict_message =  self.my_connector.recieve_message()
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


class ConnectorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(ConnectorApp, self).__init__()
        # Laden der .ui Datei
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(current_dir, 'qt_application.ui')
        uic.loadUi(ui_path, self)

        self.init_backend()
        self.init_variables()
        self.initUI()

    def initUI(self):
        # init live view of recieved messages, logged messages and info texts
        self.textBrowser_rec_msg = self.findChild(QTextBrowser, 'textBrowser_rec_msg')
        self.textBrowser_log_msg = self.findChild(QTextBrowser, 'textBrowser_log_msg')
        
        self.textBrowser_canID_blacklist = self.findChild(QTextBrowser, 'textBrowser_canID_blacklist')
        self.textBrowser_canID_whitelist = self.findChild(QTextBrowser, 'textBrowser_canID_whitelist')

        self.textBrowser_rec_msg.setText("Here, received filtered messages will be continuously displayed.")
        self.textBrowser_log_msg.setText("Here, logged filtered messages will be displayed.")
        
        self.textBrowser_canID_blacklist.setText("Here, blacklisted CAN-IDs will be listed.\nCurrently the blacklist is empty.")
        self.textBrowser_canID_whitelist.setText("Here, whitelisted CAN-IDs will be listed.\nCurrently the whitelist is empty.")

        self.pushButton_start_stop = self.findChild(QPushButton, 'pushButton_start_stop')
        self.pushButton_start_stop.clicked.connect(self.toggle_button_text_start_stop)

        self.pushButton_update_max_log_msg = self.findChild(QPushButton, 'pushButton_update_max_log_msg')
        self.pushButton_update_max_log_msg.clicked.connect(self.pushed_pushButton_update_max_log_msg)

        self.pushButton_start_recording = self.findChild(QPushButton, 'pushButton_start_recording')
        self.pushButton_start_recording.clicked.connect(self.pushed_pushButton_start_recording)

        self.lineEdit_max_log_msg = self.findChild(QLineEdit, 'lineEdit_max_log_msg')
        self.lineEdit_max_log_msg.setText("Number of mesages")

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
    
    def init_variables(self):
        self.IPv4_blacklist_elements= 0
        self.IPv4_whitlist_elements= 0

    def init_backend(self):
        self.my_connector = Connector()
        self.my_msg_logger = MessageLogger()
        self.my_message_receiver = MessageReceiver(self.my_connector,self.my_msg_logger)
        self.my_message_receiver.deque_updated_rec_msg.connect(self.display_rec_message_deque)
        self.my_message_receiver.deque_updated_log_msg.connect(self.display_log_message_deque)
    
    #************************************************************************************
    # Methods for the live view of recieved can messages and the logging of messages
    def toggle_button_text_start_stop(self):
        current_text = self.pushButton_start_stop.text()
        if current_text == 'Start':
            print("Started")
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
            print("Stopped")
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
                print_string = "ID:" +  str(message["ID"])  +"\tData:" + str(message["Data"]) + "\tExt:" + str(message["Ext"]) + "\tRTR:" + str(message["RTR"])
                self.textBrowser_rec_msg.append(print_string)
        except:
            pass
    
    def display_log_message_deque(self, message_deque):
        self.textBrowser_log_msg.clear()
        try:
            for message in message_deque:
                print_string = "ID:" +  str(message["ID"])  +"\tData:" + str(message["Data"]) + "\tExt:" + str(message["Ext"]) + "\tRTR:" + str(message["RTR"])
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

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWin = ConnectorApp()
    mainWin.show()
    sys.exit(app.exec_())