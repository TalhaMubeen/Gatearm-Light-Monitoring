import http.client as client
from io import BytesIO 
import os
import requests
from multiprocessing import Process
from  Diagnostics import LocalLogger
import datetime

class HttpClient(object):


    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __generate_complete_url__(self, url = "", api = ""):
        if len(api) > 0:
            url = url.replace('#', api)
            url = url +'?glmid='+self.MYID + '&timestamp='
            self.logger.log(self.logger.INFO, api +' upload url = '+ url)
        else:
             self.logger.log(self.logger.ERROR, 'Url API can not be empty')
        return url

    def __init__(self, configs):
        try:
            self.logger         = LocalLogger('GLM_Diagnostics', self.whoami(),configs)
            self.MYID = configs['GLM']['MY_ID']
            generalUploadURL = configs['GLM']['HTTP']['FILE_UPLOAD_URL']

            self.ImageUploadUrl = self.__generate_complete_url__(generalUploadURL, 'image')
            self.VideoUploadURL = self.__generate_complete_url__(generalUploadURL, 'video')

            self.httpClient     = client
            self.urlLookup      = {}
            self.byteObj        = BytesIO()
            self.messageCount   = 0
            self.Jobs           = []
            self.httpFileUploadCallback = None

        except:
            self.logger.log(self.logger.ERROR,'Failed to Init ' +  self.whoami())
            raise ValueError()

    def RegisterDownloadFileResponseCallback(self, callback):
        """
        Register Download file Response Callback
        """
        self.httpDownloadFileCallback = callback

    def RegisterUploadFileResponseCallback(self, callback):
        """
        Register File Upload response callback
        """
        self.httpFileUploadCallback = callback

    def AppendTimeStampToUrl(self, url):
        url = url + str(int(datetime.datetime.utcnow().timestamp()))
        return url

    def __ExecuteParallel__(self, fileType, url, filepath, uploadtype):
        with open(filepath, 'rb') as path:
            name = self.MYID + os.path.basename(filepath)
            if fileType == 'videofile':
                files = {fileType : (name, path, 'video/mp4',{'Expires': '0'})}
                
            elif fileType == 'imagefile':    
                files = {fileType : (name, path, 'image/jpeg',{'Expires': '0'})}

            with requests.Session() as session:
                if uploadtype == 'post':
                    url = self.AppendTimeStampToUrl(url)
                    try:
                        ret = session.post(url ,files = files)
                        
                        if int(ret.status_code) == 200:
                            os.remove(filepath)
                            self.logger.log(self.logger.INFO, fileType +' uplaoded successfully ')
                            self.httpFileUploadCallback(ret.status_code, True)
                        else:
                            self.logger.log(self.logger.ERROR,'Failed to Upload '+ fileType +' , HTTP Return Code '+ str(ret.status_code))
                            self.httpFileUploadCallback(ret.status_code, False)
                    except:
                        self.logger.log(self.logger.ERROR,'Failed to Connect with HTTP Server')
                else:
                    self.logger.log(self.logger.ERROR,'Request Type not found, Type = ' + type)

    def PostImages(self, imagePath):
        self.logger.log(self.logger.INFO,'Requesting to Upload Image : '+ imagePath)
        p = Process(target=self.__ExecuteParallel__, args=('imagefile', self.ImageUploadUrl, imagePath, 'post' ))
        self.Jobs.append(p)
        
    def PostVideo(self, videoPath):
        self.logger.log(self.logger.INFO,'Requesting to Upload Video : '+ videoPath)
        p = Process(target=self.__ExecuteParallel__, args=('videofile', self.VideoUploadURL, videoPath, 'post'))
        self.Jobs.append(p)
        
    def Process(self):
        for process in self.Jobs:
            if process.exitcode == None and not process.is_alive():
                process.start()

                
