#!/usr/bin/env python3
"""
Startup script for the Health Monitor application.
This script provides an easy way to run the Health Monitor with default settings.
"""
import sys
import os

# Add the current directory to Python path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from health_monitor.main import main

if __name__ == "__main__":
    main()