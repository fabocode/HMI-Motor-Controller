#!/usr/bin/env python3
"""Standalone ADS connectivity test for the Beckhoff TwinCAT 2 screw feeder.

Run on the Pi (110.110.110.11) with:
    python test_ads_connection.py

Prerequisites:
    pip install pyads
"""

import pyads
import sys

# --- Configuration ---
LOCAL_AMS_NET_ID = '110.110.110.11.1.1'   # Pi's AMS Net ID
PLC_AMS_NET_ID = '110.110.110.20.1.1'     # Feeder PLC's AMS Net ID
PLC_IP = '110.110.110.20'
AMS_PORT = pyads.PORT_TC2PLC1             # 801 for TwinCAT 2
TEST_VARIABLE = 'MAIN.Feeder1.FeederStatus.Weight'

# Default TwinCAT credentials (try these first)
PLC_USERNAME = 'Administrator'
PLC_PASSWORD = ''

print(f"Local AMS Net ID:  {LOCAL_AMS_NET_ID}")
print(f"Target AMS Net ID: {PLC_AMS_NET_ID}")
print(f"Target IP:         {PLC_IP}")
print(f"Target AMS Port:   {AMS_PORT}")
print(f"Test variable:     {TEST_VARIABLE}")
print()

# Step 1: Open AMS port and set local address (required on Linux)
print("[1] Setting up local AMS router...")
try:
    pyads.open_port()
    pyads.set_local_address(LOCAL_AMS_NET_ID)
    print(f"    OK - local AMS address set to {LOCAL_AMS_NET_ID}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
    sys.exit(1)

# Step 2: Try to add route to PLC from Pi side
print(f"[2] Adding ADS route to PLC (user={PLC_USERNAME}, pass={'(blank)' if not PLC_PASSWORD else '***'})...")
try:
    pyads.add_route_to_plc(
        LOCAL_AMS_NET_ID,
        PLC_IP,
        PLC_IP,
        PLC_USERNAME,
        PLC_PASSWORD,
        route_name='RaspberryPi'
    )
    print("    OK - route added (or already exists)")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
    print()
    print("    This likely means wrong credentials. Common options to try:")
    print("      - Administrator / (blank)")
    print("      - Administrator / 1")
    print("      - Guest / (blank)")
    print("    Ask the feeder guy for the TwinCAT login credentials.")
    print()
    print("    Continuing anyway in case a route already exists...")

# Step 3: Try to connect
print("[3] Opening ADS connection...")
try:
    plc = pyads.Connection(PLC_AMS_NET_ID, AMS_PORT)
    plc.open()
    print("    OK - connection opened")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
    pyads.close_port()
    sys.exit(1)

# Step 4: Check connection state
print("[4] Checking ADS state...")
try:
    state = plc.read_state()
    print(f"    OK - ADS state: {state}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
    print()
    print("Troubleshooting:")
    print("  - If timeout: route was not accepted, or AMS Net ID is wrong.")
    print("  - Try different PLC credentials in step 2.")
    print("  - The PLC's AMS Net ID might not be 110.110.110.20.1.1.")
    plc.close()
    pyads.close_port()
    sys.exit(1)

# Step 5: Try to read a single variable
print(f"[5] Reading '{TEST_VARIABLE}'...")
try:
    value = plc.read_by_name(TEST_VARIABLE, pyads.PLCTYPE_REAL)
    print(f"    OK - value: {value}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")

# Step 6: Try reading a few more variables
print("[6] Reading additional variables...")
test_vars = [
    ('MAIN.Feeder1.FeederStatus.TotalMass', pyads.PLCTYPE_REAL),
    ('MAIN.Feeder1.FeederStatus.MassFlow', pyads.PLCTYPE_REAL),
    ('MAIN.Feeder1.HmiLogic.CurrentStateStr', pyads.PLCTYPE_STRING),
    ('MAIN.Feeder1.FeedingModule.ServoDrive.MotorVelocity', pyads.PLCTYPE_REAL),
]
for name, plc_type in test_vars:
    try:
        value = plc.read_by_name(name, plc_type)
        print(f"    OK - {name} = {value}")
    except Exception as e:
        print(f"    FAIL - {name}: {type(e).__name__}: {e}")

# Cleanup
print()
print("[7] Closing connection...")
plc.close()
pyads.close_port()
print("    Done.")
