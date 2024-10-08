import paho.mqtt.client as mqtt
import serial
import time
import os
import threading
import pygame

# MQTT Settings
MQTT_BROKER = "192.168.2.10"  # Change this to your MQTT broker address
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "/show/"  # Prefix for all show topics

# Serial Settings
SERIAL_PORT = "COM8"  # Change this to match your ESP32's serial port
SERIAL_BAUD = 115200

# Show file directory
SHOW_DIR = "shows"  # Directory containing show files

# Global variables
ser = None
current_show = None
show_thread = None
stop_event = threading.Event()
available_shows = set()

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    for show in available_shows:
        topic = f"{MQTT_TOPIC_PREFIX}{show}"
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

def on_message(client, userdata, msg):
    global current_show, show_thread, stop_event
    show_name = msg.topic.split('/')[-1]
    print(f"Received message for show: {show_name}")
    
    if show_thread and show_thread.is_alive():
        print("Stopping current show...")
        stop_event.set()
        show_thread.join()
        stop_event.clear()
    
    current_show = show_name
    show_thread = threading.Thread(target=play_show, args=(current_show,))
    show_thread.start()

def connect_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        print(f"Connected to {SERIAL_PORT}")
    except serial.SerialException as e:
        print(f"Failed to connect to {SERIAL_PORT}: {e}")
        exit(1)

def play_audio(audio_file):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

def play_show(show_name):
    show_file = os.path.join(SHOW_DIR, f"{show_name}.dmx")
    audio_file = os.path.join(SHOW_DIR, f"{show_name}.mp3")
    
    if not os.path.exists(show_file):
        print(f"Show file not found: {show_file}")
        return

    with open(show_file, 'r') as file:
        lines = file.readlines()

    if os.path.exists(audio_file):
        play_audio(audio_file)
        print(f"Playing audio: {audio_file}")

    start_time = time.time()
    last_timecode = 0

    for line in lines:
        if stop_event.is_set():
            pygame.mixer.music.stop()
            print(f"Show {show_name} stopped.")
            return

        timecode, _, address, value = map(float, line.strip().split())
        
        # Wait until the correct timecode
        while (time.time() - start_time) < timecode:
            if stop_event.is_set():
                pygame.mixer.music.stop()
                print(f"Show {show_name} stopped.")
                return
            time.sleep(0.001)  # Small sleep to prevent busy waiting
        
        # Send the command to the ESP32
        command = f"{int(address)} {int(value)}\n"
        ser.write(command.encode())
        
        # print(f"Sent: {command.strip()} at {timecode:.3f}s")
        
        last_timecode = timecode

    # Wait for audio to finish if it's still playing
    while pygame.mixer.music.get_busy() and not stop_event.is_set():
        time.sleep(0.1)

    pygame.mixer.music.stop()
    print(f"Show {show_name} completed. Duration: {last_timecode:.3f}s")

def find_available_shows():
    global available_shows
    for file in os.listdir(SHOW_DIR):
        if file.endswith(".dmx"):
            show_name = os.path.splitext(file)[0]
            available_shows.add(show_name)
    print(f"Available shows: {available_shows}")

def main():
    connect_serial()
    find_available_shows()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()

    except KeyboardInterrupt:
        print("Program terminated by user")
    finally:
        stop_event.set()
        if show_thread:
            show_thread.join()
        client.loop_stop()
        if ser:
            ser.close()
        pygame.mixer.quit()

if __name__ == "__main__":
    main()