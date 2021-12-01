import kivy
kivy.require('2.0.0') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.config import Config
from screeninfo import get_monitors
from datetime import date 
from HMIConfig import HMI_Config

# load the configuration file
config = HMI_Config('config/hmi.yaml')

# get the current screen size
screen_width = str(int(get_monitors()[0].width  * config.get_screen_fixed_size()))
screen_height = str(int(get_monitors()[0].height * config.get_screen_fixed_size()))
# set the screen size
Config.set('graphics', 'width', screen_width)
Config.set('graphics', 'height', screen_height)    

# main screen
class Main(Screen):
    date_str = StringProperty('')

    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)    # call the super class constructor (Screen)
        Clock.schedule_interval(self.update_callback, 1)    # setup periodic task

    def update_callback(self, dt):
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
