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
from datetime import date, timedelta
from timeit import default_timer as timer
from HMIConfig import HMI_Config
import time

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
    run_button_color  = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)    # call the super class constructor (Screen)
        self.system_status  = False
        self.run_button_str = "STOP"
        self.date_str       = str(date.today().strftime("%d/%m/%y"))  # update the date string
        self.status_bar_str = "STOPPED"
        self.test_name_str  = "Test Name"
        self.timestamp_str  = str("00:00:00")
        self.start = timer()
        self.end = timer()
        Clock.schedule_interval(self.update_callback, 0.5)    # setup periodic task
        Clock.schedule_interval(self.update_callback_date, 60)    # setup periodic task
    
    def get_elapsed_time(self):
        return time.strftime("%H:%M:%S", time.gmtime(self.start - self.end))	

    def control_status_bar(self):
        if self.is_system_running():    # if system is running and no faults are detected
            self.status_bar_str = "RUNNING"
            self.start = timer()
        else:
            self.status_bar_str = "STOPPED"
            self.end = timer()
            self.start = timer()

    def update_callback(self, dt):
        
        self.control_status_bar()   # update the status bar
        if self.is_system_running():    # if system is running and no faults are detected
            self.timestamp_str = str(self.get_elapsed_time())

    def update_callback_date(self, dt):
        self.date_str = str(date.today().strftime("%d/%m/%y"))  # update the date string

    def on_test_name_evt(self, text_input):
        print(f"text included - {text_input}")
        self.test_name_str = text_input

    def is_system_running(self):
        return self.system_status

    def run_button_pressed(self):
        self.system_status = not self.system_status
        if self.system_status:
            self.run_button_str = 'START'
            self.ids['run_button_id'].background_color = [0, 1, 0, 1]
        else:
            self.run_button_str = 'STOP'
            self.ids['run_button_id'].background_color = [1, 0, 0, 1]
        

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
