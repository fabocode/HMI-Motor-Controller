import piplates.DAQC2plate as DAQC2
import time
import sys

if __name__ == '__main__':
    try:

        # Initialize the DAQC2
        # DAQC2.ADC_init()
        # # Set the ADC to read from the internal temperature sensor
        # DAQC2.ADC_set_temp_sensor(1)
        # # Set the ADC to read from the internal temperature sensor
        # DAQC2.ADC_set_temp_sensor(2)
        # Set the ADC to read from the internal temperature sensor
        adc_reading = DAQC2.getADC(0,0)
        print(f"Torque sensor output: {adc_reading}")
        time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nProgram terminated by user. Exiting now...\n\n")
        sys.exit(0)
        