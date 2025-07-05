import hid
import time

VENDOR_ID = 0x16c0
PRODUCT_ID = 0x05df

def open_relay_device():
    device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
    return device

def relay_on(device):
    # Relay ON (Relay 1): 0xFF
    device.write(bytes([0x00, 0xFF, 0x01]))

def relay_off(device):
    # Relay OFF (Relay 1): 0xFD
    device.write(bytes([0x00, 0xFD, 0x01]))

def main():
    print("Connecting to relay...")
    try:
        device = open_relay_device()
    except Exception as e:
        print(f"Failed to open relay: {e}")
        return

    print("Turning ON relay for 2 seconds...")
    relay_on(device)
    time.sleep(2)

    print("Turning OFF relay.")
    relay_off(device)

    device.close()

if __name__ == "__main__":
    main()
