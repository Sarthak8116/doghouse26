#!/usr/bin/env python3
"""
Raspberry Pi Bluetooth Speaker Controller
Connects to a Bluetooth speaker and plays audio on command.
"""

import subprocess
import time
import os
import sys

class BluetoothSpeaker:
    def __init__(self, device_address=None):
        """
        Initialize with optional Bluetooth device address.
        If not provided, will need to scan and pair first.
        """
        self.device_address = device_address
    
    def scan_devices(self, duration=10):
        """Scan for nearby Bluetooth devices."""
        print(f"Scanning for Bluetooth devices ({duration} seconds)...")
        try:
            # Start scanning
            subprocess.run(["bluetoothctl", "scan", "on"], timeout=2, capture_output=True)
            time.sleep(duration)
            subprocess.run(["bluetoothctl", "scan", "off"], timeout=2, capture_output=True)
            
            # List discovered devices
            result = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True,
                text=True
            )
            
            devices = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith("Device"):
                    parts = line.split(' ', 2)
                    if len(parts) >= 3:
                        addr = parts[1]
                        name = parts[2]
                        devices.append((addr, name))
            
            return devices
        except Exception as e:
            print(f"Error scanning: {e}")
            return []
    
    def pair(self, address):
        """Pair with a Bluetooth device."""
        print(f"Pairing with {address}...")
        try:
            subprocess.run(["bluetoothctl", "pair", address], timeout=30)
            self.device_address = address
            return True
        except Exception as e:
            print(f"Error pairing: {e}")
            return False
    
    def trust(self, address=None):
        """Trust a device for auto-connect."""
        addr = address or self.device_address
        if not addr:
            print("No device address specified")
            return False
        
        try:
            subprocess.run(["bluetoothctl", "trust", addr], timeout=10)
            return True
        except Exception as e:
            print(f"Error trusting device: {e}")
            return False
    
    def connect(self, address=None):
        """Connect to a Bluetooth speaker."""
        addr = address or self.device_address
        if not addr:
            print("No device address specified")
            return False
        
        print(f"Connecting to {addr}...")
        try:
            result = subprocess.run(
                ["bluetoothctl", "connect", addr],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if "Connected: yes" in result.stdout or "Connection successful" in result.stdout:
                print("Connected successfully!")
                self.device_address = addr
                time.sleep(2)  # Give audio sink time to register
                return True
            else:
                print(f"Connection output: {result.stdout}")
                return False
        except Exception as e:
            print(f"Error connecting: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the speaker."""
        if not self.device_address:
            return True
        
        try:
            subprocess.run(["bluetoothctl", "disconnect", self.device_address], timeout=10)
            return True
        except Exception as e:
            print(f"Error disconnecting: {e}")
            return False
    
    def is_connected(self):
        """Check if device is connected."""
        if not self.device_address:
            return False
        
        try:
            result = subprocess.run(
                ["bluetoothctl", "info", self.device_address],
                capture_output=True,
                text=True
            )
            return "Connected: yes" in result.stdout
        except:
            return False
    
    def play_audio(self, file_path):
        """Play an audio file through the Bluetooth speaker."""
        if not os.path.exists(file_path):
            print(f"Audio file not found: {file_path}")
            return False
        
        print(f"Playing: {file_path}")
        
        # Determine file type and use appropriate player
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.mp3':
                # Use mpg123 for MP3 files
                subprocess.run(["mpg123", file_path])
            elif ext in ['.wav', '.ogg', '.flac']:
                # Use aplay for WAV, or ffplay/paplay for others
                if ext == '.wav':
                    subprocess.run(["aplay", file_path])
                else:
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path])
            else:
                # Generic fallback with ffplay
                subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path])
            
            return True
        except FileNotFoundError as e:
            print(f"Audio player not found. Install with: sudo apt install mpg123 ffmpeg")
            return False
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False
    
    def play_text(self, text):
        """Convert text to speech and play through speaker."""
        try:
            # Use espeak for text-to-speech
            subprocess.run(["espeak", text])
            return True
        except FileNotFoundError:
            print("espeak not found. Install with: sudo apt install espeak")
            return False
        except Exception as e:
            print(f"Error with TTS: {e}")
            return False


def setup_interactive():
    """Interactive setup wizard."""
    speaker = BluetoothSpeaker()
    
    print("\n=== Bluetooth Speaker Setup ===\n")
    print("1. Make sure your Bluetooth speaker is in pairing mode")
    input("Press Enter when ready to scan...")
    
    devices = speaker.scan_devices(duration=10)
    
    if not devices:
        print("No devices found. Make sure your speaker is in pairing mode.")
        return None
    
    print("\nFound devices:")
    for i, (addr, name) in enumerate(devices, 1):
        print(f"  {i}. {name} ({addr})")
    
    choice = input("\nEnter device number to connect (or 'q' to quit): ")
    if choice.lower() == 'q':
        return None
    
    try:
        idx = int(choice) - 1
        addr, name = devices[idx]
    except (ValueError, IndexError):
        print("Invalid selection")
        return None
    
    print(f"\nSelected: {name}")
    
    # Pair and trust
    speaker.pair(addr)
    speaker.trust(addr)
    
    # Connect
    if speaker.connect(addr):
        print(f"\n✓ Successfully connected to {name}")
        print(f"\nSave this address for future use: {addr}")
        return speaker
    else:
        print("\n✗ Failed to connect")
        return None


def main():
    """Main entry point with command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bluetooth Speaker Controller")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup")
    parser.add_argument("--address", "-a", help="Bluetooth device address (XX:XX:XX:XX:XX:XX)")
    parser.add_argument("--connect", action="store_true", help="Connect to speaker")
    parser.add_argument("--play", "-p", help="Audio file to play")
    parser.add_argument("--say", "-s", help="Text to speak")
    parser.add_argument("--scan", action="store_true", help="Scan for devices")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_interactive()
        return
    
    if args.scan:
        speaker = BluetoothSpeaker()
        devices = speaker.scan_devices()
        print("\nFound devices:")
        for addr, name in devices:
            print(f"  {name} ({addr})")
        return
    
    if args.address:
        speaker = BluetoothSpeaker(args.address)
        
        if args.connect or args.play or args.say:
            if not speaker.is_connected():
                speaker.connect()
        
        if args.play:
            speaker.play_audio(args.play)
        
        if args.say:
            speaker.play_text(args.say)
    else:
        parser.print_help()
        print("\n\nQuick start:")
        print("  1. First run: python3 bluetooth_speaker.py --setup")
        print("  2. Then use:  python3 bluetooth_speaker.py -a XX:XX:XX:XX:XX:XX --play song.mp3")


if __name__ == "__main__":
    main()
