import Logic
import socket
import fcntl
import struct
import os
import time
import json


class MQTTDataProcessor(object):
    """This Class Processes the data recieved over 'live' mqtt-topic"""

    __instance__ = None

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
		"""
        return MQTTDataProcessor.__instance__

    def __init__(self, configs={}):
        try:
            self.logger = Logic.GetLogger().SetAPIName(self.whoami())
            self.configurations = configs
            self.MY_ID = configs['GLM']['MY_ID']
            self.EIP_ID = configs['GLM']['EIP_ID']

            self.__mqttEIPDataTypes__ = {}
            self.__mqttChannelType__ = {}
            self.__timer__ = Logic.PeriodicTimer(5 * 60, self.SendPeriodicLiveData)

            # Setting Static Object
            if MQTTDataProcessor.__instance__ is None:
                MQTTDataProcessor.__instance__ = self
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' + self.whoami())
            raise ValueError()
        pass

    def whoami(self):
        """
		returns the class name as string
		"""
        return type(self).__name__

    def Start(self):
        """
		Registers all the neccessary callbacks.
		Starts periodic live timer, MQTT Client and sends startup live packet 
		"""
        Logic.GetMQTTClient().RegisterMessageRecieveCallback(self.EIP_ID, self.MqttEIPDataCallback)
        Logic.GetMQTTClient().RegisterMessageRecieveCallback('command', self.MqttCommandsCallback)
        self.__mqttChannelType__['live'] = Logic.GetLiveCmdHandler().LiveCommandHandler
        self.__timer__.start()
        Logic.GetMQTTClient().Connect()
        self.SendPeriodicLiveData()

    def __str_to_json(self, str_data):
        """
		This module converts string to json object
		"""
        if type(str_data) is str:
            return json.loads(str_data)
        else:
            return None

    def MqttEIPDataCallback(self, str_data=""):
        """
		Register this function with MQTTClient callback function
		to recieved data over live topic
		"""
        jsonData = {}
        jsonData = self.__str_to_json(str_data)
        if jsonData is None:
            self.logger.log(self.logger.ERROR, 'Recieved Data is not in JSON format')
        elif jsonData.get("Command") != None:
            cmdType = jsonData["Command"]
            if self.__mqttEIPDataTypes__.get(cmdType) != None:
                # calling the reqiured Command Type handler
                self.__mqttEIPDataTypes__[cmdType]()
            else:
                self.logger.log(self.logger.ERROR, 'EIP command Callback Not Registered')
        else:
            pass

    def GetPublishData(self, data, channel, action):
        publishObj = {}
        publishObj['Channel'] = channel
        publishObj['Action'] = action
        publishObj['GLMID'] = self.MY_ID
        publishObj['EIPID'] = self.EIP_ID
        try:
            publishObj['Data'] = data
            obj = json.dumps(publishObj)
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Make Json Response')
        return obj

    def PublishDataOverMQTT(self, data):
        Logic.GetMQTTClient().Publish(data)

    def SendPeriodicLiveData(self):
        data = Logic.GetLiveCmdHandler().Get_local_IPDetails()
        retData = self.GetPublishData(data, 'live', 'auto')
        Logic.GetMQTTClient().PublishLiveData(retData)
        self.__timer__.restart()

    def MqttCommandsCallback(self, str_data):
        jsonData = {}
        jsonData = self.__str_to_json(str_data)
        if jsonData is None:
            self.logger.log(self.logger.ERROR, 'Recieved Data is not in JSON format')
        else:
            if jsonData.get("Channel") != None and jsonData.get("ChannelData") != None:
                # we recieved command
                channel = jsonData['Channel']
                data = jsonData['ChannelData']
                self.__mqttChannelType__[channel](data)
            else:
                pass
