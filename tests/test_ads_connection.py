#!/usr/bin/env python3
"""Standalone ADS connectivity test for the Beckhoff TwinCAT 2 screw feeder.

Run on the Pi (110.110.110.11) with:
    python test_ads_connection.py

Prerequisites:
    pip install pyads
"""

import pyads
import sys

AMS_NET_ID = '110.110.110.20.1.1'
AMS_PORT = pyads.PORT_TC2PLC1  # 801 for TwinCAT 2
TEST_VARIABLE = 'MAIN.Feeder1.FeederStatus.Weight'

print(f"Target AMS Net ID: {AMS_NET_ID}")
print(f"Target AMS Port:   {AMS_PORT}")
print(f"Test variable:     {TEST_VARIABLE}")
print()

# Step 1: Try to connect
print("[1] Opening ADS connection...")
try:
    plc = pyads.Connection(AMS_NET_ID, AMS_PORT)
    plc.open()
    print("    OK - connection opened")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
    print()
    print("Troubleshooting:")
    print("  - Is pyads installed? (pip install pyads)")
    print("  - Is the Pi on the same subnet as 110.110.110.20?")
    print("  - Has an ADS route been added on the TwinCAT side?")
    print("  - Is the AMS Net ID correct? Check TwinCAT System Manager.")
    sys.exit(1)

# Step 2: Check connection state
print("[2] Checking ADS state...")
try:
    state = plc.read_state()
    print(f"    OK - ADS state: {state}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
    print()
    print("Troubleshooting:")
    print("  - Connection opened but can't read state.")
    print("  - The AMS Net ID may be wrong.")
    print("  - An ADS route may be needed on the TwinCAT side.")
    plc.close()
    sys.exit(1)

# Step 3: Try to read a single variable
print(f"[3] Reading '{TEST_VARIABLE}'...")
try:
    value = plc.read_by_name(TEST_VARIABLE, pyads.PLCTYPE_REAL)
    print(f"    OK - value: {value}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
    print()
    print("Troubleshooting:")
    print("  - Connection works but variable read failed.")
    print("  - The variable name may have a typo or spaces.")
    print("  - Try a different variable name.")

# Step 4: Try reading a few more variables
print("[4] Reading additional variables...")
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
print("[5] Closing connection...")
plc.close()
print("    Done.")
