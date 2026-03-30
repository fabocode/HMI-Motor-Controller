# Sartorius Cubis II Scale - Integration Guide

## Overview

The HMI application reads weight data from a **Sartorius Cubis II MCA5201S-2S00-0** precision scale connected to the Raspberry Pi via USB. The weight is displayed in real-time on the HMI touchscreen and recorded alongside motor data (RPM, torque, etc.) in the Excel data export.

### Scale Specifications

| Specification | Value |
|---------------|-------|
| Model | Sartorius Cubis II MCA5201S-2S00-0 |
| Capacity | 5200 g |
| Readability | 0.1 g |
| Interface | USB-B (Virtual COM port) |
| Protocol | SBI (Sartorius Balance Interface) |

---

## Hardware Setup

### USB Connection

1. Connect the scale to the Raspberry Pi using a USB-B cable to any available USB port
2. The scale appears as a virtual serial port at `/dev/ttyACM0`
3. No additional drivers are required — the Linux `cdc_acm` kernel driver handles it automatically

### Verifying the Connection

After plugging in the USB cable, verify the scale is detected:

```bash
# Check that the device appears
ls /dev/ttyACM*

# Verify it's the Sartorius scale
python -c "import serial.tools.list_ports; [print(f'{p.device} - {p.description}') for p in serial.tools.list_ports.comports()]"
# Expected: /dev/ttyACM0 - Cubis MCA5201S-2S00-0 - CDC
```

### User Permissions

The Pi user must be in the `dialout` group to access the serial port:

```bash
sudo usermod -a -G dialout $USER
```

Log out and back in for the change to take effect.

---

## Communication Protocol

The scale uses the **SBI (Sartorius Balance Interface)** protocol over a USB virtual COM port. SBI is an ASCII-based command/response protocol used across Sartorius balance product lines.

### Serial Parameters

| Parameter | Value |
|-----------|-------|
| Baud rate | **19200** |
| Data bits | **8** |
| Parity | **None** |
| Stop bits | **1** |
| Timeout | 5 seconds |

> **Note:** These parameters were verified on 2026-03-28 with the MCA5201S-2S00-0 unit connected to this system. The Sartorius factory defaults can vary between units (some ship at 9600 baud with 7-O-1). If replacing the scale or after a factory reset, the parameters may need to be re-verified using `tests/test_scale_connection.py`.

### Command Used

| Command | Bytes | Description |
|---------|-------|-------------|
| ESC P | `\x1bP\r\n` | Request stable weight reading |

The application sends `ESC P` (print/stable read). This command waits until the scale reading is stable before responding, which typically takes 1-3 seconds.

> **Note:** `ESC S` (immediate/unstable read) was tested and is **not supported** on this unit. Only `ESC P` produces a response.

### Response Format

The scale responds with a **22-byte fixed-width ASCII string**:

```
G     +    256.1 g  \r\n
│     │    │     │
│     │    │     └── Unit (present = stable, absent = unstable)
│     │    └──────── Weight value (right-justified, space-padded)
│     └───────────── Sign (+ or -)
└─────────────────── Status (G = Gross, N = Net)
```

**Stable vs Unstable responses:**

The scale omits the unit when the reading is unstable (weight is still settling). Once the reading stabilizes, the unit (`g`) appears in the response.

| Raw Response | Weight | Stable? | Meaning |
|-------------|--------|---------|---------|
| `G            0.0 g  \r\n` | 0.0 | Yes | Empty scale (no sign for zero) |
| `G     +    256.1 g  \r\n` | 256.1 | Yes | Stable reading with object |
| `G     +    381.6    \r\n` | 381.6 | No | Weight is changing/settling |
| `G     +    619.5 g  \r\n` | 619.5 | Yes | Stable after adding weight |

**Status characters:**
- `G` = Gross weight (no tare applied)
- `N` = Net weight (tare applied)

**Stability behavior with ESC P:**
- ESC P requests a stable reading, but when weight is actively changing, it still returns an unstable response (without unit) rather than blocking indefinitely
- During transitions (adding/removing weight), expect 2-5 unstable readings before the value settles
- The application uses both stable and unstable readings for display, since the numeric value is still valid

### Other SBI Commands (Reference)

These commands are available in the SBI protocol but are not currently used by the application:

| Command | Bytes | Description |
|---------|-------|-------------|
| ESC T | `\x1bT\r\n` | Tare the scale |
| ESC Z | `\x1bZ\r\n` | Zero the scale |
| ESC S | `\x1bS\r\n` | Immediate read (not supported on this unit) |

---

## Scale Settings on the Cubis II Touchscreen

If the scale stops communicating (e.g., after a factory reset), verify these settings on the scale's built-in touchscreen:

1. Navigate to **Menu** > **Communication** > **USB**
2. Verify:
   - **Protocol**: SBI
   - **Baud rate**: 19200
   - **Data bits**: 8
   - **Parity**: None
   - **Stop bits**: 1
   - **Handshake**: None

---

## How It Works in the Application

### Architecture

```
┌──────────────┐      USB Serial       ┌──────────────────┐
│   Sartorius  │  ──────────────────>   │   Raspberry Pi   │
│   Cubis II   │  /dev/ttyACM0         │                  │
│   Scale      │  19200 baud, 8-N-1    │  Scale class     │
└──────────────┘                        │  (background     │
                                        │   thread polls   │
                                        │   every ~3-5s)   │
                                        │       │          │
                                        │       v          │
                                        │  Cached weight   │
                                        │       │          │
                                        │       v          │
                                        │  HMI UI + Excel  │
                                        └──────────────────┘
```

### Data Flow

1. A **background daemon thread** in the `Scale` class continuously sends `ESC P` and reads the response
2. Each response is parsed to extract the numeric weight value and unit
3. The parsed weight is cached as a float — the UI thread reads this cached value every 1 second via `get_weight()`
4. The weight is:
   - **Displayed** on the HMI touchscreen in the right panel
   - **Recorded** every second while the motor is running, into the data dictionary
   - **Exported** as a column in the Excel file when the motor is stopped

### Error Handling

- If the scale is **disconnected**, the application continues running normally — weight displays as `0.0`
- If the scale is **reconnected**, the background thread automatically re-establishes communication within a few seconds
- All serial communication errors are caught silently to prevent UI crashes (consistent with the motor sensor pattern)

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Scale not detected (`/dev/ttyACM0` missing) | USB cable disconnected or faulty | Check USB cable, try a different USB port |
| Permission denied on `/dev/ttyACM0` | User not in `dialout` group | Run `sudo usermod -a -G dialout $USER`, then log out/in |
| No response from scale | Protocol settings mismatch | Check scale touchscreen: Menu > Communication > USB > Protocol = SBI |
| Weight always shows 0.0 | Scale not connected or communication error | Run `python tests/test_scale_connection.py` to diagnose |
| Garbled response data | Baud rate or parity mismatch | Verify serial parameters match between scale settings and application config |

### Running the Diagnostic Test

A standalone test script is included to verify scale communication independently from the HMI application:

```bash
cd ~/HMI-Motor-Controller
python tests/test_scale_connection.py
```

This script will confirm the serial port, parameters, and response format.
