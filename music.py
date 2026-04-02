import time
import subprocess
import os
import sys
from gpiozero import Button, OutputDevice

# --- CONFIGURATION ---
DEVICE_ADDR = "88:6F:38:9E:D2:BB" 
AUDIO_FILE = "cars.mp3"            
LIGHT_PIN = 18
BUTTON_PIN = 17

# --- INITIALIZATION ---
light = OutputDevice(LIGHT_PIN)
# bounce_time=0.2 handles debouncing automatically
button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.2) 

# Track the system state
is_light_on = False
bt_ready = False

def connect_bluetooth(max_retries=2):
    """Attempts to connect to the speaker."""
    global bt_ready
    for attempt_num in range(1, max_retries + 1):
        print(f"Connection attempt {attempt_num}/{max_retries} to {DEVICE_ADDR}...")
        try:
            check = subprocess.run(["bluetoothctl", "info", DEVICE_ADDR], capture_output=True, text=True)
            if "Connected: yes" in check.stdout:
                print("Already connected.")
                bt_ready = True
                return True
            
            result = subprocess.run(["bluetoothctl", "connect", DEVICE_ADDR], capture_output=True, text=True, timeout=15)
            if "Connection successful" in result.stdout or "Connected: yes" in result.stdout:
                print("✓ Connected successfully!")
                time.sleep(2) 
                bt_ready = True
                return True
        except Exception as e:
            print(f"Bluetooth error: {e}")
        time.sleep(2)
    
    print("Bluetooth not available, but light will still work.")
    bt_ready = False
    return False

def play_audio():
    """Plays audio using ffplay in the background."""
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: File '{AUDIO_FILE}' not found.")
        return

    try:
        # Launch in background
        subprocess.Popen(["ffplay", "-nodisp", "-autoexit", AUDIO_FILE], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        print(f"Playing {AUDIO_FILE}...")
    except Exception as e:
        print(f"Audio error: {e}")

def toggle_system():
    """This function runs EXACTLY ONCE per button press."""
    global is_light_on, bt_ready

    if not is_light_on:
        # --- TURN EVERYTHING ON ---
        print("STATUS: Button Pressed | Action: ON")
        light.on()
        is_light_on = True
        
        if bt_ready:
            play_audio()
        else:
            # Quick attempt to reconnect if it dropped
            if connect_bluetooth(max_retries=1):
                play_audio()
    else:
        # --- TURN EVERYTHING OFF ---
        print("STATUS: Button Pressed | Action: OFF")
        light.off()
        is_light_on = False
        # Optional: Stop music when turning off
        subprocess.run(["pkill", "ffplay"])

# --- MAIN LOGIC ---
print("System Ready. Initializing Bluetooth...")
connect_bluetooth()

# Tell the button to call toggle_system whenever it's pressed
button.when_pressed = toggle_system

try:
    print("Monitoring button (Toggle Mode). Press Ctrl+C to exit.")
    # Keep the script alive since the work is now done via events
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down...")
    light.off()
    sys.exit(0)