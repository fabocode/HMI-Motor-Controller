import kivy
kivy.require('2.0.0') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.properties import ListProperty
from kivy.config import Config
from screeninfo import get_monitors
from datetime import date, datetime, timedelta
from timeit import default_timer as timer
from HMIConfig import HMI_Config
from sensors.torque import Torque_Sensor
from sensors.stepper_motor import Stepper_Motor
import time
import excel
import re

# load the configuration file
config = HMI_Config('config/hmi.yaml')
screen_width = str(int(get_monitors()[0].width  * config.get_screen_fixed_size()))  # get the current screen size
screen_height = str(int(get_monitors()[0].height * config.get_screen_fixed_size()))
Config.set('graphics', 'width', screen_width)
Config.set('graphics', 'height', screen_height)    
Config.set('kivy', 'keyboard_mode', 'systemanddock')    # enable virtual keyboard on text input

# main screen
class Main(Screen):
    date_str                = StringProperty('')
    run_button_str          = StringProperty('')
    status_bar_str          = StringProperty('')
    test_name_str           = StringProperty('')
    timestamp_str           = StringProperty('')
    torque_sensor_str       = StringProperty('')
    start_time_str          = StringProperty('')
    end_time_str            = StringProperty('')
    blade_tip_velocity_str  = StringProperty('')
    total_revolution_str   = StringProperty('')
    current_rpm_str         = StringProperty('')
    run_button_color        = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)    # call the super class constructor (Screen)
        self.system_status      = False
        self.run_button_str     = "START"
        self.date_str           = self.get_date()  # update the date string
        self.status_bar_str     = "STOPPED"
        self.test_name_str      = ""
        self.timestamp_str      = str("00:00:00")
        self.torque_sensor_str  = "0.00"
        self.start_time_str     = str("HH:MM:SS - M/D/Y")
        self.end_time_str       = str("HH:MM:SS - M/D/Y")
        self.start              = timer()
        self.end                = timer()
        self.now = datetime.today()
        self.past = datetime.today()
        self.past_time = 0
        self.excel              = excel # create an instance of the excel module to save the data
        self.torque_sensor      = Torque_Sensor() # create an instance of the torque sensor (address 0, channel 0)
        self.stepper_motor      = Stepper_Motor() # create an instance of the stepper motor
        Clock.schedule_interval(self.update_callback, 1)    # setup periodic task
        Clock.schedule_interval(self.update_callback_date, 300)    # setup periodic task
        self.counter = 0
        self.notes_str = ''
        self.data = self.clear_data()
        self.is_rpm_input_valid = False
        self.rpm_input = 0.0
        self.is_jogging = False
        self.total_revolution = 0.0
        self.blade_tip_velocity_str  = "0.0"
        self.total_revolution_str   = "0.0"
        self.current_rpm_str         = "0.0"
        self.seconds_counter = 0

    def validate_name(self, filename):
        filename = re.sub(r'[^\w\s-]', '', filename.lower())
        return re.sub(r'[-\s]+', '-', filename).strip('-_')

    # Utils functions
    def get_date(self):
        return str(date.today().strftime("%m/%d/%y"))

    def get_time(self):
        return str(datetime.now().strftime("%H:%M:%S - %m/%d/%y"))

    def get_time_stamp(self):
        return str(timedelta(seconds=(self.now - self.past).seconds))

    def is_system_running(self):
        return self.system_status

    # GUI functions and events
    def control_status_bar(self):
        if self.is_system_running():    # if system is running and no faults are detected
            self.status_bar_str = "RUNNING"
            self.start = timer()
        else:
            self.status_bar_str = "STOPPED"
            self.end = timer()
            self.start = timer()

    def on_test_name_input(self, text_input):
        ''' Event handler for the test name input field '''
        self.test_name_str = self.validate_name(text_input)
        print(f"text included - {self.test_name_str}")

    def on_set_rpm_input(self, text_input):
        ''' Event handler for the RPM input field '''
        # check if text input is valid number
        if text_input.isdigit():

            check = re.match(r'^[0-9]*$', text_input)
            if check:
                self.rpm_input = round(float(text_input), 2)
                self.is_rpm_input_valid = True
            else:
                self.is_rpm_input_valid = True
                self.rpm_input = 0.0
        else:
            print("no valid input")
            self.is_rpm_input_valid = True
            self.rpm_input = 0.0
        self.current_rpm_str = str(self.rpm_input)
        self.blade_tip_velocity_str = self.get_blade_tip_velocity(self.rpm_input)
        

    def on_notes_input(self, text_input):
        ''' Event handler for the notes input field '''
        self.notes_str = text_input

    def on_start_jog(self):
        ''' Event handler for the start jog button '''
        if not self.is_system_running():
            # self.stepper_motor.start_jog()
            self.is_jogging = True
        #     self.run_button_color = [0, 1, 0, 1]
        # else:
        #     self.run_button_color = [1, 0, 0, 1]

    def on_stop_jog(self):
        ''' Event handler for the stop jog button '''
        if not self.is_system_running():
            # self.stepper_motor.stop()
            self.is_jogging = False
        #     self.run_button_color = [1, 0, 0, 1]
        # else:
        #     self.run_button_color = [0, 1, 0, 1]

        
    def clear_data(self):
        ''' Clear the data dictionary '''
        self.data = {   # create a dictionary to store the data
            'Start Time': [],
            'Stop Time': [],
            'Elapsed Time': [],
            'Time Stamps': [],
            'RPM': [],
            'Torque': [],
            'Blade Tip Velocity': [],
            'Total Revolution': [],
            'Notes': []
        }
        return self.data 

    def add_data(self, data, label):
        if self.test_name_str != '' and self.test_name_str != 'Test Name' and self.data['Time Stamps'] != ():
            self.data[label].append(data)

    def run_button_pressed(self):
        self.system_status = not self.system_status
        if self.system_status:
            self.run_button_str = 'STOP'
            self.ids['run_button_id'].background_color = [1, 0, 0, 1]

            self.add_data(self.get_time(), 'Start Time')
            self.start_time_str = self.get_time()
            self.end_time_str = str("HH:MM:SS - M/D/Y")
        else:
            # if test name is not empty, save the data to the excel file
            if self.test_name_str != '' and self.test_name_str != 'Test Name' and self.data['Time Stamps'] != ():
                # save data into excel file and clear the data dictionary
                self.stepper_motor.stop()
                self.data['Notes'].append(self.notes_str)
                self.add_data(self.get_time(), 'Stop Time')
                self.end_time_str = self.get_time()
                filename = config.get_path_to_save(self.test_name_str)
                self.excel.save_data(self.data, filename)
                self.data = self.clear_data()
            self.run_button_str = 'START'
            self.ids['run_button_id'].background_color = [0, 1, 0, 1]
            self.clear_total_revolution()  # clear the total revolutions counter
            # self.data['Stop Time'].append(self.get_time())
    
    def get_blade_tip_velocity(self, rpm):
        rpm = float(rpm)
        return str(round( (27.33 * (rpm / 60.0)), 2))

    def get_total_revolution(self, rpm):
        rpm = float(rpm)
        return round((rpm / 60.0) + self.total_revolution, 2)

    def clear_total_revolution(self):
        self.total_revolution = 0.0

    def get_time_format(self, sec):
        return time.strftime("%H:%M:%S", time.gmtime(sec))
        
    # Callback functions for the periodic task
    def update_callback(self, dt):
        ''' Callback function for the periodic task '''
        if self.is_jogging:
            self.stepper_motor.jog()

        self.control_status_bar()   # update the status bar

        torque_data = self.torque_sensor.get_torque()   # get the torque data from the torque sensor
        self.torque_sensor_str = str(torque_data)
        
        
        self.now = datetime.today() # get the current time
        self.timestamp_str = self.get_time_stamp()    # update the timestamp string

        if self.is_system_running():    # if system is running and no faults are detected
            self.seconds_counter += 1
            self.total_revolution = self.get_total_revolution(self.rpm_input)
            self.total_revolution_str = str(self.total_revolution)
            self.data['Elapsed Time'].append(self.get_time_format(self.seconds_counter))
            self.data['Time Stamps'].append(self.get_time())
            self.data['RPM'].append(self.current_rpm_str)      # TO DO: get the RPM from the stepper motor
            self.data['Torque'].append(torque_data)
            self.data['Blade Tip Velocity'].append(self.blade_tip_velocity_str)   # TO DO: get the blade tip velocity from the stepper motor
            self.data['Total Revolution'].append(self.total_revolution_str)
            # update the RPM and blade tip velocity
            if self.is_rpm_input_valid and not self.is_jogging:
                self.is_rpm_input_valid = False # reset the input flag
                self.stepper_motor.start()
                self.stepper_motor.set_rpm(self.rpm_input)
                print("start the motor")

        elif not self.is_system_running() and not self.is_jogging:   # if system is stopped and not jogging
            self.past = datetime.today()    # get the current time
            self.past_time = datetime.today()
            self.stepper_motor.stop()

    # callback function for the date update    
    def update_callback_date(self, dt):
        self.date_str = str(date.today().strftime("%d/%m/%y"))  # update the date string


# screen manager
class WindowManager(ScreenManager):
    pass

# designate our .kv design file 
kv = Builder.load_file("hmi.kv")


class HMI_Motor(App):

    def build(self):
        return kv

if __name__ == '__main__':
    HMI_Motor().run()
