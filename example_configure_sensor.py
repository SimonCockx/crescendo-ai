#!/usr/bin/env python3
"""
24GHz mmWave Sensor for XIAO Configuration Script
Configures detection parameters via serial communication
"""

import serial
import time
import struct
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class SensorConfig:
    """Configuration parameters for the mmWave sensor"""
    max_motion_gate: int = 8  # 1-8, each gate = 0.75m
    max_static_gate: int = 8  # 1-8, each gate = 0.75m
    no_one_duration: int = 5  # seconds, 0-65535
    motion_sensitivity: List[int] = None  # per gate, 0-100
    static_sensitivity: List[int] = None  # per gate, 0-100
    distance_resolution: int = 0  # 0=0.75m, 1=0.2m per gate
    baud_rate: int = 256000  # serial baud rate
    bluetooth_enabled: bool = True
    bluetooth_password: str = "HiLink"


class MMWaveConfigurator:
    """Configure 24GHz mmWave Sensor via serial communication"""

    # Protocol constants
    FRAME_HEADER = [0xFD, 0xFC, 0xFB, 0xFA]
    FRAME_FOOTER = [0x04, 0x03, 0x02, 0x01]

    # Command words
    CMD_ENABLE_CONFIG = 0x00FF
    CMD_END_CONFIG = 0x00FE
    CMD_SET_DISTANCE_PARAMS = 0x0060
    CMD_READ_PARAMS = 0x0061
    CMD_ENABLE_ENGINEERING = 0x0062
    CMD_DISABLE_ENGINEERING = 0x0063
    CMD_SET_SENSITIVITY = 0x0064
    CMD_READ_VERSION = 0x00A0
    CMD_SET_BAUD_RATE = 0x00A1
    CMD_FACTORY_RESET = 0x00A2
    CMD_RESTART = 0x00A3
    CMD_BLUETOOTH_CONTROL = 0x00A4
    CMD_GET_MAC = 0x00A5
    CMD_BLUETOOTH_AUTH = 0x00A8
    CMD_SET_BT_PASSWORD = 0x00A9
    CMD_SET_DISTANCE_RESOLUTION = 0x00AA
    CMD_GET_DISTANCE_RESOLUTION = 0x00AB

    def __init__(self, port: str, baud_rate: int = 256000, timeout: float = 1.0):
        """Initialize serial connection"""
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None

    def connect(self) -> bool:
        """Connect to the sensor"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            print(f"Connected to {self.port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from sensor"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Disconnected")

    def _create_command_frame(self, command_word: int, command_data: bytes = b'') -> bytes:
        """Create a command frame with proper protocol format"""
        frame = bytearray()

        # Frame header
        frame.extend(self.FRAME_HEADER)

        # Data length (command word + command data)
        data_length = 2 + len(command_data)
        frame.extend(struct.pack('<H', data_length))

        # Command word (little endian)
        frame.extend(struct.pack('<H', command_word))

        # Command data
        frame.extend(command_data)

        # Frame footer
        frame.extend(self.FRAME_FOOTER)

        return bytes(frame)

    def _send_command(self, command_word: int, command_data: bytes = b'') -> Optional[bytes]:
        """Send command and wait for ACK response"""
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not open")
            return None

        frame = self._create_command_frame(command_word, command_data)

        # Clear input buffer
        self.serial_conn.reset_input_buffer()

        # Send command
        self.serial_conn.write(frame)
        print(f"Sent command 0x{command_word:04X}: {frame.hex().upper()}")

        # Wait for response
        time.sleep(0.1)

        # Read response
        response = self.serial_conn.read(1000)  # Read up to 1000 bytes
        if response:
            print(f"Received: {response.hex().upper()}")
            return response
        else:
            print("No response received")
            return None

    def _parse_ack_response(self, response: bytes, expected_cmd: int) -> bool:
        """Parse ACK response and check if command was successful"""
        if len(response) < 12:  # Minimum ACK frame size
            return False

        # Check frame header and footer
        if (response[:4] != bytes(self.FRAME_HEADER) or
                response[-4:] != bytes(self.FRAME_FOOTER)):
            return False

        # Extract ACK command word and status
        ack_cmd = struct.unpack('<H', response[6:8])[0]
        expected_ack = expected_cmd | 0x0100

        if ack_cmd != expected_ack:
            print(f"Unexpected ACK command: 0x{ack_cmd:04X}, expected: 0x{expected_ack:04X}")
            return False

        # Check status (0 = success, 1 = failure)
        status = struct.unpack('<H', response[8:10])[0]
        return status == 0

    def enable_configuration(self) -> bool:
        """Enable configuration mode"""
        print("Enabling configuration mode...")
        response = self._send_command(self.CMD_ENABLE_CONFIG, struct.pack('<H', 0x0001))
        if response and self._parse_ack_response(response, self.CMD_ENABLE_CONFIG):
            print("Configuration mode enabled")
            return True
        print("Failed to enable configuration mode")
        return False

    def end_configuration(self) -> bool:
        """End configuration mode"""
        print("Ending configuration mode...")
        response = self._send_command(self.CMD_END_CONFIG)
        if response and self._parse_ack_response(response, self.CMD_END_CONFIG):
            print("Configuration mode ended")
            return True
        print("Failed to end configuration mode")
        return False

    def set_distance_parameters(self, max_motion_gate: int, max_static_gate: int, no_one_duration: int) -> bool:
        """Set maximum distance gates and no-one duration"""
        print(
            f"Setting distance parameters: motion={max_motion_gate}, static={max_static_gate}, duration={no_one_duration}s")

        # Parameter words and values
        data = bytearray()
        data.extend(struct.pack('<HI', 0x0000, max_motion_gate))  # Max motion gate
        data.extend(struct.pack('<HI', 0x0001, max_static_gate))  # Max static gate
        data.extend(struct.pack('<HI', 0x0002, no_one_duration))  # No-one duration

        response = self._send_command(self.CMD_SET_DISTANCE_PARAMS, bytes(data))
        if response and self._parse_ack_response(response, self.CMD_SET_DISTANCE_PARAMS):
            print("Distance parameters set successfully")
            return True
        print("Failed to set distance parameters")
        return False

    def set_gate_sensitivity(self, gate: int, motion_sensitivity: int, static_sensitivity: int) -> bool:
        """Set sensitivity for a specific distance gate (0xFFFF for all gates)"""
        print(f"Setting gate {gate} sensitivity: motion={motion_sensitivity}, static={static_sensitivity}")

        data = bytearray()
        data.extend(struct.pack('<HI', 0x0000, gate))  # Distance gate
        data.extend(struct.pack('<HI', 0x0001, motion_sensitivity))  # Motion sensitivity
        data.extend(struct.pack('<HI', 0x0002, static_sensitivity))  # Static sensitivity

        response = self._send_command(self.CMD_SET_SENSITIVITY, bytes(data))
        if response and self._parse_ack_response(response, self.CMD_SET_SENSITIVITY):
            print(f"Gate {gate} sensitivity set successfully")
            return True
        print(f"Failed to set gate {gate} sensitivity")
        return False

    def set_all_gates_sensitivity(self, motion_sensitivity: int, static_sensitivity: int) -> bool:
        """Set sensitivity for all distance gates at once"""
        return self.set_gate_sensitivity(0xFFFF, motion_sensitivity, static_sensitivity)

    def read_parameters(self) -> Optional[dict]:
        """Read current sensor parameters"""
        print("Reading sensor parameters...")
        response = self._send_command(self.CMD_READ_PARAMS)

        if not response or not self._parse_ack_response(response, self.CMD_READ_PARAMS):
            print("Failed to read parameters")
            return None

        # Parse parameter data (simplified parsing)
        if len(response) >= 20:
            # Basic parameter extraction
            max_gates = response[11] if len(response) > 11 else 0
            motion_gate = response[12] if len(response) > 12 else 0
            static_gate = response[13] if len(response) > 13 else 0

            params = {
                'max_gates': max_gates,
                'motion_gate': motion_gate,
                'static_gate': static_gate,
                'raw_response': response.hex()
            }
            print(f"Parameters read: {params}")
            return params

        return None

    def enable_engineering_mode(self) -> bool:
        """Enable engineering mode for detailed energy reporting"""
        print("Enabling engineering mode...")
        response = self._send_command(self.CMD_ENABLE_ENGINEERING)
        if response and self._parse_ack_response(response, self.CMD_ENABLE_ENGINEERING):
            print("Engineering mode enabled")
            return True
        print("Failed to enable engineering mode")
        return False

    def disable_engineering_mode(self) -> bool:
        """Disable engineering mode"""
        print("Disabling engineering mode...")
        response = self._send_command(self.CMD_DISABLE_ENGINEERING)
        if response and self._parse_ack_response(response, self.CMD_DISABLE_ENGINEERING):
            print("Engineering mode disabled")
            return True
        print("Failed to disable engineering mode")
        return False

    def factory_reset(self) -> bool:
        """Reset sensor to factory defaults"""
        print("Performing factory reset...")
        response = self._send_command(self.CMD_FACTORY_RESET)
        if response and self._parse_ack_response(response, self.CMD_FACTORY_RESET):
            print("Factory reset completed")
            return True
        print("Failed to perform factory reset")
        return False

    def restart_sensor(self) -> bool:
        """Restart the sensor"""
        print("Restarting sensor...")
        response = self._send_command(self.CMD_RESTART)
        if response and self._parse_ack_response(response, self.CMD_RESTART):
            print("Sensor restart initiated")
            time.sleep(2)  # Wait for restart
            return True
        print("Failed to restart sensor")
        return False

    def configure_sensor(self, config: SensorConfig) -> bool:
        """Apply complete sensor configuration"""
        print("Starting sensor configuration...")

        try:
            # Enable configuration mode
            if not self.enable_configuration():
                return False

            # Set distance parameters
            if not self.set_distance_parameters(
                    config.max_motion_gate,
                    config.max_static_gate,
                    config.no_one_duration
            ):
                return False

            # Set sensitivity for individual gates if provided
            if config.motion_sensitivity and config.static_sensitivity:
                for gate in range(min(len(config.motion_sensitivity), len(config.static_sensitivity))):
                    if not self.set_gate_sensitivity(
                            gate,
                            config.motion_sensitivity[gate],
                            config.static_sensitivity[gate]
                    ):
                        print(f"Warning: Failed to set sensitivity for gate {gate}")

            # End configuration mode
            if not self.end_configuration():
                return False

            print("Sensor configuration completed successfully!")
            return True

        except Exception as e:
            print(f"Configuration failed: {e}")
            # Try to end configuration mode even on failure
            try:
                self.end_configuration()
            except:
                pass
            return False


def main():
    """Example usage of the mmWave sensor configurator"""

    # Configuration parameters
    config = SensorConfig(
        max_motion_gate=6,  # Detect motion up to 4.5m
        max_static_gate=4,  # Detect stationary targets up to 3.0m
        no_one_duration=10,  # 10 second delay before reporting "no one"
        motion_sensitivity=[50, 50, 40, 30, 20, 15, 15, 15, 15],  # Per gate
        static_sensitivity=[0, 0, 40, 40, 30, 30, 20, 20, 20],  # Per gate (0,1 not settable)
    )

    # Initialize configurator
    sensor = MMWaveConfigurator(port="COM3")  # Change to your port (e.g., "/dev/ttyAMA0" on Linux)

    try:
        # Connect to sensor
        if not sensor.connect():
            return

        # Read current parameters
        print("\n=== Current Parameters ===")
        current_params = sensor.read_parameters()

        # Apply new configuration
        print("\n=== Applying New Configuration ===")
        if sensor.configure_sensor(config):
            print("Configuration applied successfully!")
        else:
            print("Configuration failed!")

        # Read parameters again to verify
        print("\n=== Verification ===")
        new_params = sensor.read_parameters()

        # Optional: Enable engineering mode for debugging
        # sensor.enable_engineering_mode()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sensor.disconnect()


if __name__ == "__main__":
    main()
