#!/usr/bin/env python3
"""
OACA Server Startup Script
This script starts the Flask server and displays the network IP addresses
so you can access the application from other devices on the network.
"""

import os
import socket
import sys
from app import app, ensure_default_user

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't actually connect, just determines the local IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_all_ips():
    """Get all network IP addresses"""
    ips = []
    try:
        hostname = socket.gethostname()
        # Get all IP addresses
        for addr in socket.gethostbyname_ex(hostname)[2]:
            if not addr.startswith("127."):
                ips.append(addr)
    except Exception:
        pass
    
    # Fallback to local IP
    if not ips:
        local_ip = get_local_ip()
        if local_ip != "127.0.0.1":
            ips.append(local_ip)
    
    return ips if ips else ["127.0.0.1"]

def print_startup_info(port):
    """Print startup information with network access URLs"""
    print("\n" + "="*60)
    print("  OACA Aviation Administration - Server Starting")
    print("="*60)
    
    local_ip = get_local_ip()
    all_ips = get_all_ips()
    
    print(f"\n📍 Server is running on port: {port}")
    print(f"\n🌐 Access the application from:")
    print(f"   • This computer:     http://localhost:{port}")
    print(f"   • This computer:     http://127.0.0.1:{port}")
    
    if all_ips:
        print(f"\n💻 Access from other devices on the network:")
        for ip in all_ips:
            print(f"   • http://{ip}:{port}")
    
    print(f"\n📱 To access from other devices:")
    print(f"   1. Make sure they are on the same network")
    print(f"   2. Use one of the IP addresses above")
    print(f"   3. Example: http://{local_ip if local_ip != '127.0.0.1' else all_ips[0] if all_ips else 'YOUR_IP'}:{port}")
    
    print(f"\n⚠️  Note: Make sure your firewall allows connections on port {port}")
    print("="*60 + "\n")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    
    # Ensure default user exists
    ensure_default_user()
    
    # Print startup information
    print_startup_info(port)
    
    # Start the Flask server
    print("🚀 Starting Flask server...\n")
    app.run(host="0.0.0.0", port=port, debug=True)

