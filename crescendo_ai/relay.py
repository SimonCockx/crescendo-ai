"""
Module for controlling a USB relay to turn on/off a speaker.

This module provides functionality to control a USB relay device
that can switch the power to a connected speaker.
"""

import usb.core
import usb.util
import logging
import time
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class USBRelay:
    """Class to control a USB relay device."""
    
    # Default USB relay vendor and product IDs
    # These may need to be adjusted based on the specific USB relay used
    DEFAULT_VENDOR_ID = 0x16c0
    DEFAULT_PRODUCT_ID = 0x05df
    
    def __init__(self, vendor_id: int = DEFAULT_VENDOR_ID, product_id: int = DEFAULT_PRODUCT_ID):
        """
        Initialize the USB relay controller.
        
        Args:
            vendor_id: USB vendor ID of the relay device
            product_id: USB product ID of the relay device
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self._device = None
        self._is_connected = False
        
    def connect(self) -> bool:
        """
        Connect to the USB relay device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Find the USB device
            self._device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
            
            if self._device is None:
                logger.error(f"USB relay device not found (VID:{self.vendor_id:04x}, PID:{self.product_id:04x})")
                return False
                
            # If the device is in use by the kernel, detach it
            if self._device.is_kernel_driver_active(0):
                try:
                    self._device.detach_kernel_driver(0)
                except usb.core.USBError as e:
                    logger.error(f"Could not detach kernel driver: {e}")
                    return False
            
            # Set the active configuration
            try:
                self._device.set_configuration()
            except usb.core.USBError as e:
                logger.error(f"Could not set configuration: {e}")
                return False
                
            self._is_connected = True
            logger.info("Connected to USB relay device")
            return True
            
        except usb.core.USBError as e:
            logger.error(f"USB error when connecting to relay: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the USB relay device."""
        self._device = None
        self._is_connected = False
        logger.info("Disconnected from USB relay device")
    
    def is_connected(self) -> bool:
        """
        Check if the relay is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected and self._device is not None
    
    def turn_on(self, channel: int = 1) -> bool:
        """
        Turn on the specified relay channel.
        
        Args:
            channel: Relay channel number (usually 1 for single-channel relays)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot turn on relay: Device not connected")
            return False
            
        try:
            # Command format depends on the specific USB relay
            # This is a common format, but may need adjustment
            cmd = bytes([0x01, channel, 0x01])
            self._send_command(cmd)
            logger.info(f"Turned ON relay channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Error turning on relay: {e}")
            return False
    
    def turn_off(self, channel: int = 1) -> bool:
        """
        Turn off the specified relay channel.
        
        Args:
            channel: Relay channel number (usually 1 for single-channel relays)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot turn off relay: Device not connected")
            return False
            
        try:
            # Command format depends on the specific USB relay
            # This is a common format, but may need adjustment
            cmd = bytes([0x01, channel, 0x00])
            self._send_command(cmd)
            logger.info(f"Turned OFF relay channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Error turning off relay: {e}")
            return False
    
    def _send_command(self, cmd: bytes) -> None:
        """
        Send a command to the USB relay.
        
        Args:
            cmd: Command bytes to send
        """
        # The endpoint and request type may vary depending on the specific USB relay
        # These are common values, but may need adjustment
        self._device.ctrl_transfer(
            bmRequestType=0x21,  # Host to device, class, interface
            bRequest=0x09,       # SET_REPORT
            wValue=0x0300,       # Report type and ID
            wIndex=0,            # Interface
            data_or_wLength=cmd  # Command data
        )