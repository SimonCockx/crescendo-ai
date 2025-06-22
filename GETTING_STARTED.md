# Getting Started with Crescendo AI

This guide provides the essential steps to quickly set up and run the Crescendo AI system. For comprehensive documentation, please refer to the [README.md](README.md).

## Quick Setup

1. **Install Dependencies**:

   **Option 1: Using Poetry** (recommended for development):
   ```bash
   poetry install
   ```

   **Option 2: Using pip** (faster setup on Raspberry Pi):
   ```bash
   pip install -r requirements.txt
   ```

2. **Add Music**:
   ```bash
   mkdir music
   # Copy your music files to the music directory
   ```

3. **Run the System**:

   With Poetry:
   ```bash
   poetry run python crescendo.py
   ```

   With pip:
   ```bash
   python crescendo.py
   ```

4. **Test Without Hardware**:
   If you don't have the hardware components yet:

   ```bash
   # With Poetry
   poetry run python run_tests.py

   # With pip
   python run_tests.py
   ```

## Basic Hardware Setup

1. **Presence Sensor**: Connect to USB port (default: `/dev/ttyAMA0`)
2. **USB Relay**: Connect to USB port and to speaker's power input
3. **Speaker**: Connect audio to Raspberry Pi and power to relay

## Common Command-line Options

```bash
python crescendo.py --sensor-port /dev/ttyAMA0 --music-dir ~/Music --presence-timeout 60.0
```

For detailed information about:
- Complete hardware setup instructions
- Running as a service
- Troubleshooting
- Project structure
- Future development

Please see the [README.md](README.md) file.
