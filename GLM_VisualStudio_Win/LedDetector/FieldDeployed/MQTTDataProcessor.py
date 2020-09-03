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

	def __init__(self, configs ={}):
		try:
			self.logger     = LocalLogger('GLM_Diagnostics', self.whoami(), configs)
			self.configurations = configs
			self.MY_ID          = configs['GLM']['MY_ID']
			self.EIP_ID          = configs['GLM']['EIP_ID']
			self.__mqttClient__ = MQTTClient(configs)
			self.__pi_recorder__= recorder(configs)
			self.__mqttEIPDataTypes__ = {}
			self.__mqttChannelType__ = {}
			self.RegisterCallbacks()            
			self.__timer__ = PeriodicTimer(5 *  60, self.SendPeriodicLiveData)
			self.LiveCmdHandler = LiveCommandHandler.LiveCommandHandler(configs, self)
			self.InitLiveCmdHandler()

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
			self.StartRecordingPktRcvd = False
			self.StopRecordingPktRcvd  = False 
			self.TS = ""
		except:
			self.logger.log(self.logger.ERROR,'Failed to Init ' +  self.whoami())
			raise ValueError()
		pass

	def whoami(self):
		"""
		returns the class name as string
		"""
		return type(self).__name__

	def UploadVideoOnTimer(self):
		# no detection status msg rcvd in first Timeout window
		if self.StopRecordingPktRcvd and (".mp4" in self.UploadVideoFilePath): #Recording stopped before Timeout
			path = os.path.splitext(self.UploadVideoFilePath)[0]
			if not ('.mp4' in path):
				self.__LedDetector__.AddToProcessQueue(path, self.TS)     
		else:
			self.logger.log(self.logger.ERROR,'No Stop Recording MSG RCVD FOR VIDEO: '+ self.UploadVideoFilePath)

		self.TS = ""
		self.UploadVideoFilePath = ""
		self.StopRecordingPktRcvd   = False
		self.isWaitingUpload        = False        
		self.StartRecordingPktRcvd  = False
		self.logger.log(self.logger.INFO,'VIDEO UPLOAD API RESET SUCCESSFULLY')

	def RegisterCallbacks(self):
		"""
		Registers all the neccessary callbacks.
		"""
		self.__mqttClient__.RegisterMessageRecieveCallback(self.EIP_ID, self.MqttEIPDataCallback)
		self.__mqttClient__.RegisterMessageRecieveCallback('command', self.MqttCommandsCallback)

		self.__mqttEIPDataTypes__["StopRecording"] = self.__StopRecordingRcvd__
		self.__mqttEIPDataTypes__["StartRecording"] = self.__StartRecordingRcvd__
		self.__pi_recorder__.RegisterFileRecordedCallback(self.OnVideoRecorded)

	def __StartRecordingRcvd__(self):
		if self.__pi_recorder__.isRecording() == False and not self.StartRecordingPktRcvd:
			self.StartRecordingPktRcvd = True
			self.logger.log(self.logger.INFO,'Start Recording Packet Recieved From EIP ' + self.EIP_ID)
			self.StopRecordingPktRcvd = False
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

	def __StopRecordingRcvd__(self):
		"""
		stop any on-going video recording
		"""
		self.StopRecordingPktRcvd = True
		ret = self.__pi_recorder__.stop_recording()
		if ret == True:
			self.logger.log(self.logger.DEBUG , 'Stop Recording Packet Recieved from EIP ' + self.EIP_ID)
		else:
			if self.isWaitingUpload:
				self.logger.log(self.logger.INFO , 'Uploading Video NOW')
				self.__UploadVideoTimer__.stop()
				self.UploadVideoOnTimer()
			else:
				self.logger.log(self.logger.ERROR , 'Stop Recording Packet Recieved: No Video Recording | No Pending Upload')
		return

	def OnVideoRecorded(self, path, TimeStamp):
		self.UploadVideoFilePath = path
		self.TS = TimeStamp
		self.isWaitingUpload = False

		if self.StopRecordingPktRcvd == True: 
			self.logger.log(self.logger.INFO , 'Uploading Video NOW')
			self.UploadVideoOnTimer()
		else:
			self.logger.log(self.logger.INFO , 'Video Upload API Waiting For STOP RECORDING PACKET from EIP ' + self.EIP_ID)
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

	def MqttEIPDataCallback(self, str_data = ""):
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
					#calling the reqiured Command Type handler
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
			else:
				pass

	def OnVideoProcessingComplete(self, videoFile):
		if '.mp4' in videoFile:
			self.LiveCmdHandler.UploadVideo(videoFile)
		else:
			pass

	def Process(self):
		if self.__LedDetector__.isProcessingvideo():
			self.__LedDetector__.ProcessVideoFrame()

		elif self.__LedDetector__.inQueue():
			#processing video queue to find leds
			self.__LedDetector__.Process()

		self.__mqttClient__.Process()
		self.LiveCmdHandler.Process()
