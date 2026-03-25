#!/bin/bash
# Setup script for Raspberry Pi Bluetooth Speaker

echo "=== Raspberry Pi Bluetooth Speaker Setup ==="
echo ""

# Update package list
echo "Updating packages..."
sudo apt update

# Install Bluetooth utilities
echo "Installing Bluetooth utilities..."
sudo apt install -y bluetooth bluez bluez-tools pulseaudio-module-bluetooth

# Install audio players
echo "Installing audio players..."
sudo apt install -y mpg123 ffmpeg alsa-utils

# Install text-to-speech (optional)
echo "Installing text-to-speech..."
sudo apt install -y espeak

# Enable and start Bluetooth service
echo "Enabling Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Add user to bluetooth group
echo "Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

# Configure PulseAudio for Bluetooth
echo "Configuring PulseAudio..."
mkdir -p ~/.config/pulse

# Restart PulseAudio
pulseaudio --kill 2>/dev/null
pulseaudio --start

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Reboot your Pi: sudo reboot"
echo "2. Put your Bluetooth speaker in pairing mode"
echo "3. Run: python3 bluetooth_speaker.py --setup"
echo ""
