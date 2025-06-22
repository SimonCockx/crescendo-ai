"""
24GHz mmWave Sensor Data Parser for Raspberry Pi
Parses incoming data from the Human Static Presence sensor
"""

import serial
import struct
import time

class MmWaveParser:
    def __init__(self, port='/dev/ttyAMA0', baudrate=256000):
        """
        Initialize the parser with serial connection

        Args:
            port (str): Serial port path (default: /dev/ttyAMA0)
            baudrate (int): Baud rate (default: 256000)
        """
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.frame_header = b'\xF4\xF3\xF2\xF1'
        self.frame_footer = b'\xF8\xF7\xF6\xF5'

        # Target state definitions
        self.target_states = {
            0x00: "No target",
            0x01: "Moving target",
            0x02: "Stationary target",
            0x03: "Moving & Stationary target"
        }

        # Data type definitions
        self.data_types = {
            0x01: "Engineering mode data",
            0x02: "Target basic information data"
        }

    def read_data(self):
        """
        Continuously read and parse data from the sensor
        """
        print("Starting to read mmWave sensor data...")
        print("Press Ctrl+C to stop\n")

        buffer = b''

        try:
            while True:
                # Read available data
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    buffer += data

                    # Process complete frames
                    while len(buffer) >= 4:
                        # Look for frame header
                        header_pos = buffer.find(self.frame_header)
                        if header_pos == -1:
                            # No header found, clear buffer
                            buffer = buffer[-3:]  # Keep last 3 bytes in case header is split
                            break

                        # Remove data before header
                        if header_pos > 0:
                            buffer = buffer[header_pos:]

                        # Check if we have enough data for frame length
                        if len(buffer) < 6:
                            break

                        # Extract frame length (2 bytes after header, little endian)
                        frame_length = struct.unpack('<H', buffer[4:6])[0]
                        total_frame_size = 4 + 2 + frame_length + 4  # header + length + data + footer

                        # Check if we have complete frame
                        if len(buffer) < total_frame_size:
                            break

                        # Extract and parse frame
                        frame = buffer[:total_frame_size]
                        self.parse_frame(frame, frame_length)

                        # Remove processed frame from buffer
                        buffer = buffer[total_frame_size:]

                time.sleep(0.01)  # Small delay to prevent excessive CPU usage

        except KeyboardInterrupt:
            print("\nStopping data collection...")
        finally:
            self.ser.close()

    def parse_frame(self, frame, data_length):
        """
        Parse a complete frame

        Args:
            frame (bytes): Complete frame data
            data_length (int): Length of data portion
        """
        try:
            # Verify frame structure
            if len(frame) < 10:  # Minimum frame size
                return

            header = frame[:4]
            length_bytes = frame[4:6]
            data_portion = frame[6:6+data_length]
            footer = frame[6+data_length:6+data_length+4]

            # Verify header and footer
            if header != self.frame_header or footer != self.frame_footer:
                print("Invalid frame header or footer")
                return

            if len(data_portion) < 3:  # Minimum data: type + head + at least 1 byte
                return

            # Parse data portion
            data_type = data_portion[0]
            head = data_portion[1]  # Should be 0xAA

            if head != 0xAA:
                print(f"Invalid data head: 0x{head:02X}, expected 0xAA")
                return

            print(f"Data Type: {self.data_types.get(data_type, f'Unknown (0x{data_type:02X})')}")

            if data_type == 0x02:  # Target basic information
                self.parse_basic_target_data(data_portion[2:])
            elif data_type == 0x01:  # Engineering mode
                self.parse_engineering_data(data_portion[2:])
            else:
                print(f"Unknown data type: 0x{data_type:02X}")

        except Exception as e:
            print(f"Error parsing frame: {e}")

    def parse_basic_target_data(self, target_data):
        """
        Parse basic target information data
        Expected format: target_status(1) + move_distance(2) + move_energy(1) +
                        static_distance(2) + static_energy(1) + detection_distance(2) + tail(1) + checksum(1)
        """
        if len(target_data) < 10:
            print("Insufficient data for basic target parsing")
            return

        try:
            # Unpack the target data (little endian format)
            target_status = target_data[0]
            move_distance = struct.unpack('<H', target_data[1:3])[0]  # cm
            move_energy = target_data[3]
            static_distance = struct.unpack('<H', target_data[4:6])[0]  # cm
            static_energy = target_data[6]
            detection_distance = struct.unpack('<H', target_data[7:9])[0]  # cm

            # Print parsed data
            print(f"  Target Status: {self.target_states.get(target_status, f'Unknown (0x{target_status:02X})')}")
            print(f"  Moving Target Distance: {move_distance} cm")
            print(f"  Moving Target Energy: {move_energy}")
            print(f"  Static Target Distance: {static_distance} cm")
            print(f"  Static Target Energy: {static_energy}")
            print(f"  Detection Distance: {detection_distance} cm")
            print("-" * 40)

        except Exception as e:
            print(f"Error parsing basic target data: {e}")

    def parse_engineering_data(self, target_data):
        """
        Parse engineering mode data (includes basic data + energy values for each distance gate)
        """
        print("  Engineering mode data detected")

        # First parse basic target data (same as above)
        if len(target_data) >= 10:
            self.parse_basic_target_data(target_data[:10])

            # Parse additional engineering data if available
            if len(target_data) > 10:
                eng_data = target_data[10:]
                print("  Additional Engineering Data:")

                # Skip tail and checksum from basic data, then parse engineering specifics
                if len(eng_data) >= 2:
                    max_move_gate = eng_data[0] if len(eng_data) > 0 else 0
                    max_static_gate = eng_data[1] if len(eng_data) > 1 else 0

                    print(f"    Max Movement Distance Gate: {max_move_gate}")
                    print(f"    Max Static Distance Gate: {max_static_gate}")

                    # Parse energy values for each gate if available
                    if len(eng_data) > 2:
                        energy_data = eng_data[2:]
                        print("    Distance Gate Energy Values:")

                        # The exact parsing depends on the number of gates configured
                        # This is a simplified version - you may need to adjust based on your configuration
                        gates = min(8, len(energy_data) // 2)  # Assume max 8 gates, 2 bytes per gate type

                        for i in range(gates):
                            if i * 2 + 1 < len(energy_data):
                                move_energy = energy_data[i * 2] if i * 2 < len(energy_data) else 0
                                static_energy = energy_data[i * 2 + 1] if i * 2 + 1 < len(energy_data) else 0
                                distance_m = i * 0.75  # Default 0.75m per gate
                                print(f"      Gate {i} ({distance_m:.2f}m): Move={move_energy}, Static={static_energy}")

        print("-" * 40)

def main():
    """
    Main function to run the parser
    """
    print("24GHz mmWave Sensor Data Parser")
    print("===============================")

    # You may need to adjust the port based on your Raspberry Pi setup
    # Common ports: /dev/ttyUSB0, /dev/ttyACM0, /dev/serial0
    try:
        parser = MmWaveParser(port='/dev/ttyAMA0', baudrate=256000)
        parser.read_data()
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
        print("Please check:")
        print("1. Sensor is connected properly")
        print("2. Correct port is specified (try /dev/ttyUSB0, /dev/ttyACM0, or /dev/serial0)")
        print("3. User has permission to access serial port (add user to dialout group)")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
