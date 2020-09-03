import os, sys
import cv2
import numpy as np
import time
import calendar

def StaticVideoSource(videoFile , pckl):
    capture = cv2.VideoCapture(videoFile)
    count = 5
    firstFrame = True
    while(1):
        ret1, frame1 = capture.read()
        if ret1 == False:
          capture.release()
          break
        if ret1 == True:
            cropped = frame1.copy()

            if pckl == "GLM01":
                gatearm = cropped[510:850, 540:730]
                track = cropped[400:800, 750:]
            else:
                gatearm = cropped[490:900, 430:630]
                track = cropped[400:800, 630:1000]
            ts = calendar.timegm(time.gmtime()) 

            if count == 5 :
                cv2.imwrite("../Result/Track" + str(ts) + ".jpg", track) 
                cv2.imwrite("../Result/Gatewarm" + str(ts) + ".jpg", gatearm) 
            count -= 0
            if count <= 0:
                count = 5

if __name__ == '__main__':  

    files = os.listdir("../Test/")
    for file in files:
        if ".mp4" in file:
            pklfile = file.split('_')[0]
            #obj = LedDetector(pklfile)
            StaticVideoSource("../Test/" + file, pklfile)
            cv2.waitKey(0)