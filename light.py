from gpiozero import Button, OutputDevice
import time

# GPIO 18 -> TIP120 Base (Output)
# GPIO 17 -> Button (Input - Connected to Ground)
light = OutputDevice(18)
button = Button(17, pull_up=True) 

print("System Ready (Pull-Up Mode).")
print("Wiring: Button to GPIO 17 & Ground | TIP120 to GPIO 18")

try:
    while True:
        if button.is_pressed:
            # In pull-up mode, .is_pressed is True when the pin is Grounded
            print("STATUS: Button is [ PRESSED ] | Light: ON ")
            light.on()
        else:
            print("STATUS: Button is [  OPEN   ] | Light: OFF")
            light.off()
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping...")
