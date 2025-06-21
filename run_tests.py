#!/usr/bin/env python3
"""
Script to run tests for the Crescendo AI system.

This script provides a convenient way to run the simulation tests
for the Crescendo AI system.
"""

import os
import sys
import logging
from tests.test_simulation import run_simulation

if __name__ == "__main__":
    print("Running Crescendo AI simulation tests...")
    run_simulation()
    print("Tests completed.")