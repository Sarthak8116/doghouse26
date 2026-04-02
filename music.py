import time
import subprocess
import os
import sys
from gpiozero import Button, OutputDevice

# --- CONFIGURATION ---
DEVICE_ADDR = "88:6F:38:9E:D2:BB"  # Updated with your speaker address
AUDIO_FILE = "cars.mp3"            # The name of your audio file
LIGHT_PIN = 18
BUTTON_PIN = 17

# --- INITIALIZATION ---
light = OutputDevice(LIGHT_PIN)
button = Button(BUTTON_PIN, pull_up=True)

def connect_bluetooth(max_retries=3):
    """Attempts to connect to the speaker with a retry limit."""
    for attempt_num, _ in enumerate(range(max_retries), 1):
        print(f"Connection attempt {attempt_num}/{max_retries} to {DEVICE_ADDR}...")
        try:
            # Check if already connected first
            check = subprocess.run(["bluetoothctl", "info", DEVICE_ADDR], capture_output=True, text=True)
            if "Connected: yes" in check.stdout:
                print("Already connected.")
                return True
            
            # Attempt connection
            result = subprocess.run(["bluetoothctl", "connect", DEVICE_ADDR], capture_output=True, text=True, timeout=15)
            
            if "Connection successful" in result.stdout or "Connected: yes" in result.stdout:
                print("✓ Connected successfully!")
                time.sleep(2) # Buffer for PulseAudio
                return True
            else:
                print(f"Connection failed: {result.stdout}")
                
        except subprocess.TimeoutExpired:
            print("Error: Connection timed out.")
        except Exception as e:
            print(f"Unexpected Bluetooth error: {e}")
        
        time.sleep(5) # Wait before retrying
    
    print("CRITICAL: Could not connect to Bluetooth speaker.")
    return False

def play_audio():
    """Plays audio using ffplay (part of ffmpeg) which is more reliable."""
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: File '{AUDIO_FILE}' not found.")
        return

    try:
        # -nodisp: don't open a video window
        # -autoexit: close the process when the song ends
        subprocess.Popen(["ffplay", "-nodisp", "-autoexit", AUDIO_FILE], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        print(f"Playing {AUDIO_FILE} via ffplay...")
    except FileNotFoundError:
        print("Error: 'ffplay' not found. Trying to install ffmpeg...")
        subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"])
    except Exception as e:
        print(f"Audio playback error: {e}")

# --- MAIN LOGIC ---
print("System Ready. Initializing...")
# Try to connect once at startup
bt_ready = connect_bluetooth(max_retries=2)

try:
    print("Monitoring button...")
    playing = False 
    
    while True:
        if button.is_pressed:
            light.on()
            if not playing:
                print("STATUS: Button Pressed | Light ON")
                if bt_ready:
                    play_audio()
                else:
                    print("Bluetooth wasn't ready. Attempting quick reconnect...")
                    bt_ready = connect_bluetooth(max_retries=1)
                    if bt_ready:
                        play_audio()
                playing = True
        else:
            light.off()
            if playing:
                print("STATUS: Button Released | Light OFF")
                playing = False
        
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nShutting down...")
    light.off()
    sys.exit(0)
