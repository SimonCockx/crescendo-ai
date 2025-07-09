#!/usr/bin/env python3
"""
Test script for the music configuration.

This script tests the music configuration by simulating different dates and times
to verify that the correct playlist is selected for each date and time.
"""

import os
import sys
import logging
from datetime import datetime
from unittest.mock import patch

# Add the parent directory to the path so we can import the crescendo_ai package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crescendo_ai.config import load_music_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_music_config():
    """Test the music configuration with different dates and times."""
    logger.info("Testing music configuration...")
    
    # Load the music configuration
    config_path = os.path.join("music", "music_config.yaml")
    music_dir = "music"
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return False
    
    music_config = load_music_config(config_path, music_dir)
    
    # Test dates and times
    test_cases = [
        # Format: (date_str, hour, expected_playlist)
        ("2025-07-11", 3, "kamp_hiphop"),
        ("2025-07-12", 10, "kamp_jazz"),
        ("2025-07-13", 2, "kamp_jazz"),
        ("2025-07-13", 15, "kamp_klassiek"),
        ("2025-07-14", 4, "kamp_klassiek"),
        ("2025-07-14", 20, "kamp_margi"),
        ("2025-07-15", 1, "kamp_margi"),
        ("2025-07-15", 12, "kamp_rock_00s"),
        ("2025-07-16", 3, "kamp_rock_00s"),
        ("2025-07-16", 22, "kamp_rock_70_80s"),
        ("2025-07-17", 5, "kamp_rock_70_80s"),
        ("2025-07-17", 18, "kamp_rock_90s"),
        ("2025-07-18", 4, "kamp_rock_90s"),
        ("2025-07-18", 14, "kamp_rock_oldies"),
        ("2025-07-19", 3, "kamp_rock_oldies"),
        ("2025-07-19", 12, "kamp_reggae"),
        # Test a date outside the schedule
        ("2025-07-20", 12, "default"),
    ]
    
    for date_str, hour, expected_playlist in test_cases:
        # Create a datetime object for the test case
        test_datetime = datetime.strptime(f"{date_str} {hour:02d}:00:00", "%Y-%m-%d %H:%M:%S")
        
        # Mock the datetime.now() function to return our test datetime
        with patch('crescendo_ai.config.datetime') as mock_datetime:
            mock_datetime.now.return_value = test_datetime
            mock_datetime.strptime = datetime.strptime
            
            # Get the current playlist
            current_playlist = music_config.get_current_playlist()
            
            # Check if the playlist is correct
            if current_playlist and current_playlist.name == expected_playlist:
                logger.info(f"✓ {date_str} {hour:02d}:00 - Got expected playlist: {expected_playlist}")
            else:
                playlist_name = current_playlist.name if current_playlist else "None"
                logger.error(f"✗ {date_str} {hour:02d}:00 - Expected {expected_playlist}, got {playlist_name}")
    
    logger.info("Music configuration test completed")
    return True

if __name__ == "__main__":
    test_music_config()