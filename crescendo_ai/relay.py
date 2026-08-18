"""Class for controlling a USB relay device."""

import hid
import logging
import time

logger = logging.getLogger(__name__)

class USBRelay:
    """Class to control a USB relay device."""

    # Default USB relay vendor and product IDs
    DEFAULT_VENDOR_ID = 0x16c0
    DEFAULT_PRODUCT_ID = 0x05df

    # Minimum time between reconnect attempts, to avoid hammering a device
    # that is genuinely gone
    RECONNECT_INTERVAL = 10.0

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
        self._last_reconnect_attempt = 0.0

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

    def ensure_connected(self) -> bool:
        """
        Make sure the relay is connected, (re)connecting if it isn't.

        Reconnect attempts are rate-limited so a permanently missing device
        doesn't get hammered with connection attempts every loop iteration.

        Returns:
            bool: True if connected (already, or after reconnecting)
        """
        if self.is_connected():
            return True

        now = time.time()
        if now - self._last_reconnect_attempt < self.RECONNECT_INTERVAL:
            return False

        self._last_reconnect_attempt = now
        logger.info("Attempting to reconnect USB relay...")
        return self.connect()


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
            cmd = bytes([0x00, 0xFF, channel])
            self._device.write(cmd)
            self.turned_on = True
            logger.info(f"Turned ON relay channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Error turning on relay: {e}")
            # The device likely went away; mark disconnected so the next
            # loop iteration retries via ensure_connected() instead of
            # failing silently forever.
            self._is_connected = False
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
            cmd = bytes([0x00, 0xFD, channel])
            self._device.write(cmd)
            self.turned_on = False
            logger.info(f"Turned OFF relay channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Error turning off relay: {e}")
            self._is_connected = False
            return False

    def is_turned_on(self) -> bool:
        """
        Check if the relay is currently turned on.
        
        Returns:
            bool: True if the relay is on, False otherwise
        """
        return self.turned_on