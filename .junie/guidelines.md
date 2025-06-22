# Crescendo AI Development Guidelines

This document provides essential information for developers working on the Crescendo AI project.

## Build/Configuration Instructions

### Environment Setup

1. **Python Version**: The project requires Python 3.9 or higher.

2. **Poetry Installation**: The project uses Poetry for dependency management.
   ```bash
   # Install Poetry if not already installed
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Project Installation**:
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/crescendo-ai.git
   cd crescendo-ai
   
   # Install dependencies
   poetry install
   ```

### Hardware Configuration

When deploying on a Raspberry Pi:

1. **Sensor Configuration**: The 24GHz mmWave sensor should be connected via a USB-to-Serial adapter. The default port is `/dev/ttyAMA0`, but this can be configured using the `--sensor-port` option.

2. **USB Relay Setup**: The USB relay should be connected to a USB port on the Raspberry Pi. No additional configuration is needed as the system automatically detects the relay.

3. **Audio Output**: Configure the Raspberry Pi's audio output using:
   ```bash
   sudo raspi-config
   # Navigate to System Options > Audio to configure the audio output
   ```

## Testing Information

### Running Tests

1. **Simulation Tests**: The project includes a simulation mode that doesn't require hardware:
   ```bash
   # Run the simulation test
   python run_tests.py
   ```

2. **Unit Tests**: Individual unit tests can be run using the unittest framework:
   ```bash
   # Run a specific test file
   python tests/test_audio_player.py
   
   # Run all tests with unittest discovery
   python -m unittest discover -s tests
   ```

### Adding New Tests

1. **Test Structure**: Tests should be organized in the `tests` directory with filenames starting with `test_`.

2. **Test Classes**: Use the `unittest` framework and create test classes that inherit from `unittest.TestCase`.

3. **Simulation Components**: For hardware-dependent components, create simulated versions for testing, similar to the existing `SimulatedPresenceSensor`, `SimulatedUSBRelay`, and `SimulatedAudioPlayer` classes in `test_simulation.py`.

4. **Example Test**:
   ```python
   import unittest
   from crescendo_ai.some_module import SomeClass
   
   class TestSomeClass(unittest.TestCase):
       def setUp(self):
           # Setup code runs before each test
           self.instance = SomeClass()
       
       def tearDown(self):
           # Cleanup code runs after each test
           pass
       
       def test_some_functionality(self):
           # Test a specific functionality
           result = self.instance.some_method()
           self.assertEqual(result, expected_value)
   
   if __name__ == "__main__":
       unittest.main()
   ```

5. **Running Your Test**: Make your test executable and run it directly:
   ```bash
   chmod +x tests/your_test_file.py
   ./tests/your_test_file.py
   ```

## Additional Development Information

### Code Style

1. **PEP 8**: Follow the PEP 8 style guide for Python code.

2. **Docstrings**: Use Google-style docstrings for all modules, classes, and methods:
   ```python
   def function(arg1, arg2):
       """Short description of the function.
       
       Longer description if needed.
       
       Args:
           arg1: Description of arg1
           arg2: Description of arg2
           
       Returns:
           Description of return value
           
       Raises:
           ExceptionType: When and why this exception is raised
       """
       # Function implementation
   ```

3. **Type Hints**: Use type hints for function parameters and return values:
   ```python
   from typing import List, Dict, Optional
   
   def function(param1: str, param2: Optional[int] = None) -> List[Dict[str, str]]:
       # Function implementation
   ```

### Project Structure

1. **Module Organization**:
   - `crescendo_ai/`: Main package
     - `__init__.py`: Package initialization
     - `sensor.py`: Presence sensor interface
     - `relay.py`: USB relay control
     - `audio.py`: Audio playback functionality
     - `main.py`: Main system coordination
   - `tests/`: Test package
   - `crescendo.py`: Entry point script

2. **Component Design**: The system follows a modular design with separate components for:
   - Presence detection (sensor.py)
   - Power control (relay.py)
   - Audio playback (audio.py)
   - System coordination (main.py)

3. **Adding New Features**: When adding new features:
   - Create a new module in the `crescendo_ai` package if appropriate
   - Update the `CrescendoSystem` class in `main.py` to integrate the new feature
   - Add appropriate tests in the `tests` directory

### Debugging

1. **Logging**: The system uses Python's logging module. Increase verbosity for debugging:
   ```bash
   # Set log level to DEBUG
   export LOGLEVEL=DEBUG
   python crescendo.py
   ```

2. **Simulation Mode**: Use the simulation mode for testing without hardware:
   ```bash
   python run_tests.py
   ```

3. **Common Issues**:
   - **Sensor Connection**: If the sensor doesn't connect, check the port with `ls /dev/tty*`
   - **Audio Issues**: Test audio output with `aplay /usr/share/sounds/alsa/Front_Center.wav`
   - **USB Relay**: Check if the relay is detected with `lsusb`