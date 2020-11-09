import Logic
import json


class ZMQDataProcessor(object):
    """
	This class records the video 
	"""

    def whoami(self):
        """
		returns the class name as string
		"""
        return type(self).__name__

    __instance__ = None

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
		"""
        return ZMQDataProcessor.__instance__

    def __str_to_json(self, str_data):
        """
		This module converts string to json object
		"""
        if type(str_data) is str:
            return json.loads(str_data)
        else:
            return None

    def __init__(self, configs):
        try:
            self.logger = Logic.GetLogger().SetAPIName(self.whoami())
            self.__ZMQEIPCommandType__ = {}
            # Setting Static Instance
            if ZMQDataProcessor.__instance__ is None:
                ZMQDataProcessor.__instance__ = self
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' + self.whoami())
            raise ValueError()
        pass

    def Start(self):
        Logic.GetZMQClient().SetZMQDataRcvCallback(self.OnZMQDataRecieved)

    def InitZMQCommandsMap(self):
        self.__ZMQEIPCommandType__["StartRecording"] = Logic.GetVideoRecordingProcessor().OnStartRecordingRcvd
        self.__ZMQEIPCommandType__["StopRecording"] = Logic.GetVideoRecordingProcessor().OnStopRecordingRcvd

    def OnZMQDataRecieved(self, data):
        jsonData = {}
        jsonData = self.__str_to_json(data)

        if jsonData is None:
            self.logger.log(self.logger.ERROR, 'Recieved Data is not in JSON format')
        else:
            if jsonData.get("Command") != None:
                # we recieved command
                cmd = jsonData['Command']
                if self.__ZMQEIPCommandType__.get(cmd) != None:
                    self.__ZMQEIPCommandType__[cmd](data)
            else:
                pass
        pass
