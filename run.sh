#!/bin/bash
# Quick launch script for V-Li Switch Manager

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export SM_USER=$(whoami)
export SM_CSV_DATA="data.csv"
export SM_DELIMITER=";"

# Run the application
python -m switch_manager
