from numpy import mean
import argparse
import os, sys
import cv2
import numpy as np
from matplotlib import pyplot as plt



def StaticVideoSource(videoFile):
    capture = cv2.VideoCapture(videoFile)
    fgbg = cv2.createBackgroundSubtractorMOG2()
    fast = cv2.FastFeatureDetector()
    fast = cv2.FastFeatureDetector_create(threshold=25)
    fgbg = cv2.createBackgroundSubtractorMOG2(history=5,varThreshold=1,detectShadows=False)
    i = 0
    while(i < 3):
        if i == 0 :
            ret1, frame = capture.read()
            frame = frame [10:700,700:]
        i+=1
        if i == 3 :
            i = 0
        
        if ret1 == False:
          capture.release()
          break
        if ret1 == True:     
            #Converting the image to grayscale.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Extract the foreground
            edges_foreground = cv2.bilateralFilter(gray, 3, 75, 75)
            foreground = fgbg.apply(edges_foreground)
    
            # Smooth out to get the moving area
            kernel = np.ones((50,50),np.uint8)
            foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel)

            # Applying static edge extraction
            edges_foreground = cv2.bilateralFilter(gray, 9, 75, 75)
            edges_filtered = cv2.Canny(edges_foreground, 60, 120)

            # Crop off the edges out of the moving area
            cropped = (foreground // 255) * edges_filtered

            # Stacking the images to print them together for comparison
            images = np.hstack((gray, edges_filtered, cropped))

            # Display the resulting frame
            cv2.imshow('Frame', images)
            cv2.waitKey(0)



if __name__ == '__main__':  

    files = os.listdir("D:/Work/GLM/GLM_VisualStudio_Win/Test/")
    for file in files:
        if ".mp4" in file:
            #pklfile = file.split('_')[0]
            #obj = LedDetector(pklfile)
            StaticVideoSource("D:/Work/GLM/GLM_VisualStudio_Win/Test/" + file)
            cv2.waitKey(0)
