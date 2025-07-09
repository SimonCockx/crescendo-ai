# Crescendo AI

A Raspberry Pi-based system that plays background music when someone is present in a room.

> **Note:** For quick setup instructions, see [GETTING_STARTED.md](GETTING_STARTED.md)

## Overview

Crescendo AI is a smart music player system that uses a 24GHz mmWave Human Static Presence Sensor to detect human presence in a room. When someone is detected, the system turns on a speaker via a USB relay and plays background music. When no one is detected for a specified period, the music stops and the speaker is turned off to save power.

### Detection Algorithm

Crescendo AI uses a robust detection algorithm that combines both static and dynamic presence sensing:

1. **High Sensitivity**: The sensor is configured with high sensitivity (above 70) for all detection gates, ensuring reliable detection up to 6 meters.

2. **Dynamic Detection**: 
   - The system tracks dynamic (moving) target detections over time
   - A person is considered dynamically detected if motion is detected continuously for at least 3 seconds
   - Once detected, dynamic detection remains active for 5 minutes, even if motion temporarily stops

3. **Static Detection**:
   - The system also monitors for stationary targets using the static detection capability
   - This helps detect people who are not moving but still present in the room

4. **Robust Presence Detection**:
   - A person is only considered "present" when BOTH conditions are true:
     1. Dynamic detection is active (either from continuous detection or within the 5-minute window)
     2. AND a static target is currently detected
   - This dual-condition approach prevents false positives and ensures the system only plays music when someone is actually in the room

This algorithm makes the system more robust against false detections and ensures music only plays when someone is actually present in the room.

### Components

- **Raspberry Pi 3**: The main controller for the system
- **24GHz mmWave Human Static Presence Sensor**: Connected via serial interface (e.g., Seeed Studio XIAO)
- **USB Relay**: To control power to the speaker
- **Speaker**: For audio output
- **Audio Files**: Your music collection

## Installation

### Prerequisites

- Raspberry Pi 3 with Raspberry Pi OS installed
- Python 3.9 or higher
- Poetry (for dependency management) or pip (alternative for Raspberry Pi)

### Hardware Setup

1. **Presence Sensor**:
   - Connect the 24GHz mmWave sensor to a USB port on the Raspberry Pi using a USB-to-Serial adapter
   - Note the device path (usually `/dev/ttyAMA0` or similar)

2. **USB Relay**:
   - Connect the USB relay to another USB port on the Raspberry Pi
   - Connect the speaker's power input to the relay's output
   - Set up USB permissions by creating a udev rule:
     ```bash
     sudo nano /etc/udev/rules.d/99-usb-relay.rules
     ```
   - Add the following line to the file:
     ```
     SUBSYSTEM=="hidraw", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="05df", MODE="0666"
     ```
   - Apply the new rule:
     ```bash
     sudo udevadm control --reload-rules
     sudo udevadm trigger
     ```

3. **Speaker**:
   - Connect the speaker's audio input to the Raspberry Pi's audio output (3.5mm jack or HDMI)
   - Connect the speaker's power input to the USB relay

### Software Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/crescendo-ai.git
   cd crescendo-ai
   ```

2. Install dependencies using either Poetry or pip:

   **Option 1: Using Poetry (recommended for development)**
   ```bash
   poetry install
   ```

   **Option 2: Using pip (faster setup on Raspberry Pi)**
   ```bash
   pip install -r requirements.txt
   ```

3. Create a directory for your music files:
   ```bash
   mkdir music
   ```

4. Add some music files to the `music` directory (MP3, WAV, OGG, or FLAC formats).

## Usage

### Basic Usage

**If you installed with Poetry:**

1. Activate the Poetry environment:
   ```bash
   poetry shell
   ```

2. Run the system:
   ```bash
   python crescendo.py
   ```

**If you installed with pip:**

1. Run the system directly:
   ```bash
   python crescendo.py
   ```

### Command-line Options

The system supports several command-line options:

- `--sensor-port`: Serial port for the presence sensor (default: `/dev/ttyAMA0`)
- `--music-dir`: Directory containing music files (default: `music`)
- `--check-interval`: Interval in seconds between presence checks (default: `1.0`)
- `--relay-off-delay`: Delay in seconds before turning off the relay after no presence is detected (default: `900.0`, which is 15 minutes)
- `--config-path`: Path to the music configuration file (default: `music/music_config.yaml`)

Example:
```bash
python crescendo.py --sensor-port /dev/ttyAMA0 --music-dir ~/Music --relay-off-delay 1800 --config-path ~/Music/my_config.yaml
```

### Playlists and Scheduling

Crescendo AI supports playlists and scheduling through a YAML configuration file. This allows you to define which music should be played at specific times.

#### Configuration File

By default, the system looks for a configuration file named `music_config.yaml` in the music directory. You can specify a different file using the `--config-path` option.

Here's an example configuration file:

```yaml
# Playlists
playlists:
  # A playlist with a name and an ordered list of paths to audio files
  morning_playlist:
    tracks:
      - "music/track1.mp3"
      - "music/track2.mp3"
      - "music/track3.mp3"

  # A playlist that points to a directory (all files in alphabetical order)
  afternoon_playlist:
    directory: "music/afternoon"

  # A single song as a playlist
  evening_song:
    tracks:
      - "music/evening_track.mp3"

  # Default playlist (used when no playlist is scheduled)
  default:
    directory: "music"

# Schedules
schedules:
  # Schedule by day of week (0 = Monday, 6 = Sunday)
  - days: [0, 1, 2, 3, 4]  # Weekdays
    hours: [7, 8, 9, 10, 11]  # Morning hours
    playlist: "morning_playlist"

  - days: [0, 1, 2, 3, 4]  # Weekdays
    hours: [12, 13, 14, 15, 16, 17]  # Afternoon hours
    playlist: "afternoon_playlist"

  - days: [0, 1, 2, 3, 4]  # Weekdays
    hours: [18, 19, 20, 21, 22, 23]  # Evening hours
    playlist: "evening_song"

  # Weekend schedule
  - days: [5, 6]  # Weekend
    hours: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    playlist: "afternoon_playlist"

  # Specific date and time range
  - date: "2023-12-25"  # Christmas
    hours: [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    playlist: "christmas_playlist"
```

#### Playlist Types

You can define playlists in several ways:

1. **Ordered List of Tracks**: Specify an ordered list of paths to audio files.
   ```yaml
   playlist_name:
     tracks:
       - "path/to/track1.mp3"
       - "path/to/track2.mp3"
   ```

2. **Directory-Based**: Point to a directory, and all audio files in that directory will be included in alphabetical order.
   ```yaml
   playlist_name:
     directory: "path/to/directory"
   ```

3. **Single Song**: A playlist can be as simple as a single song.
   ```yaml
   playlist_name:
     tracks:
       - "path/to/song.mp3"
   ```

4. **Default Playlist**: Define a default playlist to use when no playlist is scheduled.
   ```yaml
   default:
     directory: "music"
   ```

#### Scheduling

You can schedule playlists based on:

1. **Day of Week**: Schedule a playlist for specific days of the week (0 = Monday, 6 = Sunday).
   ```yaml
   - days: [0, 1, 2, 3, 4]  # Weekdays
     hours: [7, 8, 9, 10, 11]  # Morning hours
     playlist: "morning_playlist"
   ```

2. **Specific Date**: Schedule a playlist for a specific date.
   ```yaml
   - date: "2023-12-25"  # Christmas
     hours: [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
     playlist: "christmas_playlist"
   ```

#### Behavior

When presence is detected, the system will:

1. Check the current time to determine which playlist should be active
2. Play the next track from that playlist
3. When the track ends, it will automatically play the next track in the playlist
4. If presence is lost and then detected again, it will continue from the next track in the playlist

### Running as a Service

To run Crescendo AI as a service that starts automatically on boot:

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/crescendo.service
   ```

2. Add the following content (adjust paths as needed):

   **If you installed with Poetry:**
   ```
   [Unit]
   Description=Crescendo AI Music System
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/crescendo-ai
   ExecStart=/home/pi/.local/bin/poetry run python /home/pi/crescendo-ai/crescendo.py
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

   **If you installed with pip:**
   ```
    [Unit]
    Description=Crescendo AI Music System
    After=network.target

    [Service]
    User=pi
    WorkingDirectory=/home/pi/crescendo-ai
    ExecStart=/usr/bin/python3 /home/pi/crescendo-ai/crescendo.py
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable crescendo.service
   sudo systemctl start crescendo.service
   ```

4. Check the status:
   ```bash
   sudo systemctl status crescendo.service
   ```

## Troubleshooting

### Sensor Issues

- Ensure the sensor is properly connected and the correct port is specified
- Check the sensor's documentation for specific setup requirements
- Run with increased logging to debug sensor communication issues

### Relay Issues

- Verify the USB relay is recognized by the system:
  ```bash
  lsusb
  ```
- Check if the relay requires specific drivers or permissions
- Test the relay manually to ensure it's working correctly

### Audio Issues

- Ensure audio output is properly configured on the Raspberry Pi:
  ```bash
  sudo raspi-config
  ```
  Navigate to System Options > Audio to configure the audio output
- Check volume levels using `alsamixer`
- Verify that the music files are in a supported format

## Future Development

### Planned Features

- **Music Selection Based on Context**: Select music based on time of day, weather, or other factors
- **Web Interface**: Control and configure the system through a web browser
- **Multiple Zones**: Support for multiple sensors and speakers in different rooms
- **Voice Control**: Add voice commands to control the system
- **Integration with Music Streaming Services**: Support for Spotify, YouTube Music, etc.

## Guidelines for Future Development

1. **Module Structure**: Keep the modular structure with separate components for sensor, relay, and audio.

2. **Configuration**: Use environment variables or configuration files for settings that might change.

3. **Error Handling**: Maintain robust error handling and logging throughout the codebase.

4. **Testing**: Add unit tests for each component to ensure reliability.

5. **Documentation**: Keep documentation up-to-date with any changes or additions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
