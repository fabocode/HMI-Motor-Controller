import pyads
import threading
import time


class ScrewFeeder:
    """Beckhoff TwinCAT 2 screw feeder read-only interface over ADS/TCP.

    Communicates with the PLC using the pyads library. A background daemon
    thread polls all configured variables every second and caches the latest
    readings. Call the get_*() methods from the UI thread — they return
    cached values instantly without blocking.

    Network setup:
        Pi:     110.110.110.11  (fixed IP)
        Feeder: 110.110.110.20  (TwinCAT 2)
        Subnet: 255.255.255.0
    """

    AMS_NET_ID = '110.110.110.20.1.1'
    AMS_PORT = pyads.PORT_TC2PLC1  # Port 801 for TwinCAT 2

    # PLC variables to read — (symbol_name, plc_type)
    # Derived from /TcWebVisu/feeder1.xml variable definitions
    VARIABLES = {
        'total_mass':     ('MAIN.Feeder1.FeederStatus.TotalMass', pyads.PLCTYPE_REAL),
        'weight':         ('MAIN.Feeder1.FeederStatus.Weight', pyads.PLCTYPE_REAL),
        'mass_flow':      ('MAIN.Feeder1.FeederStatus.MassFlow', pyads.PLCTYPE_REAL),
        'motor_velocity': ('MAIN.Feeder1.FeedingModule.ServoDrive.MotorVelocity', pyads.PLCTYPE_REAL),
        'motor_current':  ('MAIN.Feeder1.FeedingModule.ServoDrive.MotorCurrent', pyads.PLCTYPE_INT),
        'state':          ('MAIN.Feeder1.HmiLogic.CurrentStateStr', pyads.PLCTYPE_STRING),
        'mode':           ('MAIN.Feeder1.HmiLogic.CurrentModeStr', pyads.PLCTYPE_STRING),
    }

    _POLL_INTERVAL = 1.0        # seconds between polls
    _RECONNECT_INTERVAL = 5.0   # seconds between reconnect attempts

    def __init__(self, ams_net_id=None):
        if ams_net_id:
            self.AMS_NET_ID = ams_net_id

        self._plc = None
        self._connected = False
        self._lock = threading.Lock()

        # Cached readings — defaults
        self._data = {
            'total_mass': 0.0,
            'weight': 0.0,
            'mass_flow': 0.0,
            'motor_velocity': 0.0,
            'motor_current': 0,
            'state': '',
            'mode': '',
        }

        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_worker, daemon=True)
        self._poll_thread.start()

    def _connect(self):
        """Open ADS connection to the TwinCAT 2 PLC."""
        try:
            self._plc = pyads.Connection(self.AMS_NET_ID, self.AMS_PORT)
            self._plc.open()
            self._connected = True
        except Exception:
            self._connected = False

    def _poll_worker(self):
        """Background thread: reads all PLC variables, caches results."""
        while self._running:
            if not self._connected:
                self._connect()
                if not self._connected:
                    time.sleep(self._RECONNECT_INTERVAL)
                    continue

            try:
                # Read all variables in one batch
                symbol_names = [v[0] for v in self.VARIABLES.values()]
                plc_types = {v[0]: v[1] for v in self.VARIABLES.values()}
                results = self._plc.read_list_by_name(symbol_names)

                with self._lock:
                    for key, (symbol, _) in self.VARIABLES.items():
                        self._data[key] = results.get(symbol, self._data[key])
            except Exception:
                self._connected = False
                try:
                    if self._plc:
                        self._plc.close()
                except Exception:
                    pass

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

    def is_connected(self):
        """Return True if ADS connection to PLC is active."""
        return self._connected

    def close(self):
        """Stop polling and close ADS connection."""
        self._running = False
        try:
            if self._plc:
                self._plc.close()
        except Exception:
            pass
