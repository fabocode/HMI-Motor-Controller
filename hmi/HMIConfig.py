import yaml
from pathlib import Path

class HMI_Config:
    def __init__(self, path):
        self.path = path
        with open(path, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
            self.screen_fixed_size = self.config.get('monitor').get('screen_fixed_size')
        
    def get_screen_fixed_size(self):
        return self.screen_fixed_size

    @staticmethod
    def get_path_to_save(filename):
        return str(Path.home()) + '/Desktop/' + filename 

if __name__ == '__main__':
    # path = pathlib.Path(__file__).parent.absolute() / 'config.yaml'
    # hmi_config = HMI_Config(path)
    # print(hmi_config.get_screen_fixed_size())
    print(HMI_Config.get_path_to_save())
    
    print(f"{'/home/pi/Desktop/'} { '/home/pi/Desktop/' == HMI_Config.get_path_to_save()} {HMI_Config.get_path_to_save()}")