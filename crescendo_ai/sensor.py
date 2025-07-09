"""
Module for interfacing with the 24GHz mmWave Human Static Presence Sensor.

This module provides functionality to detect human presence using the
Seeed Studio XIAO 24GHz mmWave sensor connected via serial interface.
"""

import serial
import struct
import time
import logging
import threading
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class PresenceSensor:
    """Class to interface with the 24GHz mmWave Human Static Presence Sensor."""

    # Protocol constants
    FRAME_HEADER = b'\xFD\xFC\xFB\xFA'
    FRAME_FOOTER = b'\x04\x03\x02\x01'

    DATA_FRAME_HEADER = b'\xF4\xF3\xF2\xF1'
    DATA_FRAME_FOOTER = b'\xF8\xF7\xF6\xF5'

    # Target state definitions
    TARGET_STATES = {
        0x00: "No target",
        0x01: "Moving target",
        0x02: "Stationary target",
        0x03: "Moving & Stationary target"
    }

    # Data type definitions
    DATA_TYPES = {
        0x01: "Engineering mode data",
        0x02: "Target basic information data"
    }

    # Configuration command constants
    CMD_ENABLE_CONFIG = 0x00FF
    CMD_END_CONFIG = 0x00FE
    CMD_SET_DISTANCE_PARAMS = 0x0060
    CMD_SET_SENSITIVITY = 0x0064

    def __init__(self, port: str = '/dev/ttyAMA0', baudrate: int = 256000, timeout: float = 1.0):
        """
        Initialize the presence sensor.

        Args:
            port: Serial port the sensor is connected to
            baudrate: Baud rate for serial communication
            timeout: Serial read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._is_connected = False
        self._last_data: Dict[str, Any] = {}

        # Thread-related attributes
        self._read_thread: Optional[threading.Thread] = None
        self._thread_running = False
        self._presence_detected = False
        self._thread_lock = threading.Lock()

    def connect(self) -> bool:
        """
        Connect to the sensor.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self._is_connected = True
            logger.info(f"Connected to presence sensor on {self.port} at {self.baudrate} baud")

            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to presence sensor: {e}")
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the sensor."""
        # Stop the reading thread first
        self._stop_read_thread()

        if self._serial and self._serial.is_open:
            self._serial.close()
        self._is_connected = False
        logger.info("Disconnected from presence sensor")

    def start_reading(self) -> None:
        """Start the continuous reading thread."""
        if self._read_thread is not None and self._thread_running:
            logger.debug("Read thread already running")
            return

        self._thread_running = True
        self._read_thread = threading.Thread(
            target=self._read_thread_func,
            daemon=True,
            name="SensorReadThread"
        )
        self._read_thread.start()

    def _stop_read_thread(self) -> None:
        """Stop the continuous reading thread."""
        if self._read_thread is None or not self._thread_running:
            return

        self._thread_running = False
        if self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)  # Wait up to 2 seconds for thread to end
        self._read_thread = None
        logger.debug("Stopped sensor read thread")

    def _read_thread_func(self) -> None:
        """Thread function that continuously reads from the sensor."""
        logger.debug("Sensor read thread started")

        while self._thread_running and self.is_connected():
            try:
                data = self.read_data()

                # Update the presence state with thread safety
                with self._thread_lock:
                    self._presence_detected = bool(data.get('presence', False))

            except Exception as e:
                logger.error(f"Error in sensor read thread: {e}")

            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)

        logger.debug("Sensor read thread ended")

    def is_connected(self) -> bool:
        """
        Check if the sensor is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected and self._serial and self._serial.is_open

    def read_data(self) -> Dict[str, Any]:
        """
        Read and parse data from the sensor.

        Returns:
            Dict[str, Any]: Parsed sensor data or empty dict if error
        """
        if not self.is_connected():
            logger.error("Cannot read data: Sensor not connected")
            return {}

        # Parse the frame
        parsed_data = self._parse_data_frame(*self._read_frame(self.DATA_FRAME_HEADER, self.DATA_FRAME_FOOTER))

        if parsed_data:
            self._last_data = parsed_data
            return parsed_data

        # If we got here, we didn't get a complete frame
        # Return the last successful data or empty dict
        return self._last_data if self._last_data else {}

    def _read_frame(self, frame_header: bytes, frame_footer: bytes, delay_read = True) -> Tuple[bytes, int]:
        """
        Read frame from the sensor.

        Returns:
            Tuple[bytes, int]: frame data and frame length
        """
        if not self.is_connected():
            logger.error("Cannot read frame: Sensor not connected")
            return b'', 0

        try:
            buffer = b''
            start_time = time.time()

            # Try to read a complete frame with timeout
            while time.time() - start_time < self.timeout:
                if self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    buffer += data

                    # Process complete frames
                    while len(buffer) >= 4:
                        # Look for frame header
                        header_pos = buffer.find(frame_header)
                        if header_pos == -1:
                            # No header found, keep last 3 bytes in case header is split
                            buffer = buffer[-3:] if len(buffer) > 3 else buffer
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

                        # Extract frame
                        frame = buffer[:total_frame_size]

                        # Verify frame footer
                        if frame[-4:] != frame_footer:
                            logger.debug("Invalid frame footer in read_data")
                            # Skip this frame and continue looking
                            buffer = buffer[4:]  # Skip the header and continue
                            continue

                        # Parse the frame
                        return frame, frame_length

                if delay_read:
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.01)

            # If we got here, we didn't get a complete frame
            # Return the last successful data or empty dict
            return b'', 0

        except Exception as e:
            logger.error(f"Error reading from sensor: {e}")
            return b'', 0

    def _parse_data_frame(self, frame: bytes, data_length: int) -> Dict[str, Any]:
        """
        Parse a complete frame from the sensor.

        Args:
            frame: Complete frame data
            data_length: Length of data portion

        Returns:
            Dict[str, Any]: Parsed data or empty dict if error
        """
        try:
            # Verify frame structure
            if len(frame) < 10:  # Minimum frame size
                return {}

            header = frame[:4]
            length_bytes = frame[4:6]
            data_portion = frame[6:6+data_length]
            footer = frame[6+data_length:6+data_length+4]

            # Verify header and footer
            if header != self.DATA_FRAME_HEADER or footer != self.DATA_FRAME_FOOTER:
                logger.debug("Invalid frame header or footer")
                return {}

            if len(data_portion) < 3:  # Minimum data: type + head + at least 1 byte
                return {}

            # Parse data portion
            data_type = data_portion[0]
            head = data_portion[1]  # Should be 0xAA

            if head != 0xAA:
                logger.debug(f"Invalid data head: 0x{head:02X}, expected 0xAA")
                return {}

            result = {
                'data_type': data_type,
                'data_type_name': self.DATA_TYPES.get(data_type, f'Unknown (0x{data_type:02X})')
            }

            if data_type == 0x02:  # Target basic information
                target_data = self._parse_basic_target_data(data_portion[2:])
                result.update(target_data)
            elif data_type == 0x01:  # Engineering mode
                target_data = self._parse_engineering_data(data_portion[2:])
                result.update(target_data)

            return result

        except Exception as e:
            logger.error(f"Error parsing frame: {e}")
            return {}

    def _parse_basic_target_data(self, target_data: bytes) -> Dict[str, Any]:
        """
        Parse basic target information data.

        Args:
            target_data: Raw target data bytes

        Returns:
            Dict[str, Any]: Parsed target data
        """
        if len(target_data) < 10:
            logger.debug("Insufficient data for basic target parsing")
            return {}

        try:
            # Unpack the target data (little endian format)
            target_status = target_data[0]
            move_distance = struct.unpack('<H', target_data[1:3])[0]  # cm
            move_energy = target_data[3]
            static_distance = struct.unpack('<H', target_data[4:6])[0]  # cm
            static_energy = target_data[6]
            detection_distance = struct.unpack('<H', target_data[7:9])[0]  # cm

            return {
                'target_status': target_status,
                'target_state': self.TARGET_STATES.get(target_status, f'Unknown (0x{target_status:02X})'),
                'move_distance': move_distance,
                'move_energy': move_energy,
                'static_distance': static_distance,
                'static_energy': static_energy,
                'detection_distance': detection_distance,
                'presence': target_status > 0  # Any target (moving or stationary) indicates presence
            }

        except Exception as e:
            logger.error(f"Error parsing basic target data: {e}")
            return {}

    def _parse_engineering_data(self, target_data: bytes) -> Dict[str, Any]:
        """
        Parse engineering mode data.

        Args:
            target_data: Raw engineering data bytes

        Returns:
            Dict[str, Any]: Parsed engineering data
        """
        result = {}

        # First parse basic target data
        if len(target_data) >= 10:
            result = self._parse_basic_target_data(target_data[:10])

            # Parse additional engineering data if available
            if len(target_data) > 10:
                eng_data = target_data[10:]

                # Skip tail and checksum from basic data, then parse engineering specifics
                if len(eng_data) >= 2:
                    max_move_gate = eng_data[0] if len(eng_data) > 0 else 0
                    max_static_gate = eng_data[1] if len(eng_data) > 1 else 0

                    result['max_move_gate'] = max_move_gate
                    result['max_static_gate'] = max_static_gate

                    # Parse energy values for each gate if available
                    if len(eng_data) > 2:
                        energy_data = eng_data[2:]
                        gate_energies = []

                        # The exact parsing depends on the number of gates configured
                        gates = min(8, len(energy_data) // 2)  # Assume max 8 gates, 2 bytes per gate type

                        for i in range(gates):
                            if i * 2 + 1 < len(energy_data):
                                move_energy = energy_data[i * 2] if i * 2 < len(energy_data) else 0
                                static_energy = energy_data[i * 2 + 1] if i * 2 + 1 < len(energy_data) else 0
                                distance_m = i * 0.75  # Default 0.75m per gate

                                gate_energies.append({
                                    'gate': i,
                                    'distance_m': distance_m,
                                    'move_energy': move_energy,
                                    'static_energy': static_energy
                                })

                        result['gate_energies'] = gate_energies

        return result

    def configure(self, max_motion_gate: int = 8, max_static_gate: int = 8, 
                  no_one_duration: int = 5, motion_sensitivity: List[int] = None, 
                  static_sensitivity: List[int] = None) -> bool:
        """
        Configure the sensor parameters.

        Args:
            max_motion_gate: Maximum motion detection gate (1-8, each gate = 0.75m)
            max_static_gate: Maximum static detection gate (1-8, each gate = 0.75m)
            no_one_duration: Time in seconds before reporting no presence (0-65535)
            motion_sensitivity: List of sensitivity values for each gate (0-100)
            static_sensitivity: List of sensitivity values for each gate (0-100)

        Returns:
            bool: True if configuration successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot configure sensor: Not connected")
            return False

        try:
            # Enable configuration mode
            if not self._send_command(self.CMD_ENABLE_CONFIG, struct.pack('<H', 0x0001)):
                logger.error("Failed to enable configuration mode")
                return False

            # Set distance parameters
            data = bytearray()
            data.extend(struct.pack('<HI', 0x0000, max_motion_gate))  # Max motion gate
            data.extend(struct.pack('<HI', 0x0001, max_static_gate))  # Max static gate  
            data.extend(struct.pack('<HI', 0x0002, no_one_duration))  # No-one duration

            if not self._send_command(self.CMD_SET_DISTANCE_PARAMS, bytes(data)):
                logger.error("Failed to set distance parameters")
                self._send_command(self.CMD_END_CONFIG)  # Try to end config mode
                return False

            # Set sensitivity for individual gates if provided
            if motion_sensitivity and static_sensitivity:
                for gate in range(min(len(motion_sensitivity), len(static_sensitivity))):
                    data = bytearray()
                    data.extend(struct.pack('<HI', 0x0000, gate))  # Distance gate
                    data.extend(struct.pack('<HI', 0x0001, motion_sensitivity[gate]))  # Motion sensitivity
                    data.extend(struct.pack('<HI', 0x0002, static_sensitivity[gate]))  # Static sensitivity

                    if not self._send_command(self.CMD_SET_SENSITIVITY, bytes(data)):
                        logger.warning(f"Failed to set sensitivity for gate {gate}")

            # End configuration mode
            if not self._send_command(self.CMD_END_CONFIG):
                logger.error("Failed to end configuration mode")
                return False

            logger.info("Sensor configuration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error configuring sensor: {e}")
            # Try to end configuration mode even on failure
            try:
                self._send_command(self.CMD_END_CONFIG)
            except:
                pass
            return False

    def restart(self) -> bool:
        """Restart the sensor."""
        if not self.is_connected():
            logger.error("Cannot restart sensor: Not connected")
        return self._send_command(0x00A3)

    def _send_command(self, command_word: int, command_data: bytes = b'') -> bool:
        """
        Send a command to the sensor and wait for ACK response.

        Args:
            command_word: Command word to send
            command_data: Command data bytes

        Returns:
            bool: True if command acknowledged successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot send command: Sensor not connected")
            return False

        # Flag to track if we've already retried
        retry_attempted = False

        while True:
            try:
                # Create command frame
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

                # Clear input buffer
                self._serial.reset_input_buffer()

                # Send command
                self._serial.write(frame)
                logger.debug(f"Sent command 0x{command_word:04X}: {frame.hex().upper()}")

                # Read response header (4 bytes)
                response_frame, response_length = self._read_frame(self.FRAME_HEADER, self.FRAME_FOOTER, False)
                logger.debug(f"Response: {response_frame.hex().upper()}")

                # Extract ACK command word and status
                ack_cmd = struct.unpack('<H', response_frame[6:8])[0]
                expected_ack = command_word | 0x0100

                if ack_cmd != expected_ack:
                    logger.debug(f"Unexpected ACK command: 0x{ack_cmd:04X}, expected: 0x{expected_ack:04X}")
                    return False

                # Check status (0 = success, 1 = failure)
                status = struct.unpack('<H', response_frame[8:10])[0]
                return status == 0

            except struct.error as e:
                if "unpack requires a buffer of 2 bytes" in str(e) and not retry_attempted:
                    logger.warning("Encountered 'unpack requires a buffer of 2 bytes' error. Restarting sensor and retrying...")
                    retry_attempted = True

                    # Restart the sensor
                    self.restart()

                    # Wait a bit before retrying
                    time.sleep(2.0)

                    # Continue to retry
                    continue
                else:
                    # Either it's a different error or we've already retried
                    logger.error(f"Error sending command: {e}")
                    return False
            except Exception as e:
                logger.error(f"Error sending command: {e}")
                return False

    def is_presence_detected(self) -> bool:
        """
        Check if human presence is detected.

        This method returns the current presence state as detected by the
        continuous reading thread. It does not perform a direct sensor read.

        Returns:
            bool: True if presence detected, False otherwise
        """
        with self._thread_lock:
            return self._presence_detected

    def is_static_target_detected(self) -> bool:
        """
        Check if a stationary target is detected.

        Returns:
            bool: True if a stationary target is detected, False otherwise
        """
        with self._thread_lock:
            target_status = self._last_data.get('target_status', 0)
            # Target status 0x02 (stationary) or 0x03 (moving & stationary)
            return target_status in [0x02, 0x03]

    def is_moving_target_detected(self) -> bool:
        """
        Check if a moving target is detected.

        Returns:
            bool: True if a moving target is detected, False otherwise
        """
        with self._thread_lock:
            target_status = self._last_data.get('target_status', 0)
            # Target status 0x01 (moving) or 0x03 (moving & stationary)
            return target_status in [0x01, 0x03]

    def get_static_energy(self) -> int:
        """
        Get the energy level of the static target.

        Returns:
            int: Energy level (0-100) of the static target, or 0 if no static target
        """
        with self._thread_lock:
            return self._last_data.get('static_energy', 0)

    def get_move_energy(self) -> int:
        """
        Get the energy level of the moving target.

        Returns:
            int: Energy level (0-100) of the moving target, or 0 if no moving target
        """
        with self._thread_lock:
            return self._last_data.get('move_energy', 0)
