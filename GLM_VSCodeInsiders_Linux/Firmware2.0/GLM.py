from MQTTDataProcessor import MQTTDataProcessor as MQTTProcessor
import json
from  Diagnostics import LocalLogger
import time

class GLM(object):

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def LoadConfigurations(self):
        """Returns configurations json object if loaded correctly else None"""
        try:
            with open("/home/GLM/Current/Configurations.json")as config_file:
                data = json.load(config_file)
                return data
        except:
            return {}

    def __init__(self):
        try:
            self.configs                = {}
            self.configs                = self.LoadConfigurations()
            self.logger                 = LocalLogger("GLM_Diagnostics", self.whoami(), self.configs)
            self.mqttdataprocessor      = MQTTProcessor(self.configs)
            
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' +  self.whoami())
            raise ValueError()

    def Process(self):
        while True:
            self.mqttdataprocessor.Process()
            time.sleep(30/1000)

    def main(self):
        self.Process()


if __name__ == "__main__":
    try:
        glmObj = GLM()
        glmObj.Process()
    except:
        exit("Failed to Init GLM")
