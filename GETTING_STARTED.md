# Getting Started with Crescendo AI

This guide provides the essential steps to quickly set up and run the Crescendo AI system. For comprehensive documentation, please refer to the [README.md](README.md).

## Quick Setup

1. **Set Up a Virtual Environment**:

   Note: This step is only necessary when not using Poetry, since Poetry manages its own virtual environment.

   Create and activate a virtual environment to avoid conflicts with system packages:
   ```bash
   # Create a virtual environment
   python3 -m venv venv

   # Activate the virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```

   Your command prompt should now show `(venv)` at the beginning, indicating the virtual environment is active.

2. **Install Dependencies**:

   **Option 1: Using Poetry** (recommended for development):
   ```bash
   poetry install
   ```

   **Option 2: Using pip** (faster setup on Raspberry Pi):
   ```bash
   pip install -r requirements.txt
   ```

   Note: Always ensure your virtual environment is activated before installing packages with pip.

3. **Add Music**:
   ```bash
   mkdir music
   # Copy your music files to the music directory
   ```

4. **Run the System**:

   With Poetry:
   ```bash
   poetry run python crescendo.py
   ```

   With pip:
   ```bash
   python crescendo.py
   ```

5. **Test Without Hardware**:
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
