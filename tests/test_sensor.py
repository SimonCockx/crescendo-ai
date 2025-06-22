#!/usr/bin/env python3
"""
Test script for the updated PresenceSensor class.
"""

import sys
import time
import logging
from crescendo_ai.sensor import PresenceSensor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_sensor(port='/dev/ttyAMA0'):
    """Test the PresenceSensor class with the specified port."""
    logger.info(f"Testing PresenceSensor on port {port}")
    
    # Create sensor instance
    sensor = PresenceSensor(port=port)
    
    try:
        # Connect to sensor
        logger.info("Connecting to sensor...")
        if not sensor.connect():
            logger.error("Failed to connect to sensor")
            return False
        
        logger.info("Connected to sensor")
        
        # Configure sensor
        logger.info("Configuring sensor...")
        config_ok = sensor.configure(
            max_motion_gate=6,
            max_static_gate=4,
            no_one_duration=10,
            motion_sensitivity=[50, 50, 40, 30, 20, 15, 15, 15],
            static_sensitivity=[0, 0, 40, 40, 30, 30, 20, 20]
        )
        
        if not config_ok:
            logger.warning("Failed to configure sensor - continuing with default configuration")
        
        # Read data for 10 seconds
        logger.info("Reading data for 10 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            data = sensor.read_data()
            
            if data:
                logger.info(f"Data received: {data}")
                logger.info(f"Presence detected: {sensor.is_presence_detected()}")
            else:
                logger.warning("No data received")
            
            time.sleep(1)
        
        logger.info("Test completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return False
    finally:
        # Disconnect sensor
        logger.info("Disconnecting sensor...")
        sensor.disconnect()
    
    return False

if __name__ == "__main__":
    # Use command line argument for port if provided
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyAMA0'
    test_sensor(port)