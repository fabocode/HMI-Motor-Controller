#!/usr/bin/env python3
"""Try common AMS Net ID patterns to find the correct one for the PLC.

The PLC at 110.110.110.20 has ADS running (TCP 48898 open) but we don't
know its AMS Net ID. This script tries common patterns.

Run on the Pi:
    python find_ams_netid.py
"""

import pyads
import sys

PLC_IP = '110.110.110.20'
AMS_PORT = pyads.PORT_TC2PLC1  # 801
LOCAL_AMS = '110.110.110.11.1.1'

# Common AMS Net ID patterns for Beckhoff controllers:
# - IP-based: x.x.x.x.1.1 (most common)
# - Factory default: 5.x.x.x.1.1 or 172.x.x.x.1.1
# - Custom: could be anything, but often x.x.x.x.1.1
CANDIDATES = [
    '110.110.110.20.1.1',   # IP-based (already tried)
    '5.0.0.20.1.1',         # Beckhoff CX-series default pattern
    '5.20.110.110.1.1',     # reversed octets variant
    '172.16.0.1.1.1',       # common embedded default
    '192.168.1.1.1.1',      # another common default
    '1.1.1.1.1.1',          # minimal default
    '10.10.10.10.1.1',      # round number default
    '5.2.100.115.1.1',      # CX8090 style
    '5.10.110.20.1.1',      # Beckhoff embedded variant
    '110.110.110.20.2.1',   # IP with different subnet ID
]

print(f"Local AMS:  {LOCAL_AMS}")
print(f"Target IP:  {PLC_IP}")
print(f"AMS Port:   {AMS_PORT}")
print(f"Testing {len(CANDIDATES)} AMS Net ID candidates...")
print()

pyads.open_port()
pyads.set_local_address(LOCAL_AMS)

for ams_id in CANDIDATES:
    sys.stdout.write(f"  Trying {ams_id:<30s} ... ")
    sys.stdout.flush()
    try:
        plc = pyads.Connection(ams_id, AMS_PORT, PLC_IP)
        plc.open()
        state = plc.read_state()
        print(f"SUCCESS! State: {state}")
        print()
        print(f"  >>> Found correct AMS Net ID: {ams_id} <<<")
        plc.close()
        pyads.close_port()
        sys.exit(0)
    except pyads.ADSError as e:
        if '1861' in str(e):  # timeout
            print("timeout")
        else:
            print(f"ADS error: {e}")
    except Exception as e:
        print(f"{type(e).__name__}: {e}")
    finally:
        try:
            plc.close()
        except Exception:
            pass

pyads.close_port()
print()
print("None of the common patterns worked.")
print()
print("Next steps:")
print("  - Ask the feeder integrator/OEM for the AMS Net ID")
print("  - Or check TwinCAT System Manager if it can be accessed remotely")
