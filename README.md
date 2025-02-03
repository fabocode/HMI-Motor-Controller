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

# How to enable Touch Screen Input or read mouse inputs

You need to add this text into `~/kivy/config.ini` file

Source of information:
- [no mouse movement or touch in kivy app run from cli in raspberry](https://stackoverflow.com/questions/65631219/no-mouse-movement-or-touch-in-kivy-app-run-from-cli-in-raspberry)
- [Using Kivy with the official Raspberry Pi Touch Display
](https://github.com/mrichardson23/rpi-kivy-screen)

```console
[modules]
touchring = show_cursor=true
[input]
mouse = mouse
#%(name)s = probesysfs,provider=hidinput
mtdev_%(name)s = probesysfs,provider=mtdev
hid_%(name)s = probesysfs,provider=hidinput
```

# Drivers
Pi Plates board needs some drivers to be installed to work properly.

- https://pi-plates.com/getting_started/
- https://pi-plates.com/daqc2-users-guide/

## Motor Driver Documentation Related
- [Motor Driver Documentation](https://drive.google.com/drive/folders/1CCYSKMNFkdTGh5bgDVLDOATVJFm7dB3A?usp=sharing)