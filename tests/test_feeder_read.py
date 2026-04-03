#!/usr/bin/env python3
"""Test reading all 7 screw feeder variables via OPC XML-DA at 1-second intervals.

Run on the Pi:
    python test_feeder_read.py

Press Ctrl+C to stop.
"""

import requests
import xml.etree.ElementTree as ET
import time
import sys

OPC_URL = 'http://110.110.110.20/UPnPDevice/TcPlcDataServiceDa.dll'

VARIABLES = {
    'Total Mass':     'PLC1.MAIN.Feeder1.FeederStatus.TotalMass',
    'Weight':         'PLC1.MAIN.Feeder1.FeederStatus.Weight',
    'Mass Flow':      'PLC1.MAIN.Feeder1.FeederStatus.MassFlow',
    'Motor Velocity': 'PLC1.MAIN.Feeder1.FeedingModule.ServoDrive.MotorVelocity',
    'Motor Current':  'PLC1.MAIN.Feeder1.FeedingModule.ServoDrive.MotorCurrent',
    'State':          'PLC1.MAIN.Feeder1.HmiLogic.CurrentStateStr',
    'Mode':           'PLC1.MAIN.Feeder1.HmiLogic.CurrentModeStr',
}

NS = {'ns1': 'http://opcfoundation.org/webservices/XMLDA/1.0/'}

HEADERS = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://opcfoundation.org/webservices/XMLDA/1.0/Read',
}

# Build SOAP request with all items
items_xml = ''.join(
    f'<opc:Items ItemName="{name}"/>'
    for name in VARIABLES.values()
)

SOAP_BODY = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:opc="http://opcfoundation.org/webservices/XMLDA/1.0/">
  <soap:Body>
    <opc:Read>
      <opc:Options ReturnItemTime="true" ReturnItemName="true"/>
      <opc:ItemList>{items_xml}</opc:ItemList>
    </opc:Read>
  </soap:Body>
</soap:Envelope>"""

POLL_INTERVAL = 1.0  # seconds


def parse_response(xml_text):
    results = {}
    root = ET.fromstring(xml_text)
    for item in root.findall('.//ns1:Items', NS):
        name = item.get('ItemName', '')
        value_el = item.find('ns1:Value', NS)
        if value_el is not None and value_el.text is not None:
            xsi_type = value_el.get(
                '{http://www.w3.org/2001/XMLSchema-instance}type', ''
            )
            if 'float' in xsi_type or 'double' in xsi_type:
                results[name] = float(value_el.text)
            elif 'int' in xsi_type or 'short' in xsi_type:
                results[name] = int(value_el.text)
            else:
                results[name] = value_el.text
    return results


print(f"Reading {len(VARIABLES)} variables every {POLL_INTERVAL}s from {OPC_URL}")
print("Press Ctrl+C to stop.\n")

# Print header
print(f"{'#':>4}  {'Total Mass':>12}  {'Weight':>10}  {'Mass Flow':>10}  "
      f"{'Motor Vel':>10}  {'Motor Cur':>10}  {'State':<15}  {'Mode':<15}  {'ms':>5}")
print("-" * 105)

count = 0
try:
    while True:
        count += 1
        t0 = time.time()
        try:
            r = requests.post(OPC_URL, data=SOAP_BODY, headers=HEADERS, timeout=5)
            elapsed_ms = int((time.time() - t0) * 1000)

            if r.status_code == 200:
                results = parse_response(r.text)
                vals = {}
                for label, item_name in VARIABLES.items():
                    vals[label] = results.get(item_name, '?')

                print(f"{count:4d}  "
                      f"{vals['Total Mass']:>12.2f}  "
                      f"{vals['Weight']:>10.2f}  "
                      f"{vals['Mass Flow']:>10.2f}  "
                      f"{vals['Motor Velocity']:>10.2f}  "
                      f"{vals['Motor Current']:>10}  "
                      f"{str(vals['State']):<15}  "
                      f"{str(vals['Mode']):<15}  "
                      f"{elapsed_ms:>5}")
            else:
                print(f"{count:4d}  HTTP {r.status_code}")
        except Exception as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            print(f"{count:4d}  ERROR: {type(e).__name__}: {e}  ({elapsed_ms}ms)")

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print(f"\nStopped after {count} readings.")
