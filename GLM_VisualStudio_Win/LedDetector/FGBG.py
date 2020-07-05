import cv2
import numpy as np
from LedBlinkCounter import BlinkCounter
import time
import os

class LedDetector(object):
    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__
    
    def __init__(self, LedLocationFilePath):
        try:
            #self.__logger__        = LocalLogger('GLM_Diagnostics', self.whoami(), configs)
            self.__blinkCounter__   = BlinkCounter(LedLocationFilePath)
            self.LedLocFile         = LedLocationFilePath
        except:
            raise ValueError()
        
    def StaticVideoSource(self, videoFile):
        capture = cv2.VideoCapture(videoFile)
        
        frameCount  = 0
        previousLoc = []
        newFrame = False;
        ret1 = True
        outputFile = videoFile+'_Output.mp4'
        self.__blinkCounter__.SetPreviousLedLocations(self.LedLocFile)
        #fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        #out = cv2.VideoWriter(outputFile,0x7634706d, 6, (1024,1024))
        
        foundOneLED = {}
        foundOneLED[0] = False
        foundOneLED[1] = False
        foundOneLED[2] = False
        while(ret1):
            ret1, frame1 = capture.read()
            if ret1 == True :
                image2 = frame1[400:900, 450:730]
                orgnlFrame = image2.copy()
                ret, LightLoc = self.__blinkCounter__.GetLastLedBlinkState(image2)
       
                for  i in range(len(LightLoc)):
                    (cX, cY), radius, ret =  LightLoc[i][0] , LightLoc[i][1], LightLoc[i][2]
                    if ret == False and not foundOneLED[i]:
                        continue
                    else: 
                        foundOneLED[i] = True
                        if int(radius - 20) > 0:
                            radius = int(radius -20)
                        else:
                            radius = int(radius)
                        if ret == True:
                            outcircle = cv2.circle(orgnlFrame, (cX, cY+5), radius +3,(0, 255, 0), 2)
                            cv2.putText(orgnlFrame,"ON", (cX - 60 ,cY + 35),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        elif i > 0:
                            outcircle = cv2.circle(orgnlFrame, (cX, cY+5), radius+3,(0, 0, 255), 2)
                            cv2.putText(orgnlFrame,"OFF", (cX -60 ,cY + 35),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                        count = self.__blinkCounter__.IncrementLightCounter(i, ret)
                        if count > 0:
                            cv2.putText(orgnlFrame,str(count), (cX - 64 , cY + 12),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                frame1[400:900, 450:730] = orgnlFrame[0:, 0:] 

                cv2.imshow('Detection Frame',frame1)
                cv2.waitKey(1)
                #time.sleep(0.1)
                #out.write(frame1)
         
        #out.release()
        return outputFile

if __name__ == '__main__':  
    #print (cv2.__version__)
    #obj = LedDetector('GLM02'+'.pckl')
    #obj.StaticVideoSource('Test6.mp4')

    files = os.listdir("D:/Work/Python1/Test/")
    for file in files:
        pklfile = file.split('_')[0]
        obj = LedDetector(pklfile)
        obj.StaticVideoSource("D:/Work/Python1/Test/" + file)