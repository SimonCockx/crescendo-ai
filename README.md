# Crescendo AI

A Raspberry Pi-based system that plays background music when someone is present in a room.

> **Note:** For quick setup instructions, see [GETTING_STARTED.md](GETTING_STARTED.md)

## Overview

Crescendo AI is a smart music player system that uses a 24GHz mmWave Human Static Presence Sensor to detect human presence in a room. When someone is detected, the system turns on a speaker via a USB relay and plays background music. When no one is detected for a specified period, the music stops and the speaker is turned off to save power.

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
- `--presence-timeout`: Time in seconds to wait after last detection before stopping music (default: `30.0`)

Example:
```bash
python crescendo.py --sensor-port /dev/ttyAMA0 --music-dir ~/Music --presence-timeout 60.0
```

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
