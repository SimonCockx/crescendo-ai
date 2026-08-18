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
import logging.handlers
import time
import os

from crescendo_ai.sensor import PresenceSensor
from crescendo_ai.relay import USBRelay
from crescendo_ai.audio import AudioPlayer
from crescendo_ai.systemd_notify import notify

logger = logging.getLogger(__name__)


def configure_logging(level: str = 'INFO', log_file: str = 'crescendo.log') -> None:
    """
    Configure application-wide logging.

    Uses a rotating file handler so a long unattended run can't fill up the
    disk (capped at ~50MB across 5 rotated files) instead of the previous
    unbounded log file.

    Args:
        level: Logging level name (e.g. 'DEBUG', 'INFO', 'WARNING')
        log_file: Path to the log file
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=5
            ),
        ]
    )

class CrescendoSystem:
    """Main class that coordinates all components of the Crescendo AI system."""

    def __init__(
        self,
        sensor_port: str = '/dev/ttyAMA0',
        music_dir: str = 'music',
        check_interval: float = 1.0,
        relay_off_delay: float = 15.0 * 60.0,
        config_path: str = None,
    ):
        """
        Initialize the Crescendo system.

        Args:
            sensor_port: Serial port for the presence sensor
            music_dir: Directory containing music files
            check_interval: Interval in seconds between presence checks
            relay_off_delay: Delay in seconds before turning off the relay after no presence is detected
            config_path: Path to the music configuration file. If None, will look for music_config.yaml in music_dir.
        """
        self.sensor_port = sensor_port
        self.music_dir = music_dir
        self.check_interval = check_interval
        self.relay_off_delay = relay_off_delay
        self.config_path = config_path if config_path else os.path.join(music_dir, "music_config.yaml")

        # Initialize components
        self.sensor = PresenceSensor(port=sensor_port)
        self.relay = USBRelay()
        self.audio_player = AudioPlayer(music_dir=music_dir, config_path=self.config_path)

        # State variables
        self.running = False
        self.last_presence_time = None

        # Dynamic detection state variables
        self.dynamic_detection_history = []  # List of timestamps when dynamic motion was detected
        self.dynamic_detection_active_until = None  # Timestamp until dynamic detection is considered active
        self.dynamic_detection_duration = 300  # Duration in seconds (5 minutes) to keep dynamic detection active
        self.dynamic_detection_window = 2.0  # Seconds of history to consider for continuous motion
        self.dynamic_detection_count_threshold = 2  # Minimum detections within the window to count as continuous

        # Static detection is held active for this many seconds after the sensor
        # last reported it, so brief sensor dropouts don't reset dynamic detection
        self.static_detection_hold_time = 25
        self.last_static_detection_time = None

        # State tracking for logging
        self.prev_dynamic_detection_active = False
        self.prev_static_detected = False
        self.prev_continuous_detection = False
        self.prev_presence_detected = False

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
                motion_sensitivity=[70, 70, 65, 65, 65, 60, 60, 60],  # Per gate
                static_sensitivity=[70, 70, 60, 55, 50, 45, 45, 45]  # Per gate (0,1 not settable)
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

        notify('READY=1')

        try:
            while self.running:
                self._check_presence_and_update()
                # Pet the systemd watchdog (no-op unless WatchdogSec is
                # configured in the unit file), so a truly hung process
                # gets restarted instead of sitting silently for days.
                notify('WATCHDOG=1')
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            notify('STOPPING=1')
            self.shutdown()

    def _check_presence_and_update(self) -> None:
        """Check for presence and update system state accordingly using the robust detection algorithm."""
        try:
            current_time = time.time()

            # Retry a dropped relay connection (rate-limited internally)
            # instead of leaving speaker control dead for the rest of the run
            self.relay.ensure_connected()

            # Check for dynamic (moving) target
            dynamic_detected = self.sensor.is_moving_target_detected()

            # Update dynamic detection history
            if dynamic_detected:
                self.dynamic_detection_history.append(current_time)

            # Remove entries older than the detection window from history
            self.dynamic_detection_history = [t for t in self.dynamic_detection_history
                                             if current_time - t <= self.dynamic_detection_window]

            # Check if we have enough dynamic detections within the window
            dynamic_detection_active = False
            continuous_detection = len(self.dynamic_detection_history) >= self.dynamic_detection_count_threshold

            if continuous_detection:
                # If we have enough detections within the window, activate dynamic detection
                dynamic_detection_active = True
                # Set the dynamic detection to be active for the next 5 minutes
                self.dynamic_detection_active_until = current_time + self.dynamic_detection_duration
                # Log only if this is a new continuous detection
                if not self.prev_continuous_detection:
                    logger.debug(f"Dynamic detection activated: {self.dynamic_detection_count_threshold}+ detections within {self.dynamic_detection_window}s (active until {time.ctime(self.dynamic_detection_active_until)})")
                    self.prev_continuous_detection = True
            elif self.dynamic_detection_active_until and current_time < self.dynamic_detection_active_until:
                # Dynamic detection is still active from a previous detection
                dynamic_detection_active = True
                # No need to log this every second - it's redundant information
            else:
                # Log only if dynamic detection was previously active
                if self.prev_dynamic_detection_active:
                    logger.debug(f"Dynamic detection inactive: no continuous motion detected and not within 5-minute window")
                self.prev_continuous_detection = False

            # Check for static target
            static_detected_direct = self.sensor.is_static_target_detected()
            if static_detected_direct:
                self.last_static_detection_time = current_time

            # Static detection is held active for static_detection_hold_time seconds after
            # the sensor last reported it, so brief sensor dropouts don't reset dynamic
            # detection. Note this hold time stacks with the sensor's own no_one_duration
            # debounce, so presence can persist for up to their sum after someone leaves.
            static_detected = self.last_static_detection_time is not None and (current_time - self.last_static_detection_time <= self.static_detection_hold_time)

            # Update previous dynamic detection state
            if dynamic_detection_active != self.prev_dynamic_detection_active:
                self.prev_dynamic_detection_active = dynamic_detection_active

            # Log static detection status only if it changed
            if static_detected != self.prev_static_detected:
                if static_detected:
                    source = "live" if static_detected_direct else "held from grace period"
                    logger.debug(f"Static target detected ({source}): energy level {self.sensor.get_static_energy()}")
                else:
                    logger.debug(f"No static target detected")
                self.prev_static_detected = static_detected

            # Robust presence detection: both dynamic detection must be active AND static target must be detected
            robust_presence_detected = dynamic_detection_active and static_detected

            # Track previous state to detect changes
            was_presence_detected = self.last_presence_time is not None and (current_time - self.last_presence_time) < self.relay_off_delay

            if robust_presence_detected:
                self.last_presence_time = current_time

                # Log detailed presence detection information
                if not self.prev_presence_detected:
                    logger.info("PRESENCE DETECTED: Both conditions met for robust detection")
                    logger.info(f"  - Dynamic detection: {f'{self.dynamic_detection_count_threshold}+ detections within {self.dynamic_detection_window}s' if continuous_detection else 'Within 5-minute window'}")
                    logger.info(f"  - Static detection: Energy level {self.sensor.get_static_energy()}")

                # If music is not playing, turn on relay and start music
                if self.relay.is_connected() and not self.relay.is_turned_on():
                    logger.info("Robust presence detected - turning on relay")
                    # Turn on the relay (speaker power)
                    self.relay.turn_on()

                if not self.audio_player.is_playing():
                    logger.info("Robust presence detected - starting music")
                    # Start playing music using the configured playlist system
                    self.audio_player.play()
                else:
                    # Check if the current track has ended and play the next track if needed
                    self.audio_player.check_for_track_end()

                # Update previous presence state
                self.prev_presence_detected = True
            else:
                # Log detailed information about why presence was not detected
                if was_presence_detected and self.prev_presence_detected:
                    logger.info("PRESENCE LOST: Robust detection conditions no longer met")
                    if not dynamic_detection_active:
                        logger.info("  - Dynamic detection inactive: No continuous motion and outside 5-minute window")
                    if not static_detected:
                        logger.info("  - Static detection inactive: No stationary target detected")

                # Always update previous presence state when robust presence is not detected
                self.prev_presence_detected = False

                # Regular debug logging - only log if state changed
                if dynamic_detection_active != self.prev_dynamic_detection_active or static_detected != self.prev_static_detected:
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

            # Reset dynamic detection if no static target is detected (including the hold period).
            # This is placed at the end (rather than right after computing static_detected) to
            # match the original logic: dynamic_detection_active/prev_dynamic_detection_active
            # above already reflect this cycle's real sensor state, so PRESENCE LOST logging
            # attributes the loss correctly; only the internal history/timer used by *future*
            # cycles is cleared here.
            if not static_detected:
                # Only log if this is a change from the previous state
                if self.dynamic_detection_active_until is not None:
                    logger.debug("Resetting dynamic detection because no static target is detected")
                self.dynamic_detection_history = []
                self.dynamic_detection_active_until = None

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
    parser.add_argument('--config-path', default=None,
                        help='Path to the music configuration file. If not provided, will look for music_config.yaml in the music directory')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO). Use DEBUG for troubleshooting only - '
                             'it generates a lot of output over a long run.')

    args = parser.parse_args()

    configure_logging(level=args.log_level)

    # Create and run the system
    system = CrescendoSystem(
        sensor_port=args.sensor_port,
        music_dir=args.music_dir,
        check_interval=args.check_interval,
        relay_off_delay=args.relay_off_delay,
        config_path=args.config_path
    )

    system.run()


if __name__ == "__main__":
    main()
