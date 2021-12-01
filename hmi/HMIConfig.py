import yaml

class HMI_Config:
    def __init__(self, path):
        self.path = path
        with open(path, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
            self.screen_fixed_size = self.config.get('monitor').get('screen_fixed_size')
        
    def get_screen_fixed_size(self):
        return self.screen_fixed_size

