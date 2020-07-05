#from __future__ import print_function
#from __future__ import division
from imutils import contours
from skimage import measure
from pylab import *
import imutils
import cv2
import numpy as np
from numpy import mean
import argparse
import os, sys
import LedBlinkCounter as BCounter
#from PIL import Image, ImageStat
#from collections import namedtuple
blinkCounter = BCounter.BlinkCounter()
#from HoughLines import colorRange

#import matplotlib.pyplot as plt
#import cvlib as cv
#from   cvlib.object_detection import draw_bbox


def get_part_of_day(hour):
    return (
        "morning" if 5 <= hour <= 11
        else
        "afternoon" if 12 <= hour <= 17
        else
        "evening" if 18 <= hour <= 20
        else
        "night"
    )

def StaticVideoSource(videoFile):
    capture = cv2.VideoCapture(videoFile)
    i = 0;
    blinkCounter.SetPreviousLedLocations('GLM1.pckl')  #Load leds location here
    frameCount  = 0
    previousLoc = []
    newFrame = False;
    foundOneLED = [False,False,False]

    #count = 100
    #while count != 0:
    #     ret1, frame1 = capture.read()
    #     count -=1

    while(1):
        ret1, frame1 = capture.read()
        if ret1 == False:
          capture.release()
          break
        if ret1 == True:
            cropped = frame1.copy()
            image2 = cropped[400:900, 450:730]
            #image2 = cropped[500:900, 400:680]

            orgnlFrame = image2.copy()
            ret, LightLoc = blinkCounter.GetLastLedBlinkState(image2)

            #if ret == False or len(LightLoc) < 3 or frameCount == 5:
            #    frameCount = 0
            #    ret, cnts = YUV_LedDetection(image2)
            #    newFrame = True;                                                    
            #    CheckImageContours(cnts)
            #frameCount += 1

            for  i in range(len(LightLoc)):
                #blinkCounter.StoreLedLocations(); #Store here
                (cX, cY), radius, ret =  LightLoc[i][0] , LightLoc[i][1], LightLoc[i][2]
                if ret == False and not foundOneLED[i]:
                    continue

                else:
                    count = blinkCounter.IncrementLightCounter(i, ret)
                    yloc = 60 + (30 * i)
                    if ret == True:
                       # outcircle = cv2.circle(orgnlFrame, (int(cX), int(cY)), radius,(0, 255, 0), 2)
                        foundOneLED[i] = True
                        cv2.putText(frame1, 'LIGHT ' + str(i+1) + ' : '+ str(count), ( 5  , yloc),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        #outcircle = cv2.circle(orgnlFrame, (int(cX), int(cY)), radius,(0, 0, 255), 2)
                        cv2.putText(frame1, 'LIGHT ' + str(i+1) + ' : '+ str(count), ( 5  , yloc),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                    blinkCounter.IncrementLightCounter(i, ret)

            newFrame = False        

            #frame1[500:900, 400:680] = orgnlFrame[0:, 0:]
            frame1[400:900, 450:730] = orgnlFrame[0:, 0:]
            cv2.imshow('Detection Frame',frame1)
            cv2.waitKey(0)
 

def CheckImageContours(cnts):
    if cnts == None:
        return

    if len(cnts) > 0 and len(cnts) <= 5:
        cnts = contours.sort_contours(cnts)[0]
        for (i, c) in enumerate(cnts):
            # draw the bright spot on the image
            (x, y, w, h) = cv2.boundingRect(c)
            if h > 8 and h < 30:
                blinkCounter.SetLedsCentreLocations([x,y,w,h,c].copy())
            else: 
               print ('Small CNT ignored')
    else:
        print('No Cnts Found')


def StaticFGBG_Substraction(baseImgPath , fgImgPath):

    baseImg = cv2.imread(baseImgPath)
    fgImg   = cv2.imread(fgImgPath)

    fgbgSubsImg = cv2.absdiff(baseImg,fgImg)

    if np.any(fgbgSubsImg):
        return True, fgbgSubsImg, fgImg

    else:
        return False, fgbgSubsImg, fgImg


def YUV_LedDetection(image):
    orignalImg = image.copy()
    imageHeight = image.shape[0]
    imageWidth  = image.shape[1]

    grayimg =cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
    y, u_mapped, v_mapped = blinkCounter.GetYUVImage(image)

    avgBrightness = int(mean(y))
    print('Brightnesss =' + str(avgBrightness))
    isDay = False
    DayLightLow = np.array([0,0,105])
    DayLightHigh = np.array([0,113,255])

    LowRedBright  = np.array([0,0,180])
    HighRedBright = np.array([0,105,255])

    HighRedBrightest = np.array([0,110,255])
    HighRedAbove100 = np.array([0,114,255])

    LowRedDark  = np.array([0,0,230])
    HighRedDark = np.array([0,80,255])

    redColorMask = []
    if avgBrightness > 30 and avgBrightness < 50:
        v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 30
        cv2.imshow ('v_mapped',v_mapped)

        redColorMask = cv2.inRange(v_mapped, LowRedBright, HighRedBright)
        cv2.imshow ('redColorMask1',redColorMask)
        redColorMask[10:60, 30:imageWidth - 40] = cv2.dilate(redColorMask[10:60, 30:imageWidth - 40] , None, iterations=6)

    elif avgBrightness >= 50 and avgBrightness < 80:
        v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 50
        cv2.imshow ('v_mapped',v_mapped)

        redColorMask = cv2.inRange(v_mapped, LowRedBright, HighRedBrightest)
        cv2.imshow ('redColorMask2',redColorMask)
        redColorMask[10:60, 30:imageWidth - 40] = cv2.dilate(redColorMask[10:60, 30:imageWidth - 40] , None, iterations=6)

    elif  avgBrightness >= 80 and avgBrightness < 100:
        y[10:120, 30: image.shape[1] - 40] += 30
        v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 50
        cv2.imshow ('v_mapped',v_mapped)

        redColorMask = cv2.inRange(v_mapped, LowRedBright, HighRedAbove100)
        cv2.imshow ('redColorMask2',redColorMask)
        redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] = cv2.dilate(redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] , None, iterations=6)
    
    elif avgBrightness >= 100 :
        isDay = True
        y[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 50

        cv2.imshow ('brightness',y)
#        colorRange(v_mapped)
        cv2.imshow ('v_mapped',v_mapped)
        redColorMask = cv2.inRange(v_mapped, DayLightLow, DayLightHigh)
        cv2.imshow ('redColorMask3',redColorMask)
       
        #redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] = cv2.dilate(redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] , None, iterations=6)
        #cv2.imshow ('redColorMask32',redColorMask)
    else:
        #v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 30
        cv2.imshow ('v_mapped',v_mapped)

        redColorMask = cv2.inRange(v_mapped, LowRedDark, HighRedDark)
        cv2.imshow ('redColorMask4',redColorMask)
        redColorMask[10:60, 30:imageWidth - 40] = cv2.dilate(redColorMask[10:60, 30:imageWidth - 40] , None, iterations=6)

    LuminanceMask = CalculateLuminance(y, isDay)

    Mask = cv2.bitwise_and(LuminanceMask, redColorMask)
    Mask = cv2.dilate(Mask, None, iterations=2)

    redCnts = blinkCounter.FindCountoursInMaskedImage(LuminanceMask, 100)
    #LuminanceCnts = FindCountoursInMaskedImage(LuminanceMask, 10)
    #finalCnts = FindNearByCountours(redCnts, LuminanceCnts, grayimg, cntDst)
    cv2.imshow ('Mask',Mask) 
    cv2.imshow ('image',image) 
    cv2.imshow ('redColorMask',redColorMask) 
    cv2.imshow ('LuminanceMask',LuminanceMask) 

    return True, redCnts

def CalculateLuminance(image, isDay):
    
    if isDay == True:
       Low_Luminance = np.array([0,0,0])
       high_Luminance = np.array([255,72,255])
    else:
        Low_Luminance = np.array([220,0,224])
        high_Luminance = np.array([255,255,255])


    LuminanceMask = cv2.inRange(image, Low_Luminance, high_Luminance)
    LuminanceMask = cv2.dilate(LuminanceMask, None, iterations=4)
    return LuminanceMask

def FindNearByCountours(RedCnts, Lumancnts, image, contDist):
    cntImg = image.copy()
    cntImg[0: , 0:] = 0
    if len(RedCnts) > 0 and len(RedCnts) < 4 and len(Lumancnts) > 0:
        RedCnts = contours.sort_contours(RedCnts)[0]
        Lumancnts = contours.sort_contours(Lumancnts)[0]
        Hcnts = RedCnts
        Lcnts = Lumancnts

        for (i, c1) in enumerate(Hcnts):
            (x1, y1, w1, h1) = cv2.boundingRect(c1)
            if int(h1) < 8 :
                continue
            for (j, c2) in enumerate(Lcnts):
                (x2, y2, w2, h2) = cv2.boundingRect(c2)
                if int(h2) < 8 :
                    continue
                dx2 = (x2-x1)**2
                dy2 = (y2-y1)**2
                distance = math.sqrt(dx2+dy2)

                if distance < contDist:
                    cntImg[y1:y1+20, x1+10:x1+20] = 255
                    cntImg[y2:y2+20, x2+10:x2+20] = 255
                    cntImg = cv2.dilate(cntImg, None, iterations=3)
                    cv2.imshow('cntImg', cntImg)


    cnts = cv2.findContours(cntImg.copy(), cv2.RETR_EXTERNAL,
	    cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    return cnts

if __name__ == '__main__':  

    files = os.listdir("D:/Work/Python1/Test/")
    for file in files:
        if ".mp4" in file:
            #pklfile = file.split('_')[0]
            #obj = LedDetector(pklfile)
            StaticVideoSource("D:/Work/Python1/Test/" + file)
            cv2.waitKey(0)

    #print (cv2.__version__)
    #StaticVideoSource('Test.mp4')
