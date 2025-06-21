"""
Main module for the Crescendo AI system.

This module coordinates all components of the system:
- Presence sensor for detecting human presence
- USB relay for controlling the speaker power
- Audio player for playing background music

The system plays music when human presence is detected and stops
when no presence is detected.
"""

import logging
import time
import os
import sys
from typing import Optional

from crescendo_ai.sensor import PresenceSensor
from crescendo_ai.relay import USBRelay
from crescendo_ai.audio import AudioPlayer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crescendo.log')
    ]
)

logger = logging.getLogger(__name__)

class CrescendoSystem:
    """Main class that coordinates all components of the Crescendo AI system."""
    
    def __init__(
        self,
        sensor_port: str = '/dev/ttyUSB0',
        music_dir: str = 'music',
        check_interval: float = 1.0,
        presence_timeout: float = 30.0
    ):
        """
        Initialize the Crescendo system.
        
        Args:
            sensor_port: Serial port for the presence sensor
            music_dir: Directory containing music files
            check_interval: Interval in seconds between presence checks
            presence_timeout: Time in seconds to wait after last detection before stopping music
        """
        self.sensor_port = sensor_port
        self.music_dir = music_dir
        self.check_interval = check_interval
        self.presence_timeout = presence_timeout
        
        # Initialize components
        self.sensor = PresenceSensor(port=sensor_port)
        self.relay = USBRelay()
        self.audio_player = AudioPlayer(music_dir=music_dir)
        
        # State variables
        self.running = False
        self.last_presence_time: Optional[float] = None
    
    def initialize(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            bool: True if all components initialized successfully, False otherwise
        """
        logger.info("Initializing Crescendo system...")
        
        # Create music directory if it doesn't exist
        if not os.path.exists(self.music_dir):
            logger.info(f"Creating music directory: {self.music_dir}")
            os.makedirs(self.music_dir)
        
        # Initialize sensor
        sensor_ok = self.sensor.connect()
        if not sensor_ok:
            logger.error("Failed to initialize presence sensor")
            return False
        
        # Initialize relay
        relay_ok = self.relay.connect()
        if not relay_ok:
            logger.warning("Failed to initialize USB relay - continuing without relay control")
        
        # Initialize audio player
        audio_ok = self.audio_player.initialize()
        if not audio_ok:
            logger.error("Failed to initialize audio player")
            return False
        
        logger.info("Crescendo system initialized successfully")
        return True
    
    def shutdown(self) -> None:
        """Shutdown all system components."""
        logger.info("Shutting down Crescendo system...")
        
        # Stop music and turn off relay
        if self.audio_player.is_initialized():
            self.audio_player.stop()
            self.audio_player.shutdown()
        
        if self.relay.is_connected():
            self.relay.turn_off()
            self.relay.disconnect()
        
        self.sensor.disconnect()
        
        logger.info("Crescendo system shut down")
    
    def run(self) -> None:
        """Run the main system loop."""
        if not self.initialize():
            logger.error("Failed to initialize system. Exiting.")
            return
        
        self.running = True
        logger.info("Starting Crescendo system main loop")
        
        try:
            while self.running:
                self._check_presence_and_update()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def _check_presence_and_update(self) -> None:
        """Check for presence and update system state accordingly."""
        try:
            presence_detected = self.sensor.is_presence_detected()
            
            if presence_detected:
                # Update the last presence time
                self.last_presence_time = time.time()
                
                # If music is not playing, turn on relay and start music
                if not self.audio_player.is_playing():
                    logger.info("Presence detected - starting music")
                    
                    # Turn on the relay (speaker power)
                    if self.relay.is_connected():
                        self.relay.turn_on()
                    
                    # Start playing music
                    self.audio_player.play()
            else:
                # Check if we should stop music based on timeout
                if (self.last_presence_time is not None and 
                    time.time() - self.last_presence_time > self.presence_timeout):
                    
                    # If music is playing, stop it and turn off relay
                    if self.audio_player.is_playing():
                        logger.info("No presence detected for timeout period - stopping music")
                        
                        # Stop music
                        self.audio_player.stop()
                        
                        # Turn off the relay (speaker power)
                        if self.relay.is_connected():
                            self.relay.turn_off()
                        
                        # Reset last presence time
                        self.last_presence_time = None
                
        except Exception as e:
            logger.error(f"Error checking presence: {e}")


def main():
    """Main entry point for the Crescendo system."""
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Crescendo AI - Presence-activated music player")
    parser.add_argument('--sensor-port', default='/dev/ttyUSB0', help='Serial port for the presence sensor')
    parser.add_argument('--music-dir', default='music', help='Directory containing music files')
    parser.add_argument('--check-interval', type=float, default=1.0, help='Interval in seconds between presence checks')
    parser.add_argument('--presence-timeout', type=float, default=30.0, help='Time in seconds to wait after last detection before stopping music')
    
    args = parser.parse_args()
    
    # Create and run the system
    system = CrescendoSystem(
        sensor_port=args.sensor_port,
        music_dir=args.music_dir,
        check_interval=args.check_interval,
        presence_timeout=args.presence_timeout
    )
    
    system.run()


if __name__ == "__main__":
    main()