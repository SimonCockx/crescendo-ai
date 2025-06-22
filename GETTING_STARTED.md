# Getting Started with Crescendo AI

This guide provides a quick overview of how to get started with the Crescendo AI system.

## What is Crescendo AI?

Crescendo AI is a Raspberry Pi-based system that plays background music when someone is present in a room. It uses:

- A 24GHz mmWave Human Static Presence Sensor to detect human presence
- A USB relay to control power to a speaker
- Pygame for audio playback

## Quick Start

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Add Music**:
   Create a `music` directory and add some music files (MP3, WAV, OGG, or FLAC formats).
   ```bash
   mkdir music
   # Copy your music files to the music directory
   ```

3. **Run the System**:
   ```bash
   poetry run python crescendo.py
   ```

4. **Test Without Hardware**:
   If you don't have the hardware components yet, you can run the simulation:
   ```bash
   poetry run python run_tests.py
   ```

## Hardware Setup

1. **Presence Sensor**:
   - Connect the 24GHz mmWave sensor to a USB port on the Raspberry Pi using a USB-to-Serial adapter
   - Default port is `/dev/ttyAMA0` (can be changed with `--sensor-port` option)

2. **USB Relay**:
   - Connect the USB relay to another USB port on the Raspberry Pi
   - Connect the speaker's power input to the relay's output

3. **Speaker**:
   - Connect the speaker's audio input to the Raspberry Pi's audio output (3.5mm jack or HDMI)
   - Connect the speaker's power input to the USB relay

## Command-line Options

The system supports several command-line options:

- `--sensor-port`: Serial port for the presence sensor (default: `/dev/ttyAMA0`)
- `--music-dir`: Directory containing music files (default: `music`)
- `--check-interval`: Interval in seconds between presence checks (default: `1.0`)
- `--presence-timeout`: Time in seconds to wait after last detection before stopping music (default: `30.0`)

Example:
```bash
python crescendo.py --sensor-port /dev/ttyAMA0 --music-dir ~/Music --presence-timeout 60.0
```

## Project Structure

- `crescendo_ai/`: Main package
  - `__init__.py`: Package initialization
  - `sensor.py`: Presence sensor interface
  - `relay.py`: USB relay control
  - `audio.py`: Audio playback functionality
  - `main.py`: Main system coordination
- `tests/`: Test package
  - `test_simulation.py`: Simulation for testing without hardware
- `crescendo.py`: Entry point script
- `run_tests.py`: Script to run tests
- `README.md`: Detailed documentation
- `GETTING_STARTED.md`: This quick start guide

## Next Steps

1. **Customize Music Selection**:
   - Add your favorite music to the `music` directory
   - Modify the `audio.py` module to implement context-based selection (e.g., by time of day)

2. **Automate Startup**:
   - Set up the system to run as a service (see README.md for instructions)

3. **Extend Functionality**:
   - Add a web interface for remote control
   - Implement multiple zones with different sensors and speakers
   - Add voice control capabilities

For more detailed information, see the [README.md](README.md) file.