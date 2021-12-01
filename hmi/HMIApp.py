import kivy
kivy.require('2.0.0') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.label import Label
from kivy.config import Config
from screeninfo import get_monitors
from HMIConfig import HMI_Config

# load the configuration file
config = HMI_Config('config/hmi.yaml')

# get the current screen size
screen_width = str(int(get_monitors()[0].width  * config.get_screen_fixed_size()))
screen_height = str(int(get_monitors()[0].height * config.get_screen_fixed_size()))
# set the screen size
Config.set('graphics', 'width', screen_width)
Config.set('graphics', 'height', screen_height)    

class MyApp(App):

    def build(self):
        return Label(text='Hello world')


if __name__ == '__main__':
    MyApp().run()
