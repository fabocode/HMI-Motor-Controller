"""
Standalone test script for Sartorius Cubis II MCA5201S-2S00-0 scale communication.

Run this on the Raspberry Pi with the scale connected via USB:
    python tests/test_scale_connection.py

Prerequisites:
    - pip install pyserial
    - User must be in 'dialout' group: sudo usermod -a -G dialout $USER
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


def open_port(port, baudrate=9600, bytesize=serial.EIGHTBITS,
              parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE):
    """Open serial port with given parameters."""
    return serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=3.0
    )


def test_passive_listen(port):
    """Test 1: Just listen for any data the scale sends without commands."""
    print("\n--- Test 1: Passive listen (no commands sent) ---")
    print("  Listening for 5 seconds for any data the scale sends...")

    ser = open_port(port)
    try:
        ser.reset_input_buffer()
        start = time.time()
        data = b''
        while time.time() - start < 5.0:
            chunk = ser.read(ser.in_waiting or 1)
            if chunk:
                data += chunk
                print(f"  Received: {chunk!r}")
        if not data:
            print("  No data received passively.")
        else:
            print(f"  Total received: {data!r}")
            print(f"  Decoded: '{data.decode('ascii', errors='replace')}'")
        return bool(data)
    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    finally:
        ser.close()


def test_sbi_commands(port):
    """Test 2: Try SBI commands with different formats."""
    print("\n--- Test 2: SBI command variations ---")

    commands = [
        (b'\x1bS\r\n', "ESC S CR LF (standard SBI immediate)"),
        (b'\x1bP\r\n', "ESC P CR LF (standard SBI print/stable)"),
        (b'\x1bS\r',   "ESC S CR (no LF)"),
        (b'\x1bP\r',   "ESC P CR (no LF)"),
        (b'S\r\n',     "S CR LF (no ESC prefix)"),
        (b'P\r\n',     "P CR LF (no ESC prefix)"),
        (b'\x1bQ\r\n', "ESC Q CR LF (query)"),
        (b'W\r\n',     "W CR LF (weigh command)"),
        (b'\x1b\x70\r\n', "ESC p (lowercase) CR LF"),
    ]

    ser = open_port(port)
    try:
        for cmd, desc in commands:
            ser.reset_input_buffer()
            time.sleep(0.2)
            print(f"\n  Sending {desc}: {cmd!r}")
            ser.write(cmd)
            time.sleep(0.5)

            # Try readline first
            response = ser.readline()
            if not response:
                # Also try reading raw bytes
                response = ser.read(ser.in_waiting or 0)

            if response:
                print(f"  Raw bytes: {response!r}")
                print(f"  Decoded:   '{response.decode('ascii', errors='replace').strip()}'")
                print(f"  SUCCESS with: {desc}")
                return True, cmd, desc
            else:
                print(f"  No response.")

        return False, None, None
    except Exception as e:
        print(f"  ERROR: {e}")
        return False, None, None
    finally:
        ser.close()


def test_serial_configs(port):
    """Test 3: Try different serial configurations with SBI commands."""
    print("\n--- Test 3: Different serial configurations ---")

    configs = [
        (9600,  serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, "9600 8-N-1"),
        (9600,  serial.SEVENBITS, serial.PARITY_ODD,  serial.STOPBITS_ONE, "9600 7-O-1"),
        (9600,  serial.SEVENBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE, "9600 7-E-1"),
        (19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, "19200 8-N-1"),
        (19200, serial.SEVENBITS, serial.PARITY_ODD,  serial.STOPBITS_ONE, "19200 7-O-1"),
        (115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, "115200 8-N-1"),
    ]

    commands = [b'\x1bS\r\n', b'\x1bP\r\n']

    for baud, bits, parity, stop, desc in configs:
        try:
            ser = serial.Serial(
                port=port, baudrate=baud, bytesize=bits,
                parity=parity, stopbits=stop, timeout=2.0
            )
        except serial.SerialException as e:
            print(f"\n  {desc}: ERROR opening - {e}")
            continue

        try:
            for cmd in commands:
                ser.reset_input_buffer()
                time.sleep(0.1)
                ser.write(cmd)
                time.sleep(0.5)
                response = ser.readline()
                if not response:
                    response = ser.read(ser.in_waiting or 0)

                if response:
                    print(f"\n  {desc} + {cmd!r}:")
                    print(f"    Raw: {response!r}")
                    print(f"    Decoded: '{response.decode('ascii', errors='replace').strip()}'")
                    print(f"    SUCCESS!")
                    ser.close()
                    return True
            print(f"  {desc}: no response")
        except Exception as e:
            print(f"  {desc}: ERROR - {e}")
        finally:
            if ser.is_open:
                ser.close()

    return False


def test_raw_dump(port):
    """Test 4: Open port and dump any raw bytes for 10 seconds."""
    print("\n--- Test 4: Raw byte dump (10 seconds, 9600 8-N-1) ---")
    print("  Try pressing PRINT button on the scale during this test!")

    ser = open_port(port)
    try:
        ser.reset_input_buffer()
        start = time.time()
        all_data = b''
        while time.time() - start < 10.0:
            waiting = ser.in_waiting
            if waiting > 0:
                chunk = ser.read(waiting)
                all_data += chunk
                elapsed = time.time() - start
                print(f"  [{elapsed:.1f}s] {chunk!r}")
            time.sleep(0.1)

        if all_data:
            print(f"\n  Total bytes received: {len(all_data)}")
            print(f"  Hex: {all_data.hex(' ')}")
            print(f"  ASCII: '{all_data.decode('ascii', errors='replace')}'")
            return True
        else:
            print("  No bytes received in 10 seconds.")
            return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    finally:
        ser.close()


def main():
    print("=" * 60)
    print("Sartorius Cubis II Scale - Communication Test v2")
    print("=" * 60)

    # Step 1: List ports
    print("\n--- Detecting serial ports ---")
    ports = list_serial_ports()

    candidate_ports = []
    for p in ports:
        if 'ttyACM' in p.device or 'ttyUSB' in p.device or 'COM' in p.device:
            candidate_ports.append(p.device)

    if not candidate_ports:
        print("\nNo candidate serial ports found.")
        sys.exit(1)

    port = candidate_ports[0]
    print(f"\nUsing port: {port}")

    # Test 1: Passive listen
    if test_passive_listen(port):
        print("\n>> Scale sends data without commands (continuous mode)")

    # Test 2: SBI command variations
    success, cmd, desc = test_sbi_commands(port)
    if success:
        print(f"\n>> Working command found: {desc}")

    # Test 3: Different serial configs
    if not success:
        if test_serial_configs(port):
            print("\n>> Found working serial configuration!")

    # Test 4: Raw dump (last resort - asks user to press PRINT on scale)
    if not success:
        test_raw_dump(port)

    print("\n" + "=" * 60)
    print("DONE. Share the output above so we can determine next steps.")
    print("=" * 60)


if __name__ == '__main__':
    main()
