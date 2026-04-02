#!/usr/bin/env python3
"""Test reading PLC data via the TwinCAT OPC DA HTTP web service.

The Java WebVisu applet uses this endpoint:
    http://110.110.110.20/UPnPDevice/TcPlcDataServiceDa.dll

This is a SOAP/XML web service that can read PLC variables without
needing ADS routing or AMS Net IDs.

Run on the Pi:
    python test_opc_http.py
"""

import requests
import sys

BASE_URL = 'http://110.110.110.20'
OPC_URL = f'{BASE_URL}/UPnPDevice/TcPlcDataServiceDa.dll'

# Step 1: Check if the base URL is reachable
print("[1] Checking HTTP connectivity...")
try:
    r = requests.get(BASE_URL, timeout=5)
    print(f"    OK - HTTP {r.status_code}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")

# Step 2: Check the OPC DA endpoint
print(f"[2] Checking OPC DA endpoint...")
try:
    r = requests.get(OPC_URL, timeout=5)
    print(f"    HTTP {r.status_code}")
    print(f"    Content-Type: {r.headers.get('Content-Type', 'unknown')}")
    print(f"    Body (first 500 chars): {r.text[:500]}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")

# Step 3: Try a SOAP request to read a variable
# TcPlcDataServiceDa uses SOAP — try the standard OPC XML-DA Read request
print("[3] Trying OPC XML-DA Read request...")

SOAP_READ = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:opc="http://opcfoundation.org/webservices/XMLDA/1.0/">
  <soap:Body>
    <opc:Read>
      <opc:Options ReturnItemTime="true" ReturnItemName="true"/>
      <opc:ItemList>
        <opc:Items ItemName="PLC1.MAIN.Feeder1.FeederStatus.Weight"/>
      </opc:ItemList>
    </opc:Read>
  </soap:Body>
</soap:Envelope>"""

headers = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://opcfoundation.org/webservices/XMLDA/1.0/Read',
}

try:
    r = requests.post(OPC_URL, data=SOAP_READ, headers=headers, timeout=10)
    print(f"    HTTP {r.status_code}")
    print(f"    Response:\n{r.text[:1000]}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")

# Step 4: Try alternate variable name formats
print("[4] Trying alternate variable name formats...")

alt_names = [
    'MAIN.Feeder1.FeederStatus.Weight',
    'PLC1.MAIN.Feeder1.FeederStatus.Weight',
    'PLC1.Feeder1.FeederStatus.Weight',
]

for var_name in alt_names:
    soap = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:opc="http://opcfoundation.org/webservices/XMLDA/1.0/">
  <soap:Body>
    <opc:Read>
      <opc:Options ReturnItemTime="true" ReturnItemName="true"/>
      <opc:ItemList>
        <opc:Items ItemName="{var_name}"/>
      </opc:ItemList>
    </opc:Read>
  </soap:Body>
</soap:Envelope>"""
    try:
        r = requests.post(OPC_URL, data=soap, headers=headers, timeout=10)
        print(f"    {var_name}: HTTP {r.status_code}")
        # Check if we got a value back
        if 'Value' in r.text:
            print(f"    >>> GOT DATA: {r.text[:500]}")
        elif r.status_code == 200:
            print(f"    Response: {r.text[:300]}")
    except Exception as e:
        print(f"    {var_name}: FAILED - {type(e).__name__}: {e}")

# Step 5: Try GetStatus to see if the service is alive
print("[5] Trying OPC XML-DA GetStatus...")
SOAP_STATUS = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:opc="http://opcfoundation.org/webservices/XMLDA/1.0/">
  <soap:Body>
    <opc:GetStatus/>
  </soap:Body>
</soap:Envelope>"""

headers_status = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://opcfoundation.org/webservices/XMLDA/1.0/GetStatus',
}

try:
    r = requests.post(OPC_URL, data=SOAP_STATUS, headers=headers_status, timeout=10)
    print(f"    HTTP {r.status_code}")
    print(f"    Response:\n{r.text[:1000]}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")

# Step 6: Try browsing available items
print("[6] Trying OPC XML-DA Browse...")
SOAP_BROWSE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:opc="http://opcfoundation.org/webservices/XMLDA/1.0/">
  <soap:Body>
    <opc:Browse/>
  </soap:Body>
</soap:Envelope>"""

headers_browse = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://opcfoundation.org/webservices/XMLDA/1.0/Browse',
}

try:
    r = requests.post(OPC_URL, data=SOAP_BROWSE, headers=headers_browse, timeout=10)
    print(f"    HTTP {r.status_code}")
    print(f"    Response:\n{r.text[:2000]}")
except Exception as e:
    print(f"    FAILED - {type(e).__name__}: {e}")
