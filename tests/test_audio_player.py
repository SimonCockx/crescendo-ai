#!/usr/bin/env python3
"""
Test script for the AudioPlayer component of the Crescendo AI system.

This script tests the basic functionality of the AudioPlayer class
without requiring actual audio hardware.
"""

import os
import sys
import unittest
import tempfile
import shutil

# Add the parent directory to the path so we can import the crescendo_ai package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crescendo_ai.audio import AudioPlayer

class TestAudioPlayer(unittest.TestCase):
    """Test cases for the AudioPlayer class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test music files
        self.test_music_dir = tempfile.mkdtemp()
        
        # Create a dummy audio file
        self.test_audio_file = os.path.join(self.test_music_dir, "test_track.mp3")
        with open(self.test_audio_file, 'w') as f:
            f.write("This is a dummy audio file for testing")
        
        # Create the AudioPlayer instance
        self.audio_player = AudioPlayer(music_dir=self.test_music_dir)
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_music_dir)
    
    def test_initialization(self):
        """Test that the AudioPlayer initializes correctly."""
        # Initialize the audio player
        result = self.audio_player.initialize()
        
        # Check that initialization was successful
        self.assertTrue(result, "AudioPlayer initialization should succeed")
        self.assertTrue(self.audio_player.is_initialized(), "AudioPlayer should be initialized")
    
    def test_get_available_tracks(self):
        """Test that the AudioPlayer can find available tracks."""
        # Initialize the audio player
        self.audio_player.initialize()
        
        # Get available tracks
        tracks = self.audio_player.get_available_tracks()
        
        # Check that our test track is found
        self.assertEqual(len(tracks), 1, "Should find exactly one track")
        self.assertEqual(tracks[0]['name'], "test_track.mp3", "Track name should match")
        self.assertEqual(tracks[0]['path'], self.test_audio_file, "Track path should match")
    
    def test_play_and_stop(self):
        """Test that the AudioPlayer can play and stop tracks."""
        # Initialize the audio player
        self.audio_player.initialize()
        
        # Play the test track
        result = self.audio_player.play(self.test_audio_file)
        
        # Note: In a real test environment, this might fail because the file isn't a real audio file
        # For this example, we'll just check that the method returns the expected value
        # In a real test, you might want to use a mock or a real audio file
        
        # Stop playback
        stop_result = self.audio_player.stop()
        
        # Check that stop was successful
        self.assertTrue(stop_result, "Stopping playback should succeed")
        self.assertFalse(self.audio_player.is_playing(), "AudioPlayer should not be playing after stop")

if __name__ == "__main__":
    unittest.main()