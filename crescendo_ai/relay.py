"""Class for controlling a USB relay device."""

import hid
import logging

logger = logging.getLogger(__name__)

class USBRelay:
    """Class to control a USB relay device."""
    
    # Default USB relay vendor and product IDs
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
        self.turned_on = False
        
    def connect(self) -> bool:
        """
        Connect to the USB relay device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._device = hid.Device(vid=self.vendor_id, pid=self.product_id)
            self._is_connected = True
            logger.info("Connected to USB relay device")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"Error connecting to USB relay device: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the USB relay device."""
        if self._device:
            self._device.close()
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
            # For this specific relay, channel 1 = 0x00, channel 2 = 0x01
            relay_channel = channel - 1
            cmd = bytes([0xFF, 0x01, relay_channel])
            self._device.write(cmd)
            self.turned_on = True
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
            # For this specific relay, channel 1 = 0x00, channel 2 = 0x01
            relay_channel = channel - 1
            cmd = bytes([0xFF, 0x00, relay_channel])
            self._device.write(cmd)
            self.turned_on = False
            logger.info(f"Turned OFF relay channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Error turning off relay: {e}")
            return False

    def is_turned_on(self) -> bool:
        """
        Check if the relay is currently turned on.
        
        Returns:
            bool: True if the relay is on, False otherwise
        """
        return self.turned_on