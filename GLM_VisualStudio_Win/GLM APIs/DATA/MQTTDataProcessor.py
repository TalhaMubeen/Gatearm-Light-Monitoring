from VideoRecorder import VideoRecorder 
import json
from Diagnostics import LocalLogger
from Client.MQTTClient import MQTTClient
from Client.HttpClient import HttpClient
import time
import os

class MQTTDataProcessor(object):
    """This Class Processes the data recieved over 'live' mqtt-topic"""
    Signal_Lights_Data_Videos_Path = "/home/GLM/DIAGNOSTICS/"
    ImageUploadUrl = "http://172.19.91.135/glm/image/upload";
    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self):
        self.__mqttClient__ = MQTTClient()      
        self.__httpClient__ = HttpClient()      

        self.__logger__      = LocalLogger('GLM_Diagnostics', self.whoami())
        self.__pi_recorder__ = VideoRecorder()
        self.__mqttDataTypes__ = {}
        self.__mqttChannelType__ = {}
        self.__init_mqtt_data_processing_callbacks__()

    def StartMqttClient(self):
        self.__mqttClient__.RegisterMessageRecieveCallback('live', self.MqttLiveDataCallback)
        self.__mqttClient__.RegisterMessageRecieveCallback('command', self.MqttCommandsCallback)
        self.__mqttClient__.Start()

    def RegisterMQTTCommandsProcessor(self):
        self.__mqttChannelType__['live'] = self.LiveCommandHandler

    def __OnLightSensorData__(self):
        #starting video recording on light data
        self.__pi_recorder__.start_video_recording()
        self.__logger__.log(self.__logger__.DEBUG , 'Light Sensor Data Recieved, Starting video recording for next 10-minutes')
        return

    def __OnDetectionStatusData__(self):
        """
        stop any on-going video recording
        """
        ret = self.__pi_recorder__.stop_recording()
        if ret == True:
            recordingFile = self.__pi_recorder__.get_last_recorded_file()

        self.__logger__.log(self.__logger__.DEBUG , 'Detection Status Data Recieved')
        return

    def __init_mqtt_data_processing_callbacks__(self):
         self.__mqttDataTypes__["LightSensorData"] = self.__OnLightSensorData__
         self.__mqttDataTypes__["DetectionStatus"] = self.__OnDetectionStatusData__

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
        else:

           if jsonData.get("PacketType") != None:
               if jsonData["PacketType"] == "LiveData" and jsonData.get("Data") != None:
                   #we have valid live data packet
                   self.__ProcessLiveData__(jsonData["Data"])

                   dataType = data["DataType"]

                   if self.__mqttDataTypes__.get(dataType) != None:
                      #calling the reqiured DataType handler
                      self.__mqttDataTypes__[dataType]()

               else:
                   self.__logger__.log(self.__logger__.ERROR, 'Not a Live Data Packet')
           else:
               self.__logger__.log(self.__logger__.ERROR, 'PacketType not found')

    def LiveCommandHandler(self, channelData):
        if channelData.get("Action") != None:
            if channelData['Action'] == 'CaptureImage':
                #Capture and Upload Image here
                 path = self.__pi_recorder__.capture_image()
                 
                 if os.path.exists(path):
                     self.__httpClient__.PostImages(self.ImageUploadUrl ,path)
        return
      
    
    def MqttCommandsCallback(self, str_data):
        jsonData = {}
        jsonData = self.__str_to_json(str_data)
        if jsonData is None:
            self.__logger__.log(self.__logger__.ERROR, 'Recieved Data is not in JSON format')
        else:
            if jsonData.get("Channel") != None and jsonData.get("ChannelData") != None:
                #we recieved command 

                self.__mqttChannelType__[jsonData['Channel']](jsonData["ChannelData"])

"""
Move this code in main module
"""

obj = MQTTDataProcessor()
obj.StartMqttClient()
while True:
    time.sleep(50 / 1000)
    continue
