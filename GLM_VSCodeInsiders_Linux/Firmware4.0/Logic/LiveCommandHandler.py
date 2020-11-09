import Logic
import netifaces as ni
import os
import json


class LiveCommandHandler(object):

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
		return LiveCommandHandler.__instance__

	def __init__(self, configs):
		try:
			self.__logger__ = Logic.GetLogger().SetAPIName(self.whoami())
			# self.configurations = configs
			# self.__httpClient__ = HttpClient(configs)
			# self.__mqttDataProcessor__ = mqttDataProcessor
			# self.__httpClient__.RegisterUploadFileResponseCallback(self.OnHttpImageUploadComplete)

			# Setting Static Instance
			if LiveCommandHandler.__instance__ is None:
				LiveCommandHandler.__instance__ = self
		except:
			self.__logger__.log(self.__logger__.ERROR, 'Failed to Init ' + self.whoami())
			raise ValueError()
		pass

	def Start(self):
		Logic.GetHTTPClient().RegisterUploadFileResponseCallback(self.OnHttpImageUploadComplete)

	def LiveCommandHandler(self, channelData):
		if channelData.get("Action") is not None:
			if channelData['Action'] == 'CaptureImage':
				# Capture and Upload Image here
				path1 = Logic.GetVideoRecorder().capture_image()
				if os.path.isfile(path1):
					Logic.GetHTTPClient().PostImages(path1)
				else:
					self.__logger__.log(self.__logger__.ERROR, 'File does not exists' + path1)

			elif channelData['Action'] == 'Ping':
				data = self.Get_local_IPDetails()
				retData = Logic.GetMQTTDataProcessor().GetPublishData(data, 'live', channelData['Action'])
				Logic.GetMQTTDataProcessor().PublishDataOverMQTT(retData)

			elif channelData['Action'] == 'StreamOverIP':
				Logic.GetVideoRecorder().StartStreamOverIP()

			elif channelData['Action'] == 'StopStream':
				Logic.GetVideoRecorder().StopStream()

			elif channelData['Action'] == 'UploadVideo':
				pass

			elif channelData["Action"] == 'RecordVideo' and channelData.get("Duration") is not None:
				duration = channelData['Duration']
				Logic.GetVideoRecorder().start_video_recording(duration=duration)

			elif channelData['Action'] == 'Reset':
				pass
			else:
				pass
		else:
			pass

	def Get_local_IPDetails(self):
		# getting ip addresses of specific interfaces
		data = {}
		data['eth0'] = self.__get_ip_address__('eth0')
		data['wlan0'] = self.__get_ip_address__('wlan0')
		data['tun0'] = self.__get_ip_address__('tun0')
		data['ppp0'] = self.__get_ip_address__('ppp0')
		# making json object to publish over live / status channel
		return data

	def __get_ip_address__(self, ifname):
		try:
			ni.ifaddresses(ifname)
			ip = ni.ifaddresses(ifname)[ni.AF_INET][0]['addr']
		except:
			self.__logger__.log(self.__logger__.ERROR, 'IP not found for iface ' + ifname, True)
			ip = ''
		return ip

	def UploadVideo(self, path=''):
		if ".mp4" in path:
			Logic.GetHTTPClient().PostVideo(path)
		else:
			self.__logger__.log(self.__logger__.ERROR, 'Post FILE Path not correct')

	def OnHttpImageUploadComplete(self, ret, isUploaded):
		data = {}
		data['HttpReturnCode'] = int(ret)
		data['IsUploaded'] = bool(isUploaded)
		retData = Logic.GetMQTTDataProcessor().GetPublishData(data, 'live', 'CaptureImage')
		Logic.GetMQTTDataProcessor().PublishDataOverMQTT(retData)
