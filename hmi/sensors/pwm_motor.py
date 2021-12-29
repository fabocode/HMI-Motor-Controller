# import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time # Import the time library
import pigpio # Import the GPIO library

class Motor:
    def __init__(self, motor_pin=18):
        '''
        freq: 400
        max_dutycycle: 1
        half_dutycycle: .5
        min_dutycycle: 0
        hold_race_time: 2            # time in seconds that will allow the motors to run
        time_change_duty: 1
        one_sec: 1
        
        '''
        self._max_dutycycle = 1
        self._half_dutycycle = .5
        self._min_dutycycle = 0
        self.freq = 400
        self.pi = pigpio.pi()
        self.motor_pin = motor_pin

    def start_motor(self, target_duty):
        ''' Send the motor to the target duty cycle '''
        duty = 255 * target_duty
        self.pi.set_PWM_frequency(self.motor_pin, self.freq)
        self.pi.set_PWM_dutycycle(self.motor_pin, duty)

    def stop_motor(self):
        ''' Stop the motor '''
        self.pi.set_PWM_dutycycle(self.motor_pin, 0)
    
    def set_dutycycle(self, duty):
        ''' Set the duty cycle of the motor '''
        if duty > 255:
            duty = 255
        elif duty < 0:
            duty = 0
        
        self.pi.set_PWM_dutycycle(self.motor_pin, duty)
    
    def start(self):
        self.pi = pigpio.pi()

    def stop(self):
        self.pi.stop()

if __name__ == '__main__':
    print("demo code for the pwm output in raspberry pi")
    motor = Motor()
    motor.start()
    motor.start_motor(motor._half_dutycycle)
    time.sleep(30)
    motor.stop()
