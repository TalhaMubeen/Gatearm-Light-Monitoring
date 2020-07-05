import json
from Diagnostics import LocalLogger
from MQTTClient import MQTTClient
import socket
from VideoRecorder import VideoRecorder as recorder
import fcntl
import struct
import os
import LiveCommandHandler 
from RepeatedTimer import PeriodicTimer
from LedDetector import LedDetector
import time

class MQTTDataProcessor(object):
    """This Class Processes the data recieved over 'live' mqtt-topic"""

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self, configs ={}):
        try:
            self.logger     = LocalLogger('GLM_Diagnostics', self.whoami(), configs)
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
            
            self.RcvdDetectionMsg  = False 
            ledPath = ""
            ledPath = configs['GLM']['LedDetector']['LedCordinatesFilePath']
            ledPath = ledPath.replace("#",self.MY_ID)
            self.__LedDetector__ = LedDetector(ledPath, configs)
            self.__LedDetector__.SetProcessedVideoUploadCallback(self.OnVideoProcessingComplete)
            timeout = configs['GLM']['Recording']['Recording_Timeout']
            self.__UploadVideoTimer__  = PeriodicTimer(timeout *  60, self.UploadVideoOnTimer)
            self.Start()
            self.UploadVideoFilePath = ""
            self.isWaitingUpload = False
            self.IsLightPacketRcvd = False
            self.TS = ""
        except:
            self.logger.log(self.logger.ERROR,'Failed to Init ' +  self.whoami())
            raise ValueError()
    
    def UploadVideoOnTimer(self):
        # no detection status msg rcvd in first Timeout window
        if (self.RcvdDetectionMsg and (".mp4" in self.UploadVideoFilePath) and self.isWaitingUpload) or (self.RcvdDetectionMsg and (".mp4" in self.UploadVideoFilePath) and (not self.isWaitingUpload)): #Recording stopped before Timeout
            path = os.path.splitext(self.UploadVideoFilePath)[0]
            if not ('.mp4' in path):
                self.__LedDetector__.AddToProcessQueue(path, self.TS)     
                
        else:
            self.logger.log(self.logger.ERROR,'No Detection MSG RCVD FOR VIDEO: '+ self.UploadVideoFilePath)

        self.TS = ""
        self.UploadVideoFilePath = ""
        self.RcvdDetectionMsg   = False
        self.isWaitingUpload    = False        
        self.IsLightPacketRcvd  = False
        self.logger.log(self.logger.INFO,'VIDEO UPLOAD API RESET SUCCESSFULLY')

    def RegisterCallbacks(self):
        """
        Registers all the neccessary callbacks.
        """
        self.__mqttClient__.RegisterMessageRecieveCallback('live', self.MqttLiveDataCallback)
        self.__mqttClient__.RegisterMessageRecieveCallback('command', self.MqttCommandsCallback)

        self.__mqttDataTypes__["DetectionStatus"] = self.__OnDetectionStatusData__
        self.__mqttDataTypes__["AccelerometerAnalysisData"] = self.__OnAccelerometerAnalysisData__
        self.__mqttDataTypes__["LightPacketRcvd"] = self.__LightPacketRcvd__
        
        self.__pi_recorder__.RegisterFileRecordedCallback(self.OnVideoRecorded)
        
    def __LightPacketRcvd__(self):
        if self.__pi_recorder__.isRecording() == False and not self.IsLightPacketRcvd:
            self.IsLightPacketRcvd = True
            self.logger.log(self.logger.INFO,'Light Packet Recieved From SLM')
            self.RcvdDetectionMsg = False
            self.__pi_recorder__.start_video_recording()
        else:
            pass
               
    def InitLiveCmdHandler(self):
        self.__mqttChannelType__['live'] =  self.LiveCmdHandler.LiveCommandHandler
        self.LiveCmdHandler.InitVideoRecorder(self.__pi_recorder__)

    def Start(self):
        """
        Starts periodic live timer, MQTT Client and sends startup live packet 
        """
        self.__timer__.start()
        self.__mqttClient__.Connect()
        self.SendPeriodicLiveData()
 
    def __OnAccelerometerAnalysisData__(self, value):
        if self.IsLightPacketRcvd == False:
           self.logger.log(self.logger.INFO, 'Light Sensor Data Not Rcvd, Not recording video') 
       
        elif value.get("DetectionStatus") != None:
            if value['DetectionStatus'] >= 2 and not self.isWaitingUpload:
                if self.__pi_recorder__.isRecording() == False:
                    self.RcvdDetectionMsg = False
                    self.__pi_recorder__.start_video_recording()  
            else:
                self.logger.log(self.logger.INFO, 'Weak Accelerometer Analysis Data Rcvd', True)
        else:
            self.logger.log(self.logger.INFO, 'No Detection Status in Accelerometer Analysis Data')    

    def __OnDetectionStatusData__(self, value):
        """
        stop any on-going video recording
        """
        self.RcvdDetectionMsg = True
        ret = self.__pi_recorder__.stop_recording()
        if ret == True:
            self.logger.log(self.logger.DEBUG , 'Detection Status Recieved')
        else:
            if self.isWaitingUpload:
                self.logger.log(self.logger.INFO , 'Uploading Video NOW')
                self.__UploadVideoTimer__.stop()
                self.UploadVideoOnTimer()
            else:
                self.logger.log(self.logger.ERROR , 'Detection Status Recieved: No Video Recording and No Pending Video To Upload')
        return
    
    def OnVideoRecorded(self, path, TimeStamp):
        self.UploadVideoFilePath = path
        self.TS = TimeStamp
        self.isWaitingUpload = False
        
        if self.RcvdDetectionMsg == True: 
            self.logger.log(self.logger.INFO , 'Uploading Video NOW')
            self.UploadVideoOnTimer()
        else:
            self.logger.log(self.logger.INFO , 'Video Upload Waiting For Detection Status')
            self.isWaitingUpload = True
            self.__UploadVideoTimer__.restart()
    
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
            self.logger.log(self.logger.ERROR, 'Recieved Data is not in JSON format')
        
        elif jsonData.get("PacketType") != None:
            if jsonData["PacketType"] == "LiveData" and jsonData.get("Data") != None:
                data      = jsonData["Data"]
                dataType  = data["DataType"]
                
                if dataType == 'LightPacketRcvd':
                    self.__mqttDataTypes__[dataType]()
                else:
                    value     = data["Value"]
                if self.__mqttDataTypes__.get(dataType) != None:
                    #calling the reqiured DataType handler
                    self.__mqttDataTypes__[dataType](value)

            else:
                self.logger.log(self.logger.ERROR, 'Not a Live Data Packet')
      
    def GetPublishData(self, data, channel, action):
        publishObj = {}
        publishObj['Channel'] = channel
        publishObj['Action'] = action
        publishObj['GLMID'] = self.MY_ID
        try:    
            publishObj['Data'] = data
            obj = json.dumps(publishObj)
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Make Json Response') 

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
            self.logger.log(self.logger.ERROR, 'Recieved Data is not in JSON format')
        else:
            if jsonData.get("Channel") != None and jsonData.get("ChannelData") != None:
                #we recieved command 
                channel = jsonData['Channel']
                data = jsonData['ChannelData']
                self.__mqttChannelType__[channel](data)

    def OnVideoProcessingComplete(self, videoFile):
        if '.mp4' in videoFile:
            self.LiveCmdHandler.UploadVideo(videoFile)
        
    def Process(self):
        if self.__LedDetector__.isProcessingvideo():
            self.__LedDetector__.ProcessVideoFrame()

        elif self.__LedDetector__.inQueue():
            #processing video queue to find leds
            self.__LedDetector__.Process()

        self.__mqttClient__.Process()
        self.LiveCmdHandler.Process()
