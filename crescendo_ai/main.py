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

from crescendo_ai.sensor import PresenceSensor
from crescendo_ai.relay import USBRelay
from crescendo_ai.audio import AudioPlayer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
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
        sensor_port: str = '/dev/ttyAMA0',
        music_dir: str = 'music',
        check_interval: float = 1.0,
        relay_off_delay: float = 15.0 * 60.0,
    ):
        """
        Initialize the Crescendo system.

        Args:
            sensor_port: Serial port for the presence sensor
            music_dir: Directory containing music files
            check_interval: Interval in seconds between presence checks
            relay_off_delay: Delay in seconds before turning off the relay after no presence is detected
        """
        self.sensor_port = sensor_port
        self.music_dir = music_dir
        self.check_interval = check_interval
        self.relay_off_delay = relay_off_delay

        # Initialize components
        self.sensor = PresenceSensor(port=sensor_port)
        self.relay = USBRelay()
        self.audio_player = AudioPlayer(music_dir=music_dir)

        # State variables
        self.running = False
        self.last_presence_time = None

        # Dynamic detection state variables
        self.dynamic_detection_history = []  # List of timestamps when dynamic motion was detected
        self.dynamic_detection_active_until = None  # Timestamp until dynamic detection is considered active
        self.dynamic_detection_duration = 300  # Duration in seconds (5 minutes) to keep dynamic detection active

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

        # Configure sensor with default settings
        try:
            config_ok = self.sensor.configure(
                max_motion_gate=8,  # Detect motion up to 6m
                max_static_gate=8,  # Detect stationary targets up to 6m
                no_one_duration=10,  # 10 second delay before reporting "no one"
                motion_sensitivity=[80, 80, 75, 75, 75, 70, 70, 70],  # Per gate
                static_sensitivity=[80, 80, 75, 75, 75, 70, 70, 70]  # Per gate (0,1 not settable)
            )
            if not config_ok:
                logger.warning("Failed to configure sensor - continuing with default configuration")
        except Exception as e:
            logger.warning(f"Error configuring sensor: {e} - continuing with default configuration")

        self.sensor.start_reading()

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
        """Check for presence and update system state accordingly using the robust detection algorithm."""
        try:
            current_time = time.time()

            # Check for dynamic (moving) target
            dynamic_detected = self.sensor.is_moving_target_detected()

            # Update dynamic detection history
            if dynamic_detected:
                self.dynamic_detection_history.append(current_time)

            # Remove entries older than 3 seconds from history
            self.dynamic_detection_history = [t for t in self.dynamic_detection_history 
                                             if current_time - t <= 3.0]

            # Check if we have continuous dynamic detection for 3 seconds
            dynamic_detection_active = False
            continuous_detection = len(self.dynamic_detection_history) >= 3

            if continuous_detection:
                # If we have at least 3 detections in the last 3 seconds, activate dynamic detection
                dynamic_detection_active = True
                # Set the dynamic detection to be active for the next 5 minutes
                self.dynamic_detection_active_until = current_time + self.dynamic_detection_duration
                logger.debug(f"Dynamic detection activated: continuous motion detected for 3+ seconds (active until {time.ctime(self.dynamic_detection_active_until)})")
            elif self.dynamic_detection_active_until and current_time < self.dynamic_detection_active_until:
                # Dynamic detection is still active from a previous detection
                dynamic_detection_active = True
                remaining_time = int(self.dynamic_detection_active_until - current_time)
                logger.debug(f"Dynamic detection still active: within 5-minute window (expires in {remaining_time} seconds)")
            else:
                logger.debug(f"Dynamic detection inactive: no continuous motion detected and not within 5-minute window")

            # Check for static target
            static_detected = self.sensor.is_static_target_detected()
            if static_detected:
                logger.debug(f"Static target detected: energy level {self.sensor.get_static_energy()}")
            else:
                logger.debug(f"No static target detected")

            # Robust presence detection: both dynamic detection must be active AND static target must be detected
            robust_presence_detected = dynamic_detection_active and static_detected

            # Track previous state to detect changes
            was_presence_detected = self.last_presence_time is not None and (current_time - self.last_presence_time) < self.relay_off_delay

            if robust_presence_detected:
                self.last_presence_time = current_time

                # Log detailed presence detection information
                if not was_presence_detected:
                    logger.info("PRESENCE DETECTED: Both conditions met for robust detection")
                    logger.info(f"  - Dynamic detection: {'Continuous motion for 3+ seconds' if continuous_detection else 'Within 5-minute window'}")
                    logger.info(f"  - Static detection: Energy level {self.sensor.get_static_energy()}")

                # If music is not playing, turn on relay and start music
                if self.relay.is_connected() and not self.relay.is_turned_on():
                    logger.info("Robust presence detected - turning on relay")
                    # Turn on the relay (speaker power)
                    self.relay.turn_on()

                if not self.audio_player.is_playing():
                    logger.info("Robust presence detected - starting music")
                    # Start playing music
                    self.audio_player.play()
            else:
                # Log detailed information about why presence was not detected
                if was_presence_detected:
                    logger.info("PRESENCE LOST: Robust detection conditions no longer met")
                    if not dynamic_detection_active:
                        logger.info("  - Dynamic detection inactive: No continuous motion and outside 5-minute window")
                    if not static_detected:
                        logger.info("  - Static detection inactive: No stationary target detected")

                # Regular debug logging
                logger.debug(f"No robust presence - Dynamic: {dynamic_detection_active}, Static: {static_detected}")

                # If no robust presence is detected and music is playing, stop it
                if self.audio_player.is_playing():
                    logger.info("No robust presence detected - stopping music")
                    # Stop music
                    self.audio_player.stop()

                relay_timeout_is_complete = (self.last_presence_time is not None and 
                                           current_time - self.last_presence_time > self.relay_off_delay)

                # Turn off the relay (speaker power) after the delay
                if self.relay.is_connected() and self.relay.is_turned_on() and relay_timeout_is_complete:
                    logger.info(f"Turning off relay after {int(self.relay_off_delay/60)} minutes of no presence")
                    self.relay.turn_off()

        except Exception as e:
            logger.error(f"Error checking presence: {e}")


def main():
    """Main entry point for the Crescendo system."""
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Crescendo AI - Presence-activated music player")
    parser.add_argument('--sensor-port', default='/dev/ttyAMA0', help='Serial port for the presence sensor')
    parser.add_argument('--music-dir', default='music', help='Directory containing music files')
    parser.add_argument('--check-interval', type=float, default=1.0, help='Interval in seconds between presence checks')
    parser.add_argument('--relay-off-delay', type=float, default=15.0 * 60.0, 
                        help='Delay in seconds before turning off the relay after no presence is detected (default: 15 minutes)')

    args = parser.parse_args()

    # Create and run the system
    system = CrescendoSystem(
        sensor_port=args.sensor_port,
        music_dir=args.music_dir,
        check_interval=args.check_interval,
        relay_off_delay=args.relay_off_delay
    )

    system.run()


if __name__ == "__main__":
    main()
