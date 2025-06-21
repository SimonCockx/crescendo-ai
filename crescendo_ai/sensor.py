"""
Module for interfacing with the 24GHz mmWave Human Static Presence Sensor.

This module provides functionality to detect human presence using the
Seeed Studio XIAO 24GHz mmWave sensor connected via serial interface.
"""

import serial
import time
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class PresenceSensor:
    """Class to interface with the 24GHz mmWave Human Static Presence Sensor."""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200, timeout: float = 1.0):
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
                timeout=self.timeout
            )
            self._is_connected = True
            logger.info(f"Connected to presence sensor on {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to presence sensor: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the sensor."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._is_connected = False
        logger.info("Disconnected from presence sensor")
    
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
            
        try:
            # Clear any pending data
            self._serial.reset_input_buffer()
            
            # Read a line of data
            raw_data = self._serial.readline().decode('utf-8').strip()
            
            if not raw_data:
                return {}
                
            # Parse the data - format depends on the specific sensor
            # This is a placeholder implementation - adjust based on actual sensor output
            parsed_data = self._parse_raw_data(raw_data)
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error reading from sensor: {e}")
            return {}
    
    def _parse_raw_data(self, raw_data: str) -> Dict[str, Any]:
        """
        Parse raw data from the sensor.
        
        Args:
            raw_data: Raw data string from the sensor
            
        Returns:
            Dict[str, Any]: Parsed data
        """
        # This is a placeholder implementation
        # Actual parsing depends on the specific sensor's data format
        # Example format: "presence:1,distance:120,signal:75"
        try:
            result = {}
            parts = raw_data.split(',')
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    # Try to convert to int or float if possible
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep as string
                    result[key.strip()] = value
                    
            return result
        except Exception as e:
            logger.error(f"Error parsing sensor data: {e}")
            return {}
    
    def is_presence_detected(self) -> bool:
        """
        Check if human presence is detected.
        
        Returns:
            bool: True if presence detected, False otherwise
        """
        data = self.read_data()
        # Assuming the sensor returns a 'presence' field with 1 for detected, 0 for not detected
        # Adjust based on actual sensor data format
        return bool(data.get('presence', 0))