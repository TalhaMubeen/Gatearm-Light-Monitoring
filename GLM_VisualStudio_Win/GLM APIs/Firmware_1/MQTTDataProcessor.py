import json
from Diagnostics import LocalLogger
from MQTTClient import MQTTClient
import socket
from VideoRecorder import VideoRecorder as recorder
#import fcntl
import struct
import os
import LiveCommandHandler
from PeriodicTimer import PeriodicTimer



class MQTTDataProcessor(object):
    """This Class Processes the data recieved over 'live' mqtt-topic"""

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self, configs ={}):
        try:
            self.__logger__     = LocalLogger('GLM_Diagnostics', self.whoami(), configs)
            self.configurations = configs
            self.MY_ID          = configs['GLM']['MY_ID']
            self.__mqttClient__ = MQTTClient(configs)
            self.__pi_recorder__= recorder(configs)
            self.__mqttDataTypes__ = {}
            self.__mqttChannelType__ = {}
            self.RegisterCallbacks()            
            self.__timer__ = PeriodicTimer(5 *  60, self.SendPeriodicLiveData)
            self.LiveCmdHandler = LiveCommandHandler.LiveCommandHandler(configs, self)
            self.InitLiveCmdHandler()

            self.Start()

        except:
            self.__logger__.log(self.logger.ERROR,'Failed to Init ' +  self.whoami())
            raise ValueError()

    def RegisterCallbacks(self):
        """
        Registers all the neccessary callbacks.
        """
        self.__mqttClient__.RegisterMessageRecieveCallback('live', self.MqttLiveDataCallback)
        self.__mqttClient__.RegisterMessageRecieveCallback('command', self.MqttCommandsCallback)

        self.__mqttDataTypes__["LightSensorData"] = self.__OnLightSensorData__
        self.__mqttDataTypes__["DetectionStatus"] = self.__OnDetectionStatusData__


    def InitLiveCmdHandler(self):
        self.__mqttChannelType__['live'] =  self.LiveCmdHandler.LiveCommandHandler
        self.LiveCmdHandler.InitVideoRecorder(self.__pi_recorder__)

    def Start(self):
        """
        Starts periodic live timer, MQTT Client and sends startup live packet 
        """
        #self.__timer__.start()
        self.__mqttClient__.Connect()
        #self.SendPeriodicLiveData()

    def __OnLightSensorData__(self):
        #starting video recording on light data
        if self.__pi_recorder__.isRecording() == True:
            pass
            #self.__pi_recorder__.IncreaseVideoRecordingInterval()
        else:
            self.__pi_recorder__.start_video_recording()

    def __OnDetectionStatusData__(self):
        """
        stop any on-going video recording
        """
        ret = self.__pi_recorder__.stop_recording()
        if ret == True:
            recordingFile = self.__pi_recorder__.get_last_recorded_file()
            # use this file to process blink count finding .. etc
            self.__logger__.log(self.__logger__.DEBUG , 'Detection Status Data Recieved')

        else:
            self.__logger__.log(self.__logger__.ERROR , 'Failed to find any last recording')
        return

    def __str_to_json(self, str_data):
        """
        This module converts string to json object
        """
        if type(str_data) is str:
           return json.loads(str_data)
        else:
          return None

    def MqttLiveDataCallback(self, str_data = ""):
        """ 
        Register this function with MQTTClient callback function
        to recieved data over live topic
        """
        jsonData = {}
        jsonData = self.__str_to_json(str_data)
        if jsonData is None:
            self.__logger__.log(self.__logger__.ERROR, 'Recieved Data is not in JSON format')
        
        elif jsonData.get("PacketType") != None:
            if jsonData["PacketType"] == "LiveData" and jsonData.get("Data") != None:
                data = jsonData["Data"]
                dataType = data["DataType"]

                if self.__mqttDataTypes__.get(dataType) != None:
                    #calling the reqiured DataType handler
                    self.__mqttDataTypes__[dataType]()

            else:
                self.__logger__.log(self.__logger__.ERROR, 'Not a Live Data Packet')
      
    def GetPublishData(self, data, channel, action):
        publishObj = {}
        publishObj['Channel'] = channel
        publishObj['Action'] = action
        publishObj['GLMID'] = self.MY_ID
        try:    
            publishObj['Data'] = data
            obj = json.dumps(publishObj)
        except:
            self.__logger__.log(self.__logger__.ERROR, 'Failed to Make Json Response') 

        return obj


    def PublishDataOverMQTT(self, data):
        self.__mqttClient__.Publish(data)


    def SendPeriodicLiveData(self):
        data    = self.LiveCmdHandler.Get_local_IPDetails()
        retData = self.GetPublishData(data, 'live', 'auto')
        self.__mqttClient__.PublishLiveData(retData)
        self.__timer__.restart()

    def MqttCommandsCallback(self, str_data):
        jsonData = {}
        jsonData = self.__str_to_json(str_data)
        if jsonData is None:
            self.__logger__.log(self.__logger__.ERROR, 'Recieved Data is not in JSON format')
        else:
            if jsonData.get("Channel") != None and jsonData.get("ChannelData") != None:
                #we recieved command 
                channel = jsonData['Channel']
                data = jsonData['ChannelData']
                self.__mqttChannelType__[channel](data)

    def Process(self):
        self.__mqttClient__.Process()
        self.LiveCmdHandler.Process()
        pass
