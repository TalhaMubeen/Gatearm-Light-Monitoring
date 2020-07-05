from imutils import contours
import cv2
import numpy as np
import LedBlinkCounter as BCounter
blinkCounter = BCounter.BlinkCounter()

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


class LedDetector(object):

    def StaticVideoSource(self, videoFile):
        capture = cv2.VideoCapture(videoFile + '.mp4')
        i = 0;
        frameCount  = 0
        previousLoc = []
        newFrame = False;
        ret1 = True
        out = cv2.VideoWriter(videoFile+'_Output.mp4',cv2.VideoWriter_fourcc('M','P','4','V'), 6, (1024,1024))
        #count1 = 1

        blinkCounter.SetPrevLoc()
        i = 18
        while i > 0:
            ret1, frame1 = capture.read()
            out.write(frame1)
            i -=1
        while(ret1):
            #time.sleep(0.15)
            ret1, frame1 = capture.read()

            if ret1 == True :
                ##cv2.imshow('Orignal', frame1)
                #(h, w) = frame1.shape[:2]
                #center = (w / 2, h / 2)
                #M = cv2.getRotationMatrix2D(center, 270, 1.0)
                #rotated = cv2.warpAffine(frame1, M, (h, w))
                ##cv2.imshow('rotated', rotated)
                #cropped = rotated.copy()
                image2 = frame1[400:900, 450:730]

                ##cv2.imshow('croped', image2)
                ##cv2.waitKey(0)
                orgnlFrame = image2.copy()
                ret, LightLoc = blinkCounter.GetLastLedBlinkState(image2)
                previousLoc = LightLoc.copy()
                locUpdated = False
                if ret == False or len(previousLoc) < 3 :#or frameCount == 2:
                    frameCount = 0
                    #ret, cnts = DetectLeds2(frame1 , True)
                    ret, cnts = self.YUV_LedDetection(image2)
                    newFrame = True;
                    locUpdated = self.CheckImageContours(cnts)
                #else:
                    #cv2.destroyAllWindows()
                #frameCount += 1
                #elif count1 == 1:
                #    count1 = 0

                if locUpdated:
                    continue

                for  i in range(len(previousLoc)):
                    ret, location = previousLoc[i][0]
                    x,y,w,h,c = location
                    ((cX, cY), radius) = cv2.minEnclosingCircle(c)
                    cX = int(cX)
                    cY = int(cY)
                    radius = int(radius)
                    if int(radius - 20) > 0:
                        radius = int(radius -20)
                    else:
                        radius = int(radius)
                    if ret == True:
                        outcircle = cv2.circle(orgnlFrame, (cX, cY), radius,(0, 255, 0), 2)
                        cv2.putText(orgnlFrame,"ON", (cX -20 ,cY - 23),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        outcircle = cv2.circle(orgnlFrame, (int(cX), int(cY)), radius,(0, 0, 255), 2)
                        cv2.putText(orgnlFrame,"OFF", (cX -25 ,cY - 23),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                    count = blinkCounter.IncrementLightCounter(i, ret)
                    if count > 0:
                        cv2.putText(orgnlFrame,str(count), (cX - 70, cY + 12),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                newFrame = False        

                frame1[400:900, 450:730] = orgnlFrame[0:, 0:]
                #cv2.imshow('Detection Frame',frame1)
                out.write(frame1)
                #cv2.waitKey(0)

        out.release()
        #cv2.destroyAllWindows()
        #cv2.waitKey(0)
 
    def CheckImageContours(self,cnts):
        if cnts == None:
            return
        locUpdated = False
        if len(cnts) > 0 and len(cnts) <= 5:
            cnts = contours.sort_contours(cnts)[0]
            for (i, c) in enumerate(cnts):
                # draw the bright spot on the image
                (x, y, w, h) = cv2.boundingRect(c)
                if h > 8 and h < 30:
                   locUpdated = blinkCounter.SetLedsCentreLocations([x,y,w,h,c].copy())

        return locUpdated

    def YUV_LedDetection(self,image):
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

        LowRedDark  = np.array([0,0,180])
        HighRedDark = np.array([0,100,255])

        redColorMask = []
        if avgBrightness > 30 and avgBrightness < 50:
            v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 30
            #cv2.imshow ('v_mapped',v_mapped)

            redColorMask = cv2.inRange(v_mapped, LowRedBright, HighRedBright)
            #cv2.imshow ('redColorMask1',redColorMask)
            redColorMask[10:60, 30:imageWidth - 40] = cv2.dilate(redColorMask[10:60, 30:imageWidth - 40] , None, iterations=6)

        elif avgBrightness >= 50 and avgBrightness < 80:
            v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 50
            #cv2.imshow ('v_mapped',v_mapped)

            redColorMask = cv2.inRange(v_mapped, LowRedBright, HighRedBrightest)
            #cv2.imshow ('redColorMask2',redColorMask)
            redColorMask[10:60, 30:imageWidth - 40] = cv2.dilate(redColorMask[10:60, 30:imageWidth - 40] , None, iterations=6)

        elif  avgBrightness >= 80 and avgBrightness < 100:
            isDay = True
            y[10:120, 30: image.shape[1] - 40] += 50
            v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 50
            #cv2.imshow ('v_mapped',v_mapped)
            #cv2.imshow ('y',y)

            redColorMask = cv2.inRange(v_mapped, LowRedBright, HighRedAbove100)
            #cv2.imshow ('redColorMask2',redColorMask)
            #redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] = cv2.dilate(redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] , None, iterations=6)
    
        elif avgBrightness >= 100 :
            isDay = True
            y[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 50

            #cv2.imshow ('brightness',y)
        
            #cv2.imshow ('v_mapped',v_mapped)
            redColorMask = cv2.inRange(v_mapped, DayLightLow, DayLightHigh)
            #cv2.imshow ('redColorMask3',redColorMask)
       
            #redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] = cv2.dilate(redColorMask[10:int(imageHeight/2), 30:imageWidth - 40] , None, iterations=6)
            ##cv2.imshow ('redColorMask32',redColorMask)
        else:
            v_mapped[10:int(imageHeight/2), 10:imageWidth - 10][:,:,2] += 30
            #cv2.imshow ('v_mapped',v_mapped)

            redColorMask = cv2.inRange(v_mapped, LowRedDark, HighRedDark)
            #cv2.imshow ('redColorMask4',redColorMask)
            redColorMask[10:60, 30:imageWidth - 40] = cv2.dilate(redColorMask[10:60, 30:imageWidth - 40] , None, iterations=3)
            #cv2.imshow ('redColorMask41',redColorMask)

        LuminanceMask = self.CalculateLuminance(y, isDay)
        #colorRange(v_mapped)
        kernel = np.ones((5,5),np.uint8)
        opening = cv2.morphologyEx(redColorMask, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        #cv2.imshow ('closing',closing)
        #cv2.imshow ('opening',opening)
    
        if isDay == False:
            closing = cv2.dilate(closing, None, iterations=4)
            andMask = cv2.bitwise_and(LuminanceMask, closing)
        else:
            closing = cv2.dilate(closing, None, iterations=2)

        LuminanceMask = cv2.dilate(LuminanceMask, None, iterations=4)
        #Mask = cv2.bitwise_or(LuminanceMask, andMask)
        ##cv2.imshow ('Mask1',Mask)
        ##cv2.waitKey(0)
        #Mask = cv2.dilate(Mask, None, iterations=2)
        Mask = LuminanceMask
        redCnts = blinkCounter.FindCountoursInMaskedImage(Mask, 100)
        #LuminanceCnts = FindCountoursInMaskedImage(LuminanceMask, 10)
        #finalCnts = FindNearByCountours(redCnts, LuminanceCnts, grayimg, cntDst)
        #cv2.imshow ('Mask',Mask) 
        #cv2.imshow ('image',image) 
        #cv2.imshow ('redColorMask',redColorMask) 
        #cv2.imshow ('LuminanceMask',LuminanceMask) 
        #cv2.waitKey(0)
        return True, redCnts

    def CalculateLuminance(self,image, isDay):
    
        if isDay == True:
           Low_Luminance = np.array([0,0,0])
           high_Luminance = np.array([255,72,255])
        else:
            Low_Luminance = np.array([220,0,224])
            high_Luminance = np.array([255,255,255])


        LuminanceMask = cv2.inRange(image, Low_Luminance, high_Luminance)
        LuminanceMask = cv2.erode(LuminanceMask, None, iterations=2)
        LuminanceMask = cv2.dilate(LuminanceMask, None, iterations=4)
        return LuminanceMask

if __name__ == '__main__':  
     obj = LedDetector()
     obj.StaticVideoSource('GLM01Night')