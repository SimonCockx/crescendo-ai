"""
Module for configuration management.

This module provides functionality to load and parse the YAML configuration file
for playlists and schedules.
"""

import os
import logging
import yaml
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, time

logger = logging.getLogger(__name__)

class Playlist:
    """Class representing a playlist."""

    def __init__(self, name: str, tracks: List[str] = None, directory: str = None):
        """
        Initialize a playlist.

        Args:
            name: Name of the playlist
            tracks: List of track paths
            directory: Directory containing tracks
        """
        self.name = name
        self.tracks = tracks or []
        self.directory = directory
        self.current_track_index = 0

    def get_tracks(self, base_dir: str = "") -> List[str]:
        """
        Get all tracks in the playlist.

        Args:
            base_dir: Base directory for relative paths

        Returns:
            List of track paths
        """
        if self.tracks:
            # Return the explicitly defined tracks
            return [os.path.join(base_dir, track) if not os.path.isabs(track) else track 
                   for track in self.tracks]
        elif self.directory:
            # Get all audio files in the directory in alphabetical order
            directory_path = os.path.join(base_dir, self.directory) if not os.path.isabs(self.directory) else self.directory
            if not os.path.exists(directory_path):
                logger.warning(f"Playlist directory not found: {directory_path}")
                return []

            # Look for common audio file formats
            audio_extensions = ['.mp3', '.wav', '.ogg', '.flac']
            tracks = []

            for file in sorted(os.listdir(directory_path)):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    if ext.lower() in audio_extensions:
                        tracks.append(file_path)

            return tracks
        else:
            return []

    def get_next_track(self, base_dir: str = "") -> Optional[str]:
        """
        Get the next track in the playlist.

        Args:
            base_dir: Base directory for relative paths

        Returns:
            Path to the next track, or None if the playlist is empty
        """
        tracks = self.get_tracks(base_dir)
        if not tracks:
            return None

        # Get the current track
        track = tracks[self.current_track_index]

        # Increment the index for next time, looping back to 0 if we reach the end
        self.current_track_index = (self.current_track_index + 1) % len(tracks)

        return track

    def reset(self) -> None:
        """Reset the playlist to the beginning."""
        self.current_track_index = 0


class MusicConfig:
    """Class for managing music configuration."""

    def __init__(self, config_path: str, music_dir: str = "music"):
        """
        Initialize the music configuration.

        Args:
            config_path: Path to the YAML configuration file
            music_dir: Base directory for music files
        """
        self.config_path = config_path
        self.music_dir = music_dir
        self.playlists: Dict[str, Playlist] = {}
        self.schedules: List[Dict[str, Any]] = []
        self.default_playlist: Optional[Playlist] = None

    def load(self) -> bool:
        """
        Load the configuration from the YAML file.

        Returns:
            bool: True if loading was successful, False otherwise
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Parse playlists
            if 'playlists' in config:
                for name, playlist_config in config['playlists'].items():
                    tracks = playlist_config.get('tracks', [])
                    directory = playlist_config.get('directory')
                    playlist = Playlist(name, tracks, directory)
                    self.playlists[name] = playlist

                    # Set default playlist
                    if name == 'default':
                        self.default_playlist = playlist

            # Parse schedules
            if 'schedules' in config:
                self.schedules = config['schedules']

            logger.info(f"Loaded configuration from {self.config_path}")
            logger.info(f"Found {len(self.playlists)} playlists and {len(self.schedules)} schedules")
            return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False

    def get_playlist(self, name: str) -> Optional[Playlist]:
        """
        Get a playlist by name.

        Args:
            name: Name of the playlist

        Returns:
            Playlist object, or None if not found
        """
        return self.playlists.get(name)

    def get_current_playlist(self) -> Optional[Playlist]:
        """
        Get the playlist that should be active based on the current time.

        Returns:
            Playlist object, or None if no playlist is scheduled
        """
        now = datetime.now()
        current_day = now.weekday()  # 0 = Monday, 6 = Sunday
        current_hour = now.hour
        current_date = now.strftime("%Y-%m-%d")

        # Check each schedule
        for schedule in self.schedules:
            # Check date-specific schedule
            if 'date' in schedule and schedule['date'] == current_date:
                if 'hours' in schedule and current_hour in schedule['hours']:
                    playlist_name = schedule.get('playlist')
                    if playlist_name and playlist_name in self.playlists:
                        logger.debug(f"Using date-specific playlist: {playlist_name}")
                        return self.playlists[playlist_name]

            # Check day-of-week schedule
            if 'days' in schedule and current_day in schedule['days']:
                if 'hours' in schedule and current_hour in schedule['hours']:
                    playlist_name = schedule.get('playlist')
                    if playlist_name and playlist_name in self.playlists:
                        logger.debug(f"Using day-of-week playlist: {playlist_name}")
                        return self.playlists[playlist_name]

        # If no schedule matches, return the default playlist
        if self.default_playlist:
            logger.debug("Using default playlist")
            return self.default_playlist

        # If no default playlist is defined, return None
        return None


def load_music_config(config_path: str, music_dir: str = "music") -> MusicConfig:
    """
    Load the music configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file
        music_dir: Base directory for music files

    Returns:
        MusicConfig object
    """
    config = MusicConfig(config_path, music_dir)
    config.load()
    return config