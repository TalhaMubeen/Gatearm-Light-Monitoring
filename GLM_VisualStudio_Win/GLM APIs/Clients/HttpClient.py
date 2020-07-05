import http.client as client
import pycurl
from io import BytesIO 
import os
import requests
from multiprocessing import Process

class HttpClient(object):

    def __init__(self):
        self.httpClient = client
        self.curl       = pycurl.Curl()
        self.curl_multi = pycurl.CurlMulti()
        self.curl_multi.handles   = []
        self.httpResponseCallback = None
        self.urlLookup            = {}
        self.byteObj              = BytesIO()
        self.messageCount         = 0

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
        
    def PostImages(self, url, imagePath):

        with open(imagePath, 'rb') as image:
            name = os.path.basename(imagePath)
            files = {'imagefile' : (name, image, 'multipart/form-data',{'Expires': '0'}) }

            with requests.Session() as session:
                ret = session.post(url,files = files)
                self.httpFileUploadCallback(ret)



