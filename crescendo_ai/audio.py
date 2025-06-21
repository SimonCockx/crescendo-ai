"""
Module for audio playback functionality.

This module provides functionality to play background music
through the Raspberry Pi's audio output to a connected speaker.
"""

import pygame
import logging
import os
import time
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class AudioPlayer:
    """Class to handle audio playback."""
    
    def __init__(self, music_dir: str = "music"):
        """
        Initialize the audio player.
        
        Args:
            music_dir: Directory containing music files
        """
        self.music_dir = music_dir
        self._is_initialized = False
        self._current_track: Optional[str] = None
        self._is_playing = False
        
    def initialize(self) -> bool:
        """
        Initialize the pygame mixer for audio playback.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            pygame.mixer.init()
            self._is_initialized = True
            logger.info("Audio player initialized")
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
    
    def play(self, track_path: Optional[str] = None) -> bool:
        """
        Play a music track.
        
        Args:
            track_path: Path to the music file to play.
                        If None, plays a default track or the last played track.
        
        Returns:
            bool: True if playback started successfully, False otherwise
        """
        if not self._is_initialized:
            logger.error("Cannot play: Audio player not initialized")
            return False
        
        # If no track specified, use the current track or find a default
        if track_path is None:
            if self._current_track is not None:
                track_path = self._current_track
            else:
                # Find the first available track in the music directory
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
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            
            self._current_track = track_path
            self._is_playing = True
            logger.info(f"Playing track: {os.path.basename(track_path)}")
            return True
        except pygame.error as e:
            logger.error(f"Error playing track: {e}")
            return False
    
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