from Diagnostics import LocalLogger
import MQTTDataProcessor
import json
from HttpClient import HttpClient
import netifaces as ni
import os

class LiveCommandHandler(object):

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self, configs ={}, mqttDataProcessor = MQTTDataProcessor):
        try:
            self.__logger__     = LocalLogger('GLM_Diagnostics', self.whoami(), configs)
            self.configurations = configs
            self.__httpClient__ = HttpClient(configs)
            self.__pi_camera__ = None
            self.__mqttDataProcessor__ = mqttDataProcessor
            self.__httpClient__.RegisterUploadFileResponseCallback(self.OnHttpImageUploadComplete)
        except:
            self.__logger__.log(self.logger.ERROR,'Failed to Init ' +  self.whoami())
            raise ValueError()

    def InitVideoRecorder(self, recorder):
        self.__pi_camera__ = recorder

    def LiveCommandHandler(self, channelData):
        if channelData.get("Action") != None:

            if channelData['Action'] == 'CaptureImage':
                #Capture and Upload Image here
                path1 = self.__pi_camera__.capture_image()
            
                if os.path.isfile(path1) == True:
                     self.__httpClient__.PostImages(path1)
                else:
                    self.__logger__.log(self.logger.ERROR,'File does not exists' + path1)

            elif channelData['Action'] == 'Ping':
                data = self.Get_local_IPDetails()
                retData = self.__mqttDataProcessor__.GetPublishData(data, 'live', channelData['Action'])
                self.__mqttDataProcessor__.PublishDataOverMQTT(retData)

            elif channelData['Action'] == 'StreamOverIP':
                self.__pi_camera__.StartStreamOverIP();

            elif channelData['Action'] == 'StopStream':
                self.__pi_camera__.StopStream();
            
            elif channelData["Action"] == 'RecordVideo' and channelData.get("Duration") != None:
                duration = channelData['Duration']
                self.__pi_camera__.start_video_recording(duration=duration);

            elif channelData['Action'] == 'Reset':
                #reboot system after 10 - seconds
                pass

        return

    def Get_local_IPDetails(self):
            #getting ip addresses of specific interfaces
        data = {}
        data['eth0']  = self.__get_ip_address__('eth0')
        data['wlan0'] = self.__get_ip_address__('wlan0')
        data['tun0']  = self.__get_ip_address__('tun0')
        data['ppp0']  = self.__get_ip_address__('ppp0')
        #making json object to publish over live / status channel

        return data

    def __get_ip_address__(self, ifname):
        try :
            ni.ifaddresses(ifname)
            ip = ni.ifaddresses(ifname)[ni.AF_INET][0]['addr']
        except:
            self.__logger__.log(self.__logger__.ERROR, 'IP not found for iface '+ ifname) 
            ip = ''   
        return ip

    def OnHttpImageUploadComplete(self, ret, isUploaded):
        data = {}
        data['HttpReturnCode'] = int(ret)
        data['IsUploaded']     =   bool(isUploaded)
        retData = self.__mqttDataProcessor__.GetPublishData(data, 'live', 'CaptureImage')
        self.__mqttDataProcessor__.PublishDataOverMQTT(retData)

    def Process(self):
        self.__httpClient__.Process()
        self.__pi_camera__.Process()
        pass
