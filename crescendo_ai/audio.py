"""
Module for audio playback functionality.

This module provides functionality to play background music
through the Raspberry Pi's audio output to a connected speaker.
It supports playlists and scheduling based on a YAML configuration file.
"""

import os
import logging
import time
from typing import Optional, List, Dict

# Set environment variable for pygame NEON support on ARM processors
if 'arm' in os.uname().machine:
    os.environ['PYGAME_DETECT_AVX2'] = '1'

import pygame
from crescendo_ai.config import MusicConfig, Playlist, load_music_config

logger = logging.getLogger(__name__)

class AudioPlayer:
    """Class to handle audio playback with playlist and scheduling support."""

    def __init__(self, music_dir: str = "music", config_path: Optional[str] = None):
        """
        Initialize the audio player.

        Args:
            music_dir: Directory containing music files
            config_path: Path to the YAML configuration file. If None, will look for music_config.yaml in music_dir.
        """
        self.music_dir = music_dir
        self._is_initialized = False
        self._current_track: Optional[str] = None
        self._is_playing = False
        self._current_playlist: Optional[Playlist] = None

        # Set default config path if not provided
        if config_path is None:
            self.config_path = os.path.join(music_dir, "music_config.yaml")
        else:
            self.config_path = config_path

        self.music_config: Optional[MusicConfig] = None

    def initialize(self) -> bool:
        """
        Initialize the pygame mixer for audio playback and load the music configuration.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize pygame with a dummy video system to support event handling
            pygame.init()
            # Initialize the mixer specifically for audio
            pygame.mixer.init()
            self._is_initialized = True
            logger.info("Audio player initialized")

            # Load music configuration if the file exists
            if os.path.exists(self.config_path):
                self.music_config = load_music_config(self.config_path, self.music_dir)
                logger.info(f"Loaded music configuration from {self.config_path}")
            else:
                logger.info(f"No music configuration file found at {self.config_path}, using default behavior")

            return True
        except pygame.error as e:
            logger.error(f"Failed to initialize audio player: {e}")
            self._is_initialized = False
            return False

    def shutdown(self) -> None:
        """Shutdown the audio player."""
        if self._is_initialized:
            if self._is_playing:
                self.stop()
            pygame.mixer.quit()
            pygame.quit()  # Quit pygame completely
            self._is_initialized = False
            logger.info("Audio player shut down")

    def is_initialized(self) -> bool:
        """
        Check if the audio player is initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        return self._is_initialized

    def is_playing(self) -> bool:
        """
        Check if music is currently playing.

        Returns:
            bool: True if playing, False otherwise
        """
        if not self._is_initialized:
            return False
        return pygame.mixer.music.get_busy()

    def play(self, track_path: Optional[str] = None, playlist_name: Optional[str] = None) -> bool:
        """
        Play a music track or playlist.

        Args:
            track_path: Path to the music file to play.
                        If None, plays a default track, the last played track, or a track from the playlist.
            playlist_name: Name of the playlist to play.
                          If provided, will play the first track from this playlist.

        Returns:
            bool: True if playback started successfully, False otherwise
        """
        if not self._is_initialized:
            logger.error("Cannot play: Audio player not initialized")
            return False

        # If a playlist name is provided, set it as the current playlist and play the first track
        if playlist_name is not None:
            return self.play_playlist(playlist_name)

        # If we have a current playlist but no specific track, play the next track from the playlist
        if self._current_playlist is not None and track_path is None:
            next_track = self._current_playlist.get_next_track(self.music_dir)
            if next_track:
                track_path = next_track
            else:
                logger.warning(f"Playlist {self._current_playlist.name} is empty, looking for default track")

        # If no track specified, use the current track or find a default
        if track_path is None:
            if self._current_track is not None:
                track_path = self._current_track
            else:
                # Try to get a track from the scheduled playlist if available
                if self.music_config:
                    current_playlist = self.music_config.get_current_playlist()
                    if current_playlist:
                        self._current_playlist = current_playlist
                        next_track = current_playlist.get_next_track(self.music_dir)
                        if next_track:
                            track_path = next_track

                # If still no track, find a default
                if track_path is None:
                    track_path = self._find_default_track()
                    if track_path is None:
                        logger.error("No music tracks found in directory")
                        return False

        # Ensure the track exists
        if not os.path.exists(track_path):
            logger.error(f"Track not found: {track_path}")
            return False

        try:
            # Stop any currently playing music
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

            # Load and play the new track
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()  # Play once, not looping

            self._current_track = track_path
            self._is_playing = True
            logger.info(f"Playing track: {os.path.basename(track_path)}")

            # Set up an event to detect when the song ends
            pygame.mixer.music.set_endevent(pygame.USEREVENT)

            return True
        except pygame.error as e:
            logger.error(f"Error playing track: {e}")
            return False

    def play_playlist(self, playlist_name: str) -> bool:
        """
        Play a playlist by name.

        Args:
            playlist_name: Name of the playlist to play

        Returns:
            bool: True if playback started successfully, False otherwise
        """
        if not self._is_initialized:
            logger.error("Cannot play playlist: Audio player not initialized")
            return False

        if not self.music_config:
            logger.error("Cannot play playlist: No music configuration loaded")
            return False

        playlist = self.music_config.get_playlist(playlist_name)
        if not playlist:
            logger.error(f"Playlist not found: {playlist_name}")
            return False

        self._current_playlist = playlist
        logger.info(f"Playing playlist: {playlist_name}")

        # Play the first track in the playlist
        next_track = playlist.get_next_track(self.music_dir)
        if not next_track:
            logger.error(f"Playlist {playlist_name} is empty")
            return False

        return self.play(next_track)

    def play_next_track(self) -> bool:
        """
        Play the next track in the current playlist.

        Returns:
            bool: True if playback started successfully, False otherwise
        """
        if not self._is_initialized:
            logger.error("Cannot play next track: Audio player not initialized")
            return False

        if not self._current_playlist:
            # If no current playlist but we have a configuration, try to get the current scheduled playlist
            if self.music_config:
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
        """
        Check if the current track has ended and play the next track if needed.
        This should be called regularly from the main loop.
        """
        if not self._is_initialized or not self._is_playing:
            return

        try:
            # Check for the end-of-track event
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    logger.debug("Track ended, playing next track")
                    self.play_next_track()
        except Exception as e:
            logger.error(f"Error checking for track end: {e}")
            # If we get a "video system not initialized" error, try to reinitialize pygame
            if "video system not initialized" in str(e):
                logger.warning("Attempting to reinitialize pygame...")
                try:
                    pygame.init()
                    logger.info("Successfully reinitialized pygame")
                except Exception as reinit_error:
                    logger.error(f"Failed to reinitialize pygame: {reinit_error}")

    def stop(self) -> bool:
        """
        Stop music playback.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self._is_initialized:
            logger.error("Cannot stop: Audio player not initialized")
            return False

        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self._is_playing = False
                logger.info("Stopped music playback")
            return True
        except pygame.error as e:
            logger.error(f"Error stopping playback: {e}")
            return False

    def set_volume(self, volume: float) -> bool:
        """
        Set the playback volume.

        Args:
            volume: Volume level (0.0 to 1.0)

        Returns:
            bool: True if volume set successfully, False otherwise
        """
        if not self._is_initialized:
            logger.error("Cannot set volume: Audio player not initialized")
            return False

        try:
            # Ensure volume is within valid range
            volume = max(0.0, min(1.0, volume))
            pygame.mixer.music.set_volume(volume)
            logger.info(f"Set volume to {volume:.2f}")
            return True
        except pygame.error as e:
            logger.error(f"Error setting volume: {e}")
            return False

    def _find_default_track(self) -> Optional[str]:
        """
        Find a default music track in the music directory.

        Returns:
            Optional[str]: Path to a music file, or None if none found
        """
        if not os.path.exists(self.music_dir):
            logger.warning(f"Music directory not found: {self.music_dir}")
            return None

        # Look for common audio file formats
        audio_extensions = ['.mp3', '.wav', '.ogg', '.flac']

        for file in os.listdir(self.music_dir):
            file_path = os.path.join(self.music_dir, file)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file)
                if ext.lower() in audio_extensions:
                    return file_path

        return None

    def get_available_tracks(self) -> List[Dict[str, str]]:
        """
        Get a list of available music tracks.

        Returns:
            List[Dict[str, str]]: List of tracks with name and path
        """
        tracks = []

        if not os.path.exists(self.music_dir):
            logger.warning(f"Music directory not found: {self.music_dir}")
            return tracks

        # Look for common audio file formats
        audio_extensions = ['.mp3', '.wav', '.ogg', '.flac']

        for file in os.listdir(self.music_dir):
            file_path = os.path.join(self.music_dir, file)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file)
                if ext.lower() in audio_extensions:
                    tracks.append({
                        'name': file,
                        'path': file_path
                    })

        return tracks
