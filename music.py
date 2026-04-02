import time
import subprocess
import os
import sys
import threading # Added for the timer functionality
from gpiozero import Button, OutputDevice

# --- CONFIGURATION ---
DEVICE_ADDR = "88:6F:38:9E:D2:BB" 
AUDIO_FILE = "cars.mp3"            
LIGHT_PIN = 18
BUTTON_PIN = 17
AUTO_OFF_DELAY = 20  # Seconds until the light turns off automatically

# --- INITIALIZATION ---
light = OutputDevice(LIGHT_PIN)
button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.2) 

# Track the system state
is_light_on = False
bt_ready = False
off_timer = None # Placeholder for our countdown timer

def connect_bluetooth(max_retries=2):
    """Attempts to connect to the speaker."""
    global bt_ready
    for attempt_num in range(1, max_retries + 1):
        print(f"Connection attempt {attempt_num}/{max_retries} to {DEVICE_ADDR}...")
        try:
            check = subprocess.run(["bluetoothctl", "info", DEVICE_ADDR], capture_output=True, text=True)
            if "Connected: yes" in check.stdout:
                bt_ready = True
                return True
            
            result = subprocess.run(["bluetoothctl", "connect", DEVICE_ADDR], capture_output=True, text=True, timeout=15)
            if "Connection successful" in result.stdout or "Connected: yes" in result.stdout:
                time.sleep(2) 
                bt_ready = True
                return True
        except Exception as e:
            print(f"Bluetooth error: {e}")
        time.sleep(2)
    bt_ready = False
    return False

def play_audio():
    """Plays audio using ffplay in the background."""
    if not os.path.exists(AUDIO_FILE):
        return
    try:
        subprocess.Popen(["ffplay", "-nodisp", "-autoexit", AUDIO_FILE], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Audio error: {e}")

def turn_off():
    """Core function to shut things down."""
    global is_light_on, off_timer
    print("STATUS: Turning OFF (Timer or Manual)")
    light.off()
    is_light_on = False
    subprocess.run(["pkill", "ffplay"])
    
    # Clean up the timer object if it exists
    if off_timer:
        off_timer.cancel()
        off_timer = None

def toggle_system():
    """Handles the button logic."""
    global is_light_on, bt_ready, off_timer

    if not is_light_on:
        # --- TURN ON ---
        print(f"STATUS: ON (Will auto-off in {AUTO_OFF_DELAY}s)")
        light.on()
        is_light_on = True
        
        if bt_ready:
            play_audio()
        else:
            if connect_bluetooth(max_retries=1):
                play_audio()
        
        # Start the 20-second countdown
        off_timer = threading.Timer(AUTO_OFF_DELAY, turn_off)
        off_timer.start()
    else:
        # --- MANUAL TURN OFF ---
        turn_off()

# --- MAIN LOGIC ---
print("System Ready. Initializing Bluetooth...")
connect_bluetooth()

button.when_pressed = toggle_system

try:
    print(f"Monitoring button. Light stays on for {AUTO_OFF_DELAY}s or until pressed again.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    turn_off()
    sys.exit(0)
