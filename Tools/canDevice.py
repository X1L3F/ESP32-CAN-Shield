import can
import time

def listen_and_send(bus, send_interval=1):
    """
    Listens for incoming messages and sends a message every 'send_interval' seconds.
    """
    last_send_time = None  # Track when the last message was sent
    data_change = 0

    while True:
        current_time = time.time()

        # Send a message if the interval has passed
        if last_send_time is None or (current_time - last_send_time) >= send_interval:
            msg = can.Message(arbitration_id=0x45, data=[data_change, 255, 0, 1, 3, 1, 4, 1], is_extended_id=False)
            print(msg)
            try:
                bus.send(msg)
                print(f"Message sent on {bus.channel_info}")
                last_send_time = current_time  # Update the last send time
                data_change += 1 # increas number
            except can.CanError:
                print("Message NOT sent")

        # Non-blocking check for incoming messages
        message = bus.recv(timeout=0)  # Non-blocking
        if message:
            print(f"Received message: {message}") # message format: Timestamp   sender_can_ID  msg_info    data_length     msg_content     channel_info

        time.sleep(0.1) # Short sleep to prevent a tight loop that consumes too much CPU

if __name__ == "__main__":
    with can.Bus(interface='vector', app_name='CANalyzer', channel=0, bitrate=500000) as bus:
        listen_and_send(bus)
