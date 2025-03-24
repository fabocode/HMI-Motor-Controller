import piplates.DAQC2plate as DAQC2
import time
import threading

class Stepper_Motor:

    __REVOLUTIONS = 10 * 400.0  # number of steps per revolution
    __JOG_FREQ = 10 * 10 * 10
    _STOP_FREQ = 10             # frequency considered as "stopped"

    def __init__(self, motor_addr=1, addr=0, torque_addr=0, channel=1, drive_fault_pin=0, e_stop_pin=1, clockwise_pin=0):
        self.motor_addr = motor_addr
        self.addr = addr
        self.torque_addr = torque_addr
        self.channel = channel
        self.ch_mult = 100
        self.freq = 10            # current frequency
        self._target_freq = self.freq  # target frequency that the ramp thread will chase
        self.type = 3             # square wave
        self.level = 4            # 1:1
        self.drive_fault_pin = drive_fault_pin
        self.e_stop_pin = e_stop_pin
        self.clockwise_pin = clockwise_pin

        # Feedback flags.
        self.is_at_target = True          # True when self.freq == self._target_freq
        self.motor_stopped = True         # True if motor has decelerated and been turned off

        # Parameters for background ramping
        self._ramp_delay = 0.02   # seconds per update step
        # _ramp_rate will be set dynamically each time a new target is given.
        self._ramp_rate = 0

        self.set_square_wave()
        self.set_level(self.level)
        self.stop()               # ensure motor is off at startup
        self.clear_clockwise()

        # Start a background thread that continuously updates the frequency toward _target_freq.
        self.running = True
        self._ramp_thread = threading.Thread(target=self._ramp_worker, daemon=True)
        self._ramp_thread.start()

    def _ramp_worker(self):
        """Background thread that adjusts the frequency toward the target and updates flags."""
        while self.running:
            if self.freq < self._target_freq:
                self.freq = min(self.freq + self._ramp_rate, self._target_freq)
                self.update_freq(self.freq)
            elif self.freq > self._target_freq:
                self.freq = max(self.freq - self._ramp_rate, self._target_freq)
                self.update_freq(self.freq)
            # Update the flag: if the frequency is near the target, consider the ramp complete.
            if abs(self.freq - self._target_freq) < 0.1:
                self.is_at_target = True
            else:
                self.is_at_target = False
            time.sleep(self._ramp_delay)

    def set_clockwise(self):
        try:
            DAQC2.setDOUTbit(self.addr, self.clockwise_pin)
        except Exception:
            pass

    def clear_clockwise(self):
        try:
            DAQC2.clrDOUTbit(self.addr, self.clockwise_pin)
        except Exception:
            pass

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
        Immediately sets a new target RPM (via target frequency). The background thread
        will handle the gradual ramping.
        """
        target_freq = round((rpm_input / 60.0) * self.__REVOLUTIONS, 2)
        # Clamp frequency to limits.
        if target_freq < 10:
            target_freq = 10
        elif target_freq > 10000:
            target_freq = 10000
        self._target_freq = target_freq
        return self._target_freq

    def get_rpm(self):
        freq = self.get_frequency()
        rpm = int((freq * 60.0)/1000)/10
        return rpm

    def ramp_to_rpm(self, rpm_input, ramp_time=1.0):
        """
        Non-blocking ramp: sets target RPM and computes a ramp rate so the transition
        takes approximately ramp_time seconds.
        """
        target_freq = round((rpm_input / 60.0) * self.__REVOLUTIONS, 2)
        target_freq = max(10, min(target_freq, 10000))
        self._target_freq = target_freq
        self.motor_stopped = False
        steps = ramp_time / self._ramp_delay
        self._ramp_rate = abs(target_freq - self.freq) / steps
        return self._target_freq
    
    def slow_stop(self, ramp_time=1.0, final_freq=_STOP_FREQ):
        """
        Initiates a slow stop: adjusts the ramp rate so deceleration takes ramp_time seconds,
        then once the frequency reaches final_freq, turns the motor off and sets motor_stopped flag.
        """
        self._target_freq = final_freq
        steps = ramp_time / self._ramp_delay
        self._ramp_rate = abs(self.freq - final_freq) / steps

        def wait_and_turn_off():
            while abs(self.freq - final_freq) > 0.1:
                time.sleep(0.01)
            try:
                DAQC2.fgOFF(self.motor_addr, self.channel)
            except Exception:
                pass
            self.motor_stopped = True

        threading.Thread(target=wait_and_turn_off, daemon=True).start()

    def stop(self, ramp_time=1.0):
        """
        Initiates a non-blocking, gradual stop with a fixed ramp time.
        """
        self.slow_stop(ramp_time=ramp_time, final_freq=self._STOP_FREQ)

    def __destroy__(self):
        self.running = False
        self.stop()
