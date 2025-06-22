#!/usr/bin/env python3
"""
Simulation test script for the Crescendo AI system.

This script simulates the behavior of the system without requiring
the actual hardware components. It's useful for testing the logic
and flow of the application.
"""

import os
import sys
import time
import logging
import threading
from typing import Optional

# Add the parent directory to the path so we can import the crescendo_ai package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crescendo_ai.sensor import PresenceSensor
from crescendo_ai.relay import USBRelay
from crescendo_ai.audio import AudioPlayer
from crescendo_ai.main import CrescendoSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SimulatedPresenceSensor(PresenceSensor):
    """A simulated version of the presence sensor for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._presence_detected = False
        self._is_connected = True

    def connect(self) -> bool:
        """Simulate connecting to the sensor."""
        logger.info("Simulated sensor connected")
        self._is_connected = True
        return True

    def disconnect(self) -> None:
        """Simulate disconnecting from the sensor."""
        logger.info("Simulated sensor disconnected")
        self._is_connected = False

    def is_connected(self) -> bool:
        """Check if the simulated sensor is connected."""
        return self._is_connected

    def read_data(self) -> dict:
        """Simulate reading data from the sensor."""
        return {"presence": 1 if self._presence_detected else 0}

    def is_presence_detected(self) -> bool:
        """Check if presence is detected in the simulation."""
        return self._presence_detected

    def set_presence(self, detected: bool) -> None:
        """
        Set the simulated presence state.

        Args:
            detected: True to simulate presence, False for no presence
        """
        self._presence_detected = detected
        state = "DETECTED" if detected else "NOT DETECTED"
        logger.info(f"Simulated presence: {state}")


class SimulatedUSBRelay(USBRelay):
    """A simulated version of the USB relay for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_connected = True
        self._relay_state = False

    def connect(self) -> bool:
        """Simulate connecting to the relay."""
        logger.info("Simulated relay connected")
        self._is_connected = True
        return True

    def disconnect(self) -> None:
        """Simulate disconnecting from the relay."""
        logger.info("Simulated relay disconnected")
        self._is_connected = False

    def is_connected(self) -> bool:
        """Check if the simulated relay is connected."""
        return self._is_connected

    def turn_on(self, channel: int = 1) -> bool:
        """Simulate turning on the relay."""
        self._relay_state = True
        logger.info(f"Simulated relay channel {channel} turned ON")
        return True

    def turn_off(self, channel: int = 1) -> bool:
        """Simulate turning off the relay."""
        self._relay_state = False
        logger.info(f"Simulated relay channel {channel} turned OFF")
        return True

    def get_state(self) -> bool:
        """Get the current state of the simulated relay."""
        return self._relay_state


class SimulatedAudioPlayer(AudioPlayer):
    """A simulated version of the audio player for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_initialized = True
        self._is_playing = False
        self._current_track = "simulated_track.mp3"

    def initialize(self) -> bool:
        """Simulate initializing the audio player."""
        logger.info("Simulated audio player initialized")
        self._is_initialized = True
        return True

    def shutdown(self) -> None:
        """Simulate shutting down the audio player."""
        if self._is_playing:
            self.stop()
        logger.info("Simulated audio player shut down")
        self._is_initialized = False

    def is_initialized(self) -> bool:
        """Check if the simulated audio player is initialized."""
        return self._is_initialized

    def is_playing(self) -> bool:
        """Check if the simulated audio player is playing."""
        return self._is_playing

    def play(self, track_path: Optional[str] = None) -> bool:
        """Simulate playing a track."""
        if not self._is_initialized:
            logger.error("Cannot play: Simulated audio player not initialized")
            return False

        self._is_playing = True
        self._current_track = track_path or "simulated_track.mp3"
        logger.info(f"Simulated audio player playing: {self._current_track}")
        return True

    def stop(self) -> bool:
        """Simulate stopping playback."""
        if not self._is_initialized:
            logger.error("Cannot stop: Simulated audio player not initialized")
            return False

        if self._is_playing:
            self._is_playing = False
            logger.info("Simulated audio player stopped")
        return True

    def set_volume(self, volume: float) -> bool:
        """Simulate setting the volume."""
        if not self._is_initialized:
            logger.error("Cannot set volume: Simulated audio player not initialized")
            return False

        logger.info(f"Simulated audio player volume set to {volume:.2f}")
        return True


class SimulatedCrescendoSystem(CrescendoSystem):
    """A simulated version of the Crescendo system for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace the real components with simulated ones
        self.sensor = SimulatedPresenceSensor(port=self.sensor_port)
        self.relay = SimulatedUSBRelay()
        self.audio_player = SimulatedAudioPlayer(music_dir=self.music_dir)


def run_simulation():
    """Run a simulation of the Crescendo system."""
    logger.info("Starting Crescendo AI simulation")

    # Create a simulated system
    system = SimulatedCrescendoSystem(
        sensor_port="simulated_port",
        music_dir="simulated_music_dir",
        check_interval=1.0
    )

    # Start the system in a separate thread
    system_thread = threading.Thread(target=system.run)
    system_thread.daemon = True
    system_thread.start()

    try:
        # Wait for the system to initialize
        time.sleep(2)

        # Simulate presence detection
        logger.info("Simulating presence detection...")
        system.sensor.set_presence(True)

        # Wait to see the system respond
        time.sleep(3)

        # Verify that music is playing
        if system.audio_player.is_playing():
            logger.info("✓ System correctly started playing music when presence detected")
        else:
            logger.error("✗ System failed to start playing music when presence detected")

        # Simulate person leaving
        logger.info("Simulating person leaving...")
        system.sensor.set_presence(False)

        # Wait a short time for the system to respond
        logger.info("Waiting for system to respond to no presence...")
        time.sleep(3)

        # Verify that music stopped
        if not system.audio_player.is_playing():
            logger.info("✓ System correctly stopped playing music when no presence detected")
        else:
            logger.error("✗ System failed to stop playing music when no presence detected")

        # Simulate presence again
        logger.info("Simulating presence detection again...")
        system.sensor.set_presence(True)

        # Wait to see the system respond
        time.sleep(3)

        # Verify that music is playing again
        if system.audio_player.is_playing():
            logger.info("✓ System correctly restarted playing music when presence detected")
        else:
            logger.error("✗ System failed to restart playing music when presence detected")

        # End the simulation
        logger.info("Simulation completed successfully")

    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Error during simulation: {e}", exc_info=True)
    finally:
        # Stop the system
        system.running = False
        system_thread.join(timeout=2)
        logger.info("Simulation ended")


if __name__ == "__main__":
    # Create the tests directory if it doesn't exist
    os.makedirs("tests", exist_ok=True)

    # Run the simulation
    run_simulation()
