import piplates.DAQC2plate as DAQC2
import time

class Stepper_Motor:

    __REVOLUTIONS = 10 * 400.0  # number of steps per revolution
    __JOG_FREQ = 10 * 10 * 10 # 10 Hz

    def __init__(self, motor_addr=1, addr=0, torque_addr=0, channel=1, drive_fault_pin=0, e_stop_pin=1):
        self.motor_addr = motor_addr
        self.addr = addr
        self.torque_addr = torque_addr
        self.channel = channel
        self.ch_mult = 100
        self.freq = 10
        self.type = 3               # square wave
        self.level = 4              # 1:1
        self.set_square_wave()
        self.set_level(self.level)
        self.stop()
        self.drive_fault_pin = drive_fault_pin
        self.e_stop_pin = e_stop_pin

    def get_frequency(self):
        try:
            return DAQC2.getFREQ(0)
        except Exception:
            return 0

    def is_drive_fault_active(self):
        try:
            if DAQC2.getDINbit(self.addr, self.drive_fault_pin):
                return False
            else:
                return True
        except Exception:
            return False

    def is_e_stop_active(self):
        try:
            if DAQC2.getDINbit(self.addr, self.e_stop_pin):
                return False
            else:
                return True
        except Exception:
            return False

    def get_torque(self) -> float:
        try:
            Nm = abs(round(DAQC2.getADC(self.addr, self.torque_addr) * 0.05, 4))
            return Nm
        except:
            print("Error: Torque sensor not connected")
            return 0.0

    def set_square_wave(self):
        try:
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def set_level(self, level):
        try:
            self.level = level
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def start(self):
        try:
            DAQC2.fgON(self.motor_addr, self.channel)
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def jog(self):
        try:
            DAQC2.fgON(self.motor_addr, self.channel)
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
            DAQC2.fgFREQ(self.motor_addr, self.channel, self.__JOG_FREQ)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def update_freq(self, freq):
        try:
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
            DAQC2.fgFREQ(self.motor_addr, self.channel, freq)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def set_rpm(self, rpm_input):
        """
        Sets the target RPM immediately (without ramping).
        """
        # Calculate target frequency from RPM
        target_freq = round((rpm_input / 60.0) * self.__REVOLUTIONS, 2)
        # Bound frequency within limits
        if target_freq < 10:
            target_freq = 10
        elif target_freq > 10000:
            target_freq = 10000

        self.freq = target_freq
        self.update_freq(self.freq)
        return self.freq

    def get_rpm(self):
        freq = self.get_frequency()
        rpm = int((freq * 60.0)/1000)/10
        return rpm

    def ramp_to_rpm(self, rpm_input, ramp_time=None, steps=None):
        """
        Gradually ramps the motor's frequency from the current frequency to the target RPM.
        The number of steps is scaled based on the difference between the current
        frequency and the target frequency.
        """
        # Convert target RPM to frequency
        target_freq = round((rpm_input / 60.0) * self.__REVOLUTIONS, 2)
        if target_freq < 10:
            target_freq = 10
        elif target_freq > 10000:
            target_freq = 10000

        current_freq = self.freq if hasattr(self, "freq") else 10

        # Dynamically scale the number of steps if not provided.
        if steps is None:
            step_size = 5.0  # Hz per step
            steps = max(10, int(abs(target_freq - current_freq) / step_size))

        # Scale ramp_time if not provided (defaulting to 0.02 sec per step).
        if ramp_time is None:
            ramp_time = steps * 0.02

        delta = (target_freq - current_freq) / steps
        step_delay = ramp_time / steps

        for i in range(steps):
            new_freq = current_freq + delta * (i + 1)
            self.update_freq(new_freq)
            time.sleep(step_delay)

        # Ensure the final frequency is exactly set.
        self.freq = target_freq
        self.update_freq(self.freq)
        return self.freq
    
    def slow_stop(self, ramp_time=None, steps=None, final_freq=10):
        """
        Gradually decelerates the motor's frequency from the current value to a final frequency,
        then shuts the motor off.
        
        Args:
            ramp_time (float, optional): Total time (in seconds) for the deceleration.
            steps (int, optional): Number of incremental steps in the deceleration.
            final_freq (float): The target frequency at the end of deceleration.
        
        Returns:
            float: The final frequency (should be equal to final_freq) after deceleration.
        """
        current_freq = self.freq if hasattr(self, "freq") else 10

        # Dynamically calculate steps if not provided.
        if steps is None:
            step_size = 5.0  # Hz per step
            steps = max(10, int(abs(current_freq - final_freq) / step_size))

        # Set a default ramp_time if not provided.
        if ramp_time is None:
            ramp_time = steps * 0.02

        delta = (final_freq - current_freq) / steps
        step_delay = ramp_time / steps

        for i in range(steps):
            new_freq = current_freq + delta * (i + 1)
            self.update_freq(new_freq)
            time.sleep(step_delay)

        # Ensure the frequency is exactly the final frequency.
        self.freq = final_freq
        self.update_freq(self.freq)
        
        # Now fully turn off the motor.
        try:
            DAQC2.fgOFF(self.motor_addr, self.channel)
        except Exception as e:
            # Optionally log the error.
            # print("Error turning off the motor:", e)
            pass

        return self.freq

    def stop(self):
        """
        Stops the motor gradually using slow_stop.
        """
        self.slow_stop()

    def __destroy__(self):
        self.stop()