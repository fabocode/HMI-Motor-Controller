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
from datetime import date, datetime
from timeit import default_timer as timer
from HMIConfig import HMI_Config
from sensors.torque import Torque_Sensor
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
    date_str          = StringProperty('')
    run_button_str    = StringProperty('')
    status_bar_str    = StringProperty('')
    test_name_str     = StringProperty('')
    timestamp_str     = StringProperty('')
    torque_sensor_str = StringProperty('')
    start_time_str    = StringProperty('')
    end_time_str      = StringProperty('')
    run_button_color  = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)    # call the super class constructor (Screen)
        self.system_status      = False
        self.run_button_str     = "START"
        self.date_str           = self.get_date()  # update the date string
        self.status_bar_str     = "STOPPED"
        self.test_name_str      = "Test Name"
        self.timestamp_str      = str("00:00:00")
        self.torque_sensor_str  = "0.00"
        self.start_time_str     = str("HH:MM:SS - M/D/Y")
        self.end_time_str       = str("HH:MM:SS - M/D/Y")
        self.start              = timer()
        self.end                = timer()
        self.excel              = excel # create an instance of the excel module to save the data
        self.torque_sensor      = Torque_Sensor(0,0) # create an instance of the torque sensor (address 0, channel 0)
        Clock.schedule_interval(self.update_callback, 1)    # setup periodic task
        Clock.schedule_interval(self.update_callback_date, 300)    # setup periodic task
        self.counter = 0

        self.data = self.clear_data()

    def validate_name(self, filename):
        filename = re.sub(r'[^\w\s-]', '', filename.lower())
        return re.sub(r'[-\s]+', '-', filename).strip('-_')

    # Utils functions
    def get_date(self):
        return str(date.today().strftime("%m/%d/%y"))

    def get_time(self):
        return str(datetime.now().strftime("%H:%M:%S - %m/%d/%y"))
    
    def get_elapsed_time(self):
        return str(time.strftime("%H:%M:%S", time.gmtime(self.start - self.end))	)

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

    def on_test_name_evt(self, text_input):
        ''' Event handler for the test name input field '''
        self.test_name_str = self.validate_name(text_input)
        print(f"text included - {self.test_name_str}")

    def clear_data(self):
        ''' Clear the data dictionary '''
        self.data = {   # create a dictionary to store the data
            'Start Time': [],
            'Stop Time': [],
            'Elapsed Time': [],
            'Time Stamps': [],
            'RPM': [],
            'Torque': [],
            'Blade Tip Velocity': []
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
                self.excel.save_data(self.data, self.test_name_str)
                # save data into excel file 
                print("saving data into excel file ")
                self.add_data(self.get_time(), 'Stop Time')
                self.end_time_str = self.get_time()
                filename = config.get_path_to_save(self.test_name_str)
                self.excel.save_data(self.data, filename)
                self.data = self.clear_data()
            self.run_button_str = 'START'
            self.ids['run_button_id'].background_color = [0, 1, 0, 1]
            # self.data['Stop Time'].append(self.get_time())
    
    # Callback functions for the periodic task

    def update_callback(self, dt):
        self.control_status_bar()   # update the status bar
        torque_data = self.torque_sensor.get_torque()
        self.torque_sensor_str = str(torque_data)
        if self.is_system_running():    # if system is running and no faults are detected
            self.timestamp_str = self.get_elapsed_time()    # update the timestamp string
            self.data['Elapsed Time'].append(self.get_elapsed_time())
            self.data['Time Stamps'].append(self.get_time())
            self.data['RPM'].append(0)
            self.data['Torque'].append(torque_data)
            self.data['Blade Tip Velocity'].append(0)

    # callback function for the date update    
    def update_callback_date(self, dt):
        self.date_str = str(date.today().strftime("%d/%m/%y"))  # update the date string


# screen manager
class WindowManager(ScreenManager):
    pass

# designate our .kv design file 
kv = Builder.load_file("hmi.kv")


class HMIApp(App):

    def build(self):
        return kv

if __name__ == '__main__':
    HMIApp().run()
