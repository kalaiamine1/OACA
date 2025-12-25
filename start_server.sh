#!/bin/bash
# OACA Server Startup Script for Linux/Mac
# This script starts the Flask server and displays network access information

echo ""
echo "============================================================"
echo "  OACA Aviation Administration - Server Startup"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Get the local IP address
IP=$(hostname -I | awk '{print $1}')
if [ -z "$IP" ]; then
    IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}')
fi

if [ ! -z "$IP" ]; then
    echo "Found IP address: $IP"
    echo ""
fi

echo "Starting server..."
echo ""

# Start the Python server
python3 start_server.py

