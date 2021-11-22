import piplates.DAQC2plate as DAQC2
import time
import sys

if __name__ == '__main__':
    try:
        while True:
            adc_reading = DAQC2.getADC(0,0)
            print(f"Torque sensor output: {adc_reading}")
            time.sleep(.5)  # read every half second

    except KeyboardInterrupt:
        print("\n\nProgram terminated by user. Exiting now...\n\n")
        sys.exit(0)
