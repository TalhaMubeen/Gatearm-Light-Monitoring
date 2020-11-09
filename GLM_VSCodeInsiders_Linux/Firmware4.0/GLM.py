import Logic
import json
import time


class GLM(object):

    def whoami(self):
        """returns the class name as string"""
        return type(self).__name__

    def LoadConfigurations(self):
        """Returns configurations json object if loaded correctly else None"""
        try:
            with open("./Logic/Configurations.json")as config_file:
                data = json.load(config_file)
                return data
        except:
            return {}
        pass

    def __init__(self):
        try:
            self.configs = {}
            self.configs = self.LoadConfigurations()
            self.Init(config=self.configs)
            self.Start()
            self.logger = Logic.GetLogger().SetAPIName(self.whoami())
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' + self.whoami())
            raise ValueError()
        pass

    def EXECUTE(self):
        while True:
            self.Process()
            time.sleep(30 / 1000)

    def Init(self, config):
        _Diagnostics = Logic.LocalLogger("GLM_Diagnostics", config)

        MY_ID = config['GLM']['MY_ID']
        ledPath = config['GLM']['LedDetector']['LedCordinatesFilePath']
        # ledPath = ledPath.replace("#", MY_ID)
        ledPath = "./GLM01.pckl"

        Logic.UDPClient(config)
        Logic.HttpClient(config)
        Logic.MQTTClient(config)
        Logic.LedDetector(config)
        Logic.BlinkCounter(ledPath, config)
        Logic.WIFIZMQClient(config)
        Logic.VideoRecorder(config)
        Logic.ZMQDataProcessor(config)
        Logic.MQTTDataProcessor(config)
        Logic.LiveCommandHandler(config)
        Logic.VideoRecordingProcessor(config)

    def Start(self):
        Logic.LiveCommandHandler.Instance().Start()
        Logic.MQTTDataProcessor.Instance().Start()
        Logic.VideoRecordingProcessor.Instance().Start()
        Logic.ZMQDataProcessor.Instance().Start()

    def Process(self):
        Logic.HttpClient.Instance().Process()
        Logic.MQTTClient.Instance().Process()
        Logic.UDPClient.Instance().Process()
        Logic.WIFIZMQClient.Instance().Process()
        Logic.VideoRecordingProcessor.Instance().Process()
        time.sleep(30 / 1000)


if __name__ == "__main__":
    try:
        glmObj = GLM()
        glmObj.EXECUTE()
    except:
        exit("Failed to Init GLM")
    pass
