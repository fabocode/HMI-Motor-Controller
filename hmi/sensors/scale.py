import serial
import serial.tools.list_ports
import threading
import time
import re


class Scale:
    """Sartorius Cubis II MCA5201S-2S00-0 SBI interface over USB serial.

    Communicates using the SBI (Sartorius Balance Interface) protocol.
    A background daemon thread polls the scale continuously and caches the
    latest weight reading. Call get_weight() from the UI thread — it returns
    the cached value instantly without blocking.

    Verified config (2026-03-30):
        Port: /dev/ttyACM0  |  19200 baud, 8-N-1  |  ESC P command
    """

    # SBI command — ESC P (stable read). ESC S is not supported on this unit.
    _CMD_READ = b'\x1bP\r\n'

    # Serial parameters (verified on MCA5201S-2S00-0)
    _BAUD = 19200
    _BYTESIZE = serial.EIGHTBITS
    _PARITY = serial.PARITY_NONE
    _STOPBITS = serial.STOPBITS_ONE
    _TIMEOUT = 5.0  # ESC P blocks until stable, typically 1-3s

    # Regex to extract numeric value from SBI response.
    # Handles both stable ("G     +    256.1 g  ") and unstable ("G     +    381.6    ")
    _WEIGHT_RE = re.compile(r'([+-]?\s*[\d.]+)')

    _POLL_INTERVAL = 0.5        # seconds between poll attempts
    _RECONNECT_INTERVAL = 2.0   # seconds between reconnect attempts

    def __init__(self, port=None):
        self._port_path = port
        self._serial = None
        self._weight = 0.0
        self._unit = 'g'
        self._stable = False
        self._connected = False
        self._lock = threading.Lock()

        self._connect(port)

        # Background polling thread (mirrors stepper_motor._ramp_thread pattern)
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_worker, daemon=True)
        self._poll_thread.start()

    def _find_port(self):
        """Auto-detect Sartorius scale USB port."""
        try:
            ports = serial.tools.list_ports.comports()
            for p in ports:
                if 'Cubis' in (p.description or '') or 'Sartorius' in (p.description or ''):
                    return p.device
                if 'ttyACM' in p.device:
                    return p.device
        except Exception:
            pass
        return None

    def _connect(self, port=None):
        """Open serial connection to the scale."""
        try:
            if port is None:
                port = self._find_port()
            if port is None:
                self._connected = False
                return
            self._serial = serial.Serial(
                port=port,
                baudrate=self._BAUD,
                bytesize=self._BYTESIZE,
                parity=self._PARITY,
                stopbits=self._STOPBITS,
                timeout=self._TIMEOUT
            )
            self._connected = True
            self._port_path = port
        except Exception:
            self._connected = False

    def _parse_response(self, raw):
        """Parse SBI response bytes into weight float.

        Stable response:   b'G     +    256.1 g  \\r\\n'  -> 256.1
        Unstable response: b'G     +    381.6    \\r\\n'  -> 381.6
        """
        try:
            text = raw.decode('ascii', errors='ignore').strip()
            # Check for error responses
            if text.startswith('E') or not text:
                return None, False

            # Detect stability: unit present means stable
            stable = bool(re.search(r'[a-zA-Z]\s*$', text))

            # Extract numeric value (skip the status character at position 0)
            match = self._WEIGHT_RE.search(text[1:])
            if match:
                value_str = match.group(1).replace(' ', '')
                return float(value_str), stable
        except Exception:
            pass
        return None, False

    def _poll_worker(self):
        """Background thread: reads weight continuously, caches result."""
        while self._running:
            if not self._connected:
                self._connect(self._port_path)
                time.sleep(self._RECONNECT_INTERVAL)
                continue
            try:
                with self._lock:
                    self._serial.reset_input_buffer()
                    self._serial.write(self._CMD_READ)
                    response = self._serial.readline()
                value, stable = self._parse_response(response)
                if value is not None:
                    self._weight = value
                    self._stable = stable
            except Exception:
                self._connected = False
                try:
                    if self._serial and self._serial.is_open:
                        self._serial.close()
                except Exception:
                    pass
            time.sleep(self._POLL_INTERVAL)

    def get_weight(self):
        """Return latest weight reading in grams. Safe to call from UI thread."""
        try:
            return self._weight
        except Exception:
            return 0.0

    def get_unit(self):
        """Return unit string from last reading."""
        try:
            return self._unit
        except Exception:
            return 'g'

    def is_stable(self):
        """Return True if the last reading was a stable (settled) value."""
        return self._stable

    def is_connected(self):
        """Return True if serial connection to scale is active."""
        return self._connected

    def close(self):
        """Stop polling and close serial connection."""
        self._running = False
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()
        except Exception:
            pass
