"""
Standalone test script for Sartorius Cubis II MCA5201S-2S00-0 scale communication.

Run this on the Raspberry Pi with the scale connected via USB:
    python tests/test_scale_connection.py

Confirmed working config:
    Port: /dev/ttyACM0
    Baud: 19200, 8-N-1
    Command: ESC P (b'\\x1bP\\r\\n') - stable weight read
    Response: 22-byte extended SBI, e.g. 'G            0.0 g  \\r\\n'

Prerequisites:
    - pip install pyserial
    - User must be in 'dialout' group: sudo usermod -a -G dialout $USER
"""

import serial
import serial.tools.list_ports
import re
import time
import sys

# Confirmed working parameters
PORT = '/dev/ttyACM0'
BAUD = 19200
BYTESIZE = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
TIMEOUT = 3.0

# SBI commands
CMD_STABLE_READ = b'\x1bP\r\n'
CMD_IMMEDIATE_READ = b'\x1bS\r\n'

# Regex to parse weight from response like 'G            0.0 g'
WEIGHT_RE = re.compile(r'([+-]?\s*[\d.]+)\s+(\w+)')


def list_serial_ports():
    """List all available serial ports."""
    ports = serial.tools.list_ports.comports()
    print("Available serial ports:")
    for p in ports:
        print(f"  {p.device} - {p.description} [VID:PID={p.vid}:{p.pid}]")
    return ports


def open_scale():
    """Open serial connection to the scale."""
    return serial.Serial(
        port=PORT,
        baudrate=BAUD,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS,
        timeout=TIMEOUT
    )


def parse_response(raw):
    """Parse SBI response into weight value and unit."""
    text = raw.decode('ascii', errors='replace').strip()
    match = WEIGHT_RE.search(text)
    if match:
        value = float(match.group(1).replace(' ', ''))
        unit = match.group(2)
        return value, unit, text
    return None, None, text


def main():
    print("=" * 60)
    print("Sartorius Cubis II Scale - Confirmed Config Test")
    print(f"  Port: {PORT} | Baud: {BAUD} | Format: 8-N-1")
    print("=" * 60)

    # List ports
    list_serial_ports()

    # Open connection
    print(f"\nOpening {PORT}...")
    try:
        ser = open_scale()
    except serial.SerialException as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Connected!\n")

    # Test 1: Stable read (ESC P) — 5 consecutive reads
    print("--- Test 1: ESC P (stable read) x5 ---")
    for i in range(5):
        ser.reset_input_buffer()
        ser.write(CMD_STABLE_READ)
        raw = ser.readline()
        value, unit, text = parse_response(raw)
        print(f"  Read {i+1}: raw={raw!r}  parsed={value} {unit}")
        time.sleep(1.0)

    # Test 2: Immediate read (ESC S) — check if this also works
    print("\n--- Test 2: ESC S (immediate read) x5 ---")
    for i in range(5):
        ser.reset_input_buffer()
        ser.write(CMD_IMMEDIATE_READ)
        raw = ser.readline()
        value, unit, text = parse_response(raw)
        if raw:
            print(f"  Read {i+1}: raw={raw!r}  parsed={value} {unit}")
        else:
            print(f"  Read {i+1}: No response (ESC S not supported)")
            if i == 0:
                print("  Skipping remaining ESC S tests.")
                break
        time.sleep(1.0)

    # Test 3: Place something on the scale
    print("\n--- Test 3: Live monitoring for 15 seconds ---")
    print("  Place/remove objects on the scale to see value changes!")
    start = time.time()
    while time.time() - start < 15.0:
        ser.reset_input_buffer()
        ser.write(CMD_STABLE_READ)
        raw = ser.readline()
        value, unit, text = parse_response(raw)
        elapsed = time.time() - start
        if value is not None:
            print(f"  [{elapsed:5.1f}s] {value:>10} {unit}")
        else:
            print(f"  [{elapsed:5.1f}s] (no response or parse error: '{text}')")
        time.sleep(1.0)

    ser.close()
    print("\n" + "=" * 60)
    print("DONE. Share the output above.")
    print("=" * 60)


if __name__ == '__main__':
    main()
