"""
Standalone test script for Sartorius Cubis II MCA5201S-2S00-0 scale communication.

Run this on the Raspberry Pi with the scale connected via USB:
    python tests/test_scale_connection.py

Prerequisites:
    - pip install pyserial
    - User must be in 'dialout' group: sudo usermod -a -G dialout $USER
    - Scale touchscreen: Menu > Communication > USB > Protocol = SBI
"""

import serial
import serial.tools.list_ports
import time
import sys


def list_serial_ports():
    """List all available serial ports."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found.")
        return []
    print("Available serial ports:")
    for p in ports:
        print(f"  {p.device} - {p.description} [VID:PID={p.vid}:{p.pid}]")
    return ports


def try_read_weight(port, baudrate, bytesize, parity, stopbits):
    """Attempt to read weight from the scale with given serial parameters."""
    params_str = f"{baudrate} baud, {bytesize} data bits, parity={parity}, {stopbits} stop bits"
    print(f"\nTrying: {port} @ {params_str}")

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=2.0
        )
    except serial.SerialException as e:
        print(f"  ERROR opening port: {e}")
        return False

    try:
        # Flush any stale data
        ser.reset_input_buffer()
        time.sleep(0.1)

        # Send SBI immediate read command (ESC S)
        cmd = b'\x1bS\r\n'
        print(f"  Sending: {cmd!r}")
        ser.write(cmd)

        # Read response
        response_raw = ser.readline()
        print(f"  Raw bytes:   {response_raw!r}")
        print(f"  Decoded:     '{response_raw.decode('ascii', errors='replace').strip()}'")

        if not response_raw:
            print("  No response received (timeout).")
            # Try stable read command as fallback
            print("  Retrying with ESC P (stable read)...")
            ser.write(b'\x1bP\r\n')
            response_raw = ser.readline()
            print(f"  Raw bytes:   {response_raw!r}")
            print(f"  Decoded:     '{response_raw.decode('ascii', errors='replace').strip()}'")

        if response_raw:
            print("  SUCCESS - got a response!")
            return True
        else:
            print("  No response.")
            return False

    except Exception as e:
        print(f"  ERROR during communication: {e}")
        return False
    finally:
        ser.close()


def main():
    print("=" * 60)
    print("Sartorius Cubis II Scale - Communication Test")
    print("=" * 60)

    # Step 1: List ports
    print("\n--- Step 1: Detecting serial ports ---")
    ports = list_serial_ports()

    # Find likely scale port (ttyACM or ttyUSB devices)
    candidate_ports = []
    for p in ports:
        if 'ttyACM' in p.device or 'ttyUSB' in p.device:
            candidate_ports.append(p.device)

    if not candidate_ports:
        # On Windows, look for COM ports
        for p in ports:
            if 'COM' in p.device:
                candidate_ports.append(p.device)

    if not candidate_ports:
        print("\nNo candidate serial ports found.")
        print("Check that the scale is connected via USB and powered on.")
        sys.exit(1)

    print(f"\nCandidate ports: {candidate_ports}")

    # Step 2: Try each port with different serial configurations
    print("\n--- Step 2: Testing communication ---")

    configs = [
        # Default SBI: 9600, 7-O-1
        (9600, serial.SEVENBITS, serial.PARITY_ODD, serial.STOPBITS_ONE),
        # Alternative: 19200, 7-O-1
        (19200, serial.SEVENBITS, serial.PARITY_ODD, serial.STOPBITS_ONE),
        # Alternative: 9600, 8-N-1
        (9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE),
        # Alternative: 19200, 8-N-1
        (19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE),
    ]

    success = False
    for port in candidate_ports:
        for baudrate, bytesize, parity, stopbits in configs:
            if try_read_weight(port, baudrate, bytesize, parity, stopbits):
                success = True
                print(f"\n{'=' * 60}")
                print(f"WORKING CONFIG FOUND!")
                print(f"  Port:      {port}")
                print(f"  Baud rate: {baudrate}")
                print(f"  Data bits: {bytesize}")
                print(f"  Parity:    {parity}")
                print(f"  Stop bits: {stopbits}")
                print(f"{'=' * 60}")

                # Do a few more reads to confirm
                print("\nPerforming 5 consecutive reads (1 second apart)...")
                try:
                    ser = serial.Serial(
                        port=port,
                        baudrate=baudrate,
                        bytesize=bytesize,
                        parity=parity,
                        stopbits=stopbits,
                        timeout=2.0
                    )
                    for i in range(5):
                        ser.reset_input_buffer()
                        ser.write(b'\x1bS\r\n')
                        resp = ser.readline()
                        decoded = resp.decode('ascii', errors='replace').strip()
                        print(f"  Read {i+1}: '{decoded}'")
                        time.sleep(1.0)
                    ser.close()
                except Exception as e:
                    print(f"  Error during consecutive reads: {e}")

                return
        if not success:
            print(f"\nNo working config found for {port}")

    if not success:
        print("\n" + "=" * 60)
        print("FAILED: Could not communicate with the scale.")
        print("Troubleshooting:")
        print("  1. Check scale is powered on and USB cable is connected")
        print("  2. On the scale touchscreen: Menu > Communication > USB")
        print("     - Protocol should be set to 'SBI'")
        print("  3. Verify user is in dialout group:")
        print("     sudo usermod -a -G dialout $USER")
        print("     (then log out and back in)")
        print("  4. Check dmesg for USB device detection:")
        print("     dmesg | tail -20")
        print("=" * 60)


if __name__ == '__main__':
    main()
