#!/usr/bin/env python3
"""
Simple Command Listener
Waits for commands (via stdin, file, or network) and plays audio.
"""

import os
import sys
import json
import socket
import threading
from bluetooth_speaker import BluetoothSpeaker

# Configuration - Update these for your setup
CONFIG = {
    "speaker_address": "XX:XX:XX:XX:XX:XX",  # Your speaker's Bluetooth address
    "audio_folder": "/home/pi/music",         # Folder with your audio files
    "listen_port": 5000,                       # Port for network commands
}


class CommandListener:
    def __init__(self, speaker_address):
        self.speaker = BluetoothSpeaker(speaker_address)
        self.audio_folder = CONFIG["audio_folder"]
        self.running = False
        
        # Command mappings - customize these!
        self.commands = {
            "play": self.cmd_play,
            "stop": self.cmd_stop,
            "doorbell": lambda: self.play_file("doorbell.mp3"),
            "welcome": lambda: self.speaker.play_text("Welcome to the hotel"),
            "checkout": lambda: self.play_file("checkout_reminder.mp3"),
            "alert": lambda: self.play_file("alert.wav"),
        }
    
    def ensure_connected(self):
        """Make sure we're connected to the speaker."""
        if not self.speaker.is_connected():
            print("Connecting to speaker...")
            return self.speaker.connect()
        return True
    
    def play_file(self, filename):
        """Play an audio file from the audio folder."""
        filepath = os.path.join(self.audio_folder, filename)
        if os.path.exists(filepath):
            self.ensure_connected()
            self.speaker.play_audio(filepath)
        else:
            print(f"File not found: {filepath}")
    
    def cmd_play(self, filename=None):
        """Play command - plays specified file."""
        if filename:
            self.play_file(filename)
        else:
            print("Usage: play <filename>")
    
    def cmd_stop(self):
        """Stop playback (placeholder - implement as needed)."""
        print("Stop command received")
        # Could implement with subprocess to kill audio player
    
    def process_command(self, command_str):
        """Process a command string."""
        parts = command_str.strip().lower().split(maxsplit=1)
        if not parts:
            return
        
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else None
        
        if cmd in self.commands:
            handler = self.commands[cmd]
            if args and callable(handler):
                # Check if handler accepts arguments
                try:
                    handler(args)
                except TypeError:
                    handler()
            else:
                handler()
        else:
            print(f"Unknown command: {cmd}")
            print(f"Available commands: {', '.join(self.commands.keys())}")
    
    def listen_stdin(self):
        """Listen for commands from standard input."""
        print("Listening for commands (type 'help' for available commands)...")
        print("Commands: " + ", ".join(self.commands.keys()))
        print()
        
        while self.running:
            try:
                cmd = input("> ").strip()
                if cmd.lower() == "quit":
                    break
                elif cmd.lower() == "help":
                    print("Available commands:")
                    for c in self.commands:
                        print(f"  - {c}")
                else:
                    self.process_command(cmd)
            except EOFError:
                break
            except KeyboardInterrupt:
                break
    
    def listen_network(self, port=5000):
        """Listen for commands over the network (simple TCP)."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', port))
        server.listen(5)
        server.settimeout(1.0)
        
        print(f"Listening for network commands on port {port}...")
        print(f"Send commands with: echo 'play song.mp3' | nc <pi_ip> {port}")
        
        while self.running:
            try:
                client, addr = server.accept()
                data = client.recv(1024).decode('utf-8')
                print(f"Received from {addr}: {data}")
                self.process_command(data)
                client.close()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Network error: {e}")
        
        server.close()
    
    def start(self, mode="stdin"):
        """Start listening for commands."""
        self.running = True
        
        # Connect to speaker on startup
        print("Connecting to Bluetooth speaker...")
        if self.ensure_connected():
            print("✓ Connected!")
        else:
            print("⚠ Could not connect - will retry when playing")
        
        if mode == "stdin":
            self.listen_stdin()
        elif mode == "network":
            self.listen_network(CONFIG["listen_port"])
        elif mode == "both":
            # Run network listener in background thread
            net_thread = threading.Thread(target=self.listen_network, args=(CONFIG["listen_port"],))
            net_thread.daemon = True
            net_thread.start()
            self.listen_stdin()
    
    def stop(self):
        """Stop listening."""
        self.running = False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Command Listener for Bluetooth Speaker")
    parser.add_argument("--address", "-a", default=CONFIG["speaker_address"],
                        help="Bluetooth speaker address")
    parser.add_argument("--mode", "-m", choices=["stdin", "network", "both"],
                        default="stdin", help="Listening mode")
    parser.add_argument("--folder", "-f", default=CONFIG["audio_folder"],
                        help="Audio files folder")
    
    args = parser.parse_args()
    
    CONFIG["speaker_address"] = args.address
    CONFIG["audio_folder"] = args.folder
    
    listener = CommandListener(args.address)
    
    try:
        listener.start(args.mode)
    except KeyboardInterrupt:
        print("\nShutting down...")
        listener.stop()


if __name__ == "__main__":
    main()
