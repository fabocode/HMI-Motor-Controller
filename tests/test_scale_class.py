"""
Test script for the Scale sensor class.

Run this on the Raspberry Pi with the scale connected via USB:
    python tests/test_scale_class.py

This tests the production Scale class (hmi/sensors/scale.py) by:
1. Instantiating it and letting the background thread connect
2. Printing get_weight(), is_connected(), is_stable() in a loop
3. Monitoring for 60 seconds — place/remove objects to verify weight changes

Prerequisites:
    - pip install pyserial
    - User must be in 'dialout' group
"""

import sys
import os
import time

# Add hmi directory to path so we can import sensors.scale
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hmi'))

from sensors.scale import Scale


def main():
    print("=" * 60)
    print("Scale Class Test")
    print("=" * 60)

    print("\nInstantiating Scale (auto-detect port)...")
    scale = Scale()

    # Give the background thread a moment to connect and get first reading
    time.sleep(2.0)

    print(f"  Connected: {scale.is_connected()}")
    if not scale.is_connected():
        print("  WARNING: Scale not connected. Will keep trying (auto-reconnect)...")
    print()

    print("--- Live readings for 60 seconds ---")
    print("  Place/remove objects on the scale to see changes.")
    print("  Press Ctrl+C to stop early.\n")

    try:
        for i in range(60):
            weight = scale.get_weight()
            connected = scale.is_connected()
            stable = scale.is_stable()
            status = "STABLE" if stable else "UNSTABLE"
            conn = "OK" if connected else "DISCONNECTED"

            print(f"  [{i+1:3d}s]  {weight:>8.1f} g  |  {status:<10s}  |  {conn}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n  Stopped by user.")

    print(f"\nFinal reading: {scale.get_weight()} {scale.get_unit()}")
    print(f"Connected: {scale.is_connected()}")

    scale.close()
    print("\nScale closed. Done.")


if __name__ == '__main__':
    main()
