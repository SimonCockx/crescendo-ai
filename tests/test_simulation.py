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
        self._current_playlist = None

    def initialize(self) -> bool:
        """Simulate initializing the audio player."""
        logger.info("Simulated audio player initialized")
        self._is_initialized = True

        # Try to load the music configuration if it exists
        if os.path.exists(self.config_path):
            from crescendo_ai.config import load_music_config
            self.music_config = load_music_config(self.config_path, self.music_dir)
            logger.info(f"Simulated audio player loaded music configuration from {self.config_path}")

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

    def play(self, track_path: Optional[str] = None, playlist_name: Optional[str] = None) -> bool:
        """Simulate playing a track or playlist."""
        if not self._is_initialized:
            logger.error("Cannot play: Simulated audio player not initialized")
            return False

        # If a playlist name is provided, play that playlist
        if playlist_name is not None:
            return self.play_playlist(playlist_name)

        # If we have a current playlist but no specific track, play the next track from the playlist
        if self._current_playlist is not None and track_path is None:
            next_track = self._current_playlist.get_next_track(self.music_dir)
            if next_track:
                track_path = next_track

        # If no track specified, use the current track or find a default
        if track_path is None:
            if self._current_track is not None:
                track_path = self._current_track
            else:
                # Try to get a track from the scheduled playlist if available
                if hasattr(self, 'music_config') and self.music_config:
                    current_playlist = self.music_config.get_current_playlist()
                    if current_playlist:
                        self._current_playlist = current_playlist
                        next_track = current_playlist.get_next_track(self.music_dir)
                        if next_track:
                            track_path = next_track

                # If still no track, use a default
                if track_path is None:
                    track_path = "simulated_track.mp3"

        self._is_playing = True
        self._current_track = track_path
        logger.info(f"Simulated audio player playing: {self._current_track}")
        return True

    def play_playlist(self, playlist_name: str) -> bool:
        """Simulate playing a playlist."""
        if not self._is_initialized:
            logger.error("Cannot play playlist: Simulated audio player not initialized")
            return False

        if not hasattr(self, 'music_config') or not self.music_config:
            logger.error("Cannot play playlist: No music configuration loaded")
            return False

        playlist = self.music_config.get_playlist(playlist_name)
        if not playlist:
            logger.error(f"Playlist not found: {playlist_name}")
            return False

        self._current_playlist = playlist
        logger.info(f"Simulated audio player playing playlist: {playlist_name}")

        # Play the first track in the playlist
        next_track = playlist.get_next_track(self.music_dir)
        if not next_track:
            logger.error(f"Playlist {playlist_name} is empty")
            return False

        return self.play(next_track)

    def play_next_track(self) -> bool:
        """Simulate playing the next track in the current playlist."""
        if not self._is_initialized:
            logger.error("Cannot play next track: Simulated audio player not initialized")
            return False

        if not self._current_playlist:
            # If no current playlist but we have a configuration, try to get the current scheduled playlist
            if hasattr(self, 'music_config') and self.music_config:
                self._current_playlist = self.music_config.get_current_playlist()

            # If still no playlist, we can't play the next track
            if not self._current_playlist:
                logger.error("Cannot play next track: No current playlist")
                return False

        next_track = self._current_playlist.get_next_track(self.music_dir)
        if not next_track:
            logger.error(f"Playlist {self._current_playlist.name} is empty")
            return False

        return self.play(next_track)

    def check_for_track_end(self) -> None:
        """Simulate checking for track end."""
        # In a real implementation, this would check for the end of the current track
        # and play the next track if needed. For the simulation, we'll just log it.
        if self._is_playing:
            logger.debug("Simulated audio player checking for track end")

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
        self.audio_player = SimulatedAudioPlayer(music_dir=self.music_dir, config_path=self.config_path)


def create_test_config(music_dir):
    """Create a test configuration file for the simulation."""
    import yaml

    # Create the music directory if it doesn't exist
    os.makedirs(music_dir, exist_ok=True)

    # Create a test configuration file
    config_path = os.path.join(music_dir, "music_config.yaml")

    # Define a simple configuration for testing
    config = {
        "playlists": {
            "test_playlist": {
                "tracks": [
                    "simulated_track1.mp3",
                    "simulated_track2.mp3",
                    "simulated_track3.mp3"
                ]
            },
            "default": {
                "tracks": [
                    "simulated_default_track.mp3"
                ]
            }
        },
        "schedules": [
            {
                "days": [0, 1, 2, 3, 4, 5, 6],  # All days
                "hours": list(range(24)),  # All hours
                "playlist": "test_playlist"
            }
        ]
    }

    # Write the configuration to the file
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    logger.info(f"Created test configuration file at {config_path}")
    return config_path

def run_simulation():
    """Run a simulation of the Crescendo system."""
    logger.info("Starting Crescendo AI simulation")

    # Create a test music directory
    music_dir = "simulated_music_dir"

    # Create a test configuration file
    config_path = create_test_config(music_dir)

    # Create a simulated system
    system = SimulatedCrescendoSystem(
        sensor_port="simulated_port",
        music_dir=music_dir,
        check_interval=1.0,
        config_path=config_path
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

        # Test playlist functionality
        logger.info("Testing playlist functionality...")

        # Test playing a specific playlist
        if system.audio_player.play_playlist("test_playlist"):
            logger.info("✓ Successfully played test_playlist")
        else:
            logger.error("✗ Failed to play test_playlist")

        # Verify the current track is from the playlist
        current_track = system.audio_player._current_track
        if "simulated_track" in current_track:
            logger.info(f"✓ Playing track from playlist: {current_track}")
        else:
            logger.error(f"✗ Not playing track from playlist: {current_track}")

        # Test playing the next track in the playlist
        if system.audio_player.play_next_track():
            logger.info("✓ Successfully played next track in playlist")
        else:
            logger.error("✗ Failed to play next track in playlist")

        # Verify the current track is the next track in the playlist
        new_current_track = system.audio_player._current_track
        if new_current_track != current_track:
            logger.info(f"✓ Advanced to next track: {new_current_track}")
        else:
            logger.error(f"✗ Failed to advance to next track: {new_current_track}")

        # Test the check_for_track_end method
        logger.info("Testing check_for_track_end method...")
        system.audio_player.check_for_track_end()

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
