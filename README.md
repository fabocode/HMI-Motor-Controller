# HMI-Motor-Controller
 HMI Motor Controller

# Requirements
- ADC Enabled
- 1280x720 Window Resolution

# Note if you work in a virtual environment 
It's required to type the following command `export CFLAGS=-fcommon`.
This will enable to install the RPi.GPIO module without problems.

# Wiring Connection with Stepper Driver and Raspberry Pi 
| Stepper driver | Raspberry Pi Plates board |
| -------------- | ------------------------- |
| `DIR -`        |  `GND`                    |
| `DIR +`        |  `DOUT0`                  |
| `PUL -`        |  `GND`                    |
| `PUL +`        |  `PWM0`                   |
