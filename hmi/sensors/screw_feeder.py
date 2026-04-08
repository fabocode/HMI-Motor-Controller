import requests
import threading
import time
import xml.etree.ElementTree as ET


class ScrewFeeder:
    """Beckhoff TwinCAT 2 screw feeder read-only interface over OPC XML-DA.

    Communicates with the PLC using the OPC XML-DA SOAP web service exposed
    by TwinCAT at /UPnPDevice/TcPlcDataServiceDa.dll. A background daemon
    thread polls all configured variables every second and caches the latest
    readings. Call the get_*() methods from the UI thread — they return
    cached values instantly without blocking.

    Network setup:
        Pi:     110.110.110.11  (fixed IP)
        Feeder: 110.110.110.20  (TwinCAT 2)
        Subnet: 255.255.255.0
    """

    OPC_URL = 'http://110.110.110.20/UPnPDevice/TcPlcDataServiceDa.dll'

    # PLC variables to read (OPC XML-DA item names)
    # Derived from /TcWebVisu/feeder1.xml variable definitions
    VARIABLES = {
        'total_mass':     'PLC1.MAIN.Feeder1.FeederStatus.TotalMass',
        'weight':         'PLC1.MAIN.Feeder1.FeederStatus.Weight',
        'mass_flow':      'PLC1.MAIN.Feeder1.FeederStatus.MassFlow',
        'motor_velocity': 'PLC1.MAIN.Feeder1.FeedingModule.ServoDrive.MotorVelocity',
        'motor_current':  'PLC1.MAIN.Feeder1.FeedingModule.ServoDrive.MotorCurrent',
        'state':          'PLC1.MAIN.Feeder1.HmiLogic.CurrentStateStr',
        'mode':           'PLC1.MAIN.Feeder1.HmiLogic.CurrentModeStr',
        'gravimetric':    'PLC1.MAIN.Feeder1.FeedingModule.Gravimetric',
        'hmi_state_cmd':  'PLC1.MAIN.Feeder1.HmiLogic.HMIStateCmdStr',
        'hmi_mode':       'PLC1.MAIN.Feeder1.HmiLogic.HMIModeStr',
        'screw_velocity': 'PLC1.MAIN.Feeder1.FeederStatus.ScrewVelocity',
        'feed_factor':    'PLC1.MAIN.Feeder1.FeederStatus.FeedFactorBarrelExit',
        'massflow_rsd':   'PLC1.MAIN.Feeder1.FeederStatus.MassflowRSD',
    }

    _SOAP_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:opc="http://opcfoundation.org/webservices/XMLDA/1.0/">
  <soap:Body>
    <opc:Read>
      <opc:Options ReturnItemTime="true" ReturnItemName="true"/>
      <opc:ItemList>{items}</opc:ItemList>
    </opc:Read>
  </soap:Body>
</soap:Envelope>"""

    _SOAP_ITEM = '<opc:Items ItemName="{name}"/>'

    _HEADERS = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://opcfoundation.org/webservices/XMLDA/1.0/Read',
    }

    _NS = {'ns1': 'http://opcfoundation.org/webservices/XMLDA/1.0/'}

    _POLL_INTERVAL = 1.0
    _REQUEST_TIMEOUT = 5.0

    def __init__(self, opc_url=None):
        if opc_url:
            self.OPC_URL = opc_url

        self._connected = False

        # Cached readings — defaults
        self._data = {
            'total_mass': 0.0,
            'weight': 0.0,
            'mass_flow': 0.0,
            'motor_velocity': 0.0,
            'motor_current': 0,
            'state': '',
            'mode': '',
            'gravimetric': '',
            'hmi_state_cmd': '',
            'hmi_mode': '',
            'screw_velocity': 0.0,
            'feed_factor': 0.0,
            'massflow_rsd': 0.0,
        }

        # Build the SOAP request body once (all items in one request)
        items_xml = ''.join(
            self._SOAP_ITEM.format(name=name)
            for name in self.VARIABLES.values()
        )
        self._soap_body = self._SOAP_TEMPLATE.format(items=items_xml)

        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_worker, daemon=True)
        self._poll_thread.start()

    def _parse_response(self, xml_text):
        """Parse OPC XML-DA Read response and return dict of item_name -> value."""
        results = {}
        root = ET.fromstring(xml_text)
        for item in root.findall('.//ns1:Items', self._NS):
            name = item.get('ItemName', '')
            value_el = item.find('ns1:Value', self._NS)
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

    def _poll_worker(self):
        """Background thread: reads all PLC variables via HTTP, caches results."""
        while self._running:
            try:
                r = requests.post(
                    self.OPC_URL,
                    data=self._soap_body,
                    headers=self._HEADERS,
                    timeout=self._REQUEST_TIMEOUT,
                )
                if r.status_code == 200:
                    results = self._parse_response(r.text)
                    for key, item_name in self.VARIABLES.items():
                        if item_name in results:
                            self._data[key] = results[item_name]
                    self._connected = True
                else:
                    self._connected = False
            except Exception:
                self._connected = False

            time.sleep(self._POLL_INTERVAL)

    # --- Public getters (safe to call from UI thread) ---

    def get_total_mass(self):
        """Return cumulative mass fed (float)."""
        return self._data['total_mass']

    def get_weight(self):
        """Return current weight on feeder (float)."""
        return self._data['weight']

    def get_mass_flow(self):
        """Return current mass flow rate (float)."""
        return self._data['mass_flow']

    def get_motor_velocity(self):
        """Return feeder motor velocity (float)."""
        return self._data['motor_velocity']

    def get_motor_current(self):
        """Return feeder motor current (int)."""
        return self._data['motor_current']

    def get_state(self):
        """Return current feeder state string (e.g., 'Running')."""
        return self._data['state']

    def get_mode(self):
        """Return current feeder mode string (e.g., 'Feed')."""
        return self._data['mode']

    def get_gravimetric(self):
        """Return gravimetric mode status."""
        return self._data['gravimetric']

    def get_hmi_state_cmd(self):
        """Return HMI state command string."""
        return self._data['hmi_state_cmd']

    def get_hmi_mode(self):
        """Return HMI mode string."""
        return self._data['hmi_mode']

    def get_screw_velocity(self):
        """Return screw velocity (float)."""
        return self._data['screw_velocity']

    def get_feed_factor(self):
        """Return feed factor at barrel exit (float)."""
        return self._data['feed_factor']

    def get_massflow_rsd(self):
        """Return mass flow RSD (float)."""
        return self._data['massflow_rsd']

    def is_connected(self):
        """Return True if OPC XML-DA endpoint is responding."""
        return self._connected

    def close(self):
        """Stop polling thread."""
        self._running = False
