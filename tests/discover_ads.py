#!/usr/bin/env python3
"""Discover Beckhoff TwinCAT devices on the network via UDP broadcast.

TwinCAT devices listen on UDP port 48899 for discovery broadcasts.
This script sends a discovery packet and prints any responses,
revealing the actual AMS Net ID of the device.

Run on the Pi:
    python discover_ads.py
"""

import socket
import struct
import sys

BROADCAST_PORT = 48899
TIMEOUT = 5  # seconds

# TwinCAT UDP discovery request packet
# This is a minimal ADS discovery broadcast frame
DISCOVER_PACKET = (
    b'\x03\x66\x14\x71'   # magic / header
    b'\x00\x00\x00\x00'
    b'\x00\x00\x00\x00'
    b'\x01\x00\x00\x00'
    b'\x00\x00\x00\x00'
)

print(f"Sending TwinCAT discovery broadcast on UDP port {BROADCAST_PORT}...")
print(f"Timeout: {TIMEOUT}s")
print()

# Try both broadcast and direct UDP to the known IP
targets = [
    ('255.255.255.255', 'broadcast'),
    ('110.110.110.255', 'subnet broadcast'),
    ('110.110.110.20', 'direct'),
]

for target_ip, label in targets:
    print(f"--- Trying {label} ({target_ip}:{BROADCAST_PORT}) ---")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(TIMEOUT)
        sock.sendto(DISCOVER_PACKET, (target_ip, BROADCAST_PORT))

        try:
            while True:
                data, addr = sock.recvfrom(4096)
                print(f"  Response from {addr[0]}:{addr[1]} ({len(data)} bytes)")
                print(f"  Raw hex: {data.hex()}")

                # Try to extract AMS Net ID from response
                # AMS Net ID is typically 6 bytes somewhere in the response
                if len(data) >= 6:
                    # Common offset for AMS Net ID in discovery responses
                    for offset in [0, 4, 8, 12, 16, 20, 24]:
                        if offset + 6 <= len(data):
                            ams = data[offset:offset + 6]
                            ams_str = '.'.join(str(b) for b in ams)
                            # Filter for plausible AMS Net IDs (first octet > 0, not all zeros)
                            if ams[0] > 0 and any(b > 0 for b in ams[1:]):
                                print(f"  Possible AMS Net ID at offset {offset}: {ams_str}")
                print()
        except socket.timeout:
            print("  No (more) responses.")
        finally:
            sock.close()
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    print()

# Also try a simple TCP connect to ADS port to confirm it's reachable
print("--- Checking TCP port 48898 (ADS) ---")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex(('110.110.110.20', 48898))
    if result == 0:
        print("  Port 48898 is OPEN (ADS TCP)")
    else:
        print(f"  Port 48898 is CLOSED (error code {result})")
    sock.close()
except Exception as e:
    print(f"  Error: {type(e).__name__}: {e}")
