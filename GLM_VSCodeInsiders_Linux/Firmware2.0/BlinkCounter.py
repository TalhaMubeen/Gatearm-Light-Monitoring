import numpy as np
import cv2
import time
from RepeatedTimer import PeriodicTimer
from Diagnostics import LocalLogger
import pickle

class BlinkCounter(object):

    def make_lut_u(self):
        return np.array([[[i,255-i,0] for i in range(256)]],dtype=np.uint8)

    def make_lut_v(self):
        return np.array([[[0,255-i,i] for i in range(256)]],dtype=np.uint8)

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__
    
    def __init__(self, LedLocationFilePath, configs):
        try:
            self.logger     = LocalLogger('GLM_Diagnostics', self.whoami(), configs)
            self.SetPreviousLedLocations(LedLocationFilePath)
            
            self.__TOTAL_NUMBER_OF_LEDS__ = 3
            self.__LedsCentrePointList__  = list()
            self.__LastStateofLedAtPos__  = dict()
            self.__LedLocations__         = []
            self.__LedBlinkCounter__      = []
            self.__VerdictTimer__         = PeriodicTimer(10, self.GenerateVerdict)
        except:
            self.logger.log(self.logger.ERROR,'Failed to Init ' +  self.whoami())
            raise ValueError()


    def GetYUVImage(self, image):
        yuvImage = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        yuvImage = cv2.GaussianBlur(yuvImage, (5, 5), 0)
        #Separating the y, cb and cr channels     
        y,u,v    = cv2.split(yuvImage)
        del yuvImage

        lut_u, lut_v = self.make_lut_u(), self.make_lut_v()
        u = cv2.cvtColor(u, cv2.COLOR_GRAY2BGR)
        v = cv2.cvtColor(v, cv2.COLOR_GRAY2BGR)

        v_mapped = cv2.LUT(v, lut_v)
        u_mapped = cv2.LUT(u, lut_u)
        del lut_u
        del lut_v
        del u
        del v
        # Convert back to BGR so we can apply the LUT and stack the images
        y = cv2.cvtColor(y, cv2.COLOR_GRAY2BGR)

        return y, u_mapped, v_mapped
    
    def GetLastLedBlinkState(self, image):
        ret = False
        if len(self.__LedLocations__) < 1:
            return ret, self.__LedLocations__

        YImage, _ , v_mapped = self.GetYUVImage(image)
        del image
        #YImage += 50
        Low_Luminance = np.array([130,0,130])
        high_Luminance = np.array([255,255,255])
        LuminanceMask = cv2.inRange(YImage, Low_Luminance, high_Luminance)
        del YImage
        del Low_Luminance
        del high_Luminance
        LuminanceMask = cv2.dilate(LuminanceMask, None, iterations=4)

        for  i in range(len(self.__LedLocations__)):
            (rectX, rectY), radius =  self.__LedLocations__[i][0] , self.__LedLocations__[i][1]

            cropped = v_mapped[rectY-10:(rectY+2*radius), rectX-10:int(rectX+2*radius)-10]
            cropped[:,:,2] += 50
            cropY   = LuminanceMask[rectY-10:(rectY+2*radius), rectX-10:int(rectX+2*radius)-10]

            if len(self.__LedLocations__[i]) == 3:
                self.__LedLocations__[i].append(cropped)
                continue
            else:
                prev = self.__LedLocations__[i][3]
                dif = cv2.subtract(cropped, prev)
                #Calculating Mean Square Difference bw current and prev frame                
                err = np.sum((cropped.astype("float") - prev.astype("float")) ** 2)
                err /= float(prev.shape[0] * prev.shape[1])
                self.__LedLocations__[i][3] = []
                self.__LedLocations__[i][3] = cropped
                del cropped
                del prev
                if err < 30:
                     continue

                count = cv2.countNonZero(dif[:,:,1])
                countb = cv2.countNonZero(dif[:,:,2])
                del dif
                count2 = cv2.countNonZero(cropY)
                del cropY

                if count2+countb > 700:
                    ret = True
                    self.__LedLocations__[i][2] = True
                    continue
                elif count2+countb <= 400 or count2 == 0:
                    ret = True
                    self.__LedLocations__[i][2] = False
                    continue

                
                elif count < 500:
                    ret = True
                    self.__LedLocations__[i][2] = True
                    continue
                else:
                    ret = True
                    self.__LedLocations__[i][2] = False
                    continue
        del v_mapped
        del LuminanceMask
        return ret, self.__LedLocations__

    def SetPreviousLedLocations(self, filepath):
        self.__LedBlinkCounter__ = []
        xyr = {}
        f = open(filepath, 'rb')
        obj = pickle.load(f)
        f.close()
        if len(obj) == 3:
            self.__LedLocations__ = obj.copy()
            for  i in range(len(self.__LedLocations__)):
                data = [i, [False, 0]]
                self.__LedBlinkCounter__.append(data)
                ((x, y), radius), b = cv2.minEnclosingCircle(self.__LedLocations__[i][0][4]) , False
                if i > 0:
                    swapped = False
                    for j in range(len(xyr)):
                        y2 = xyr[j][0][1]
                        if y < y2:
                            temp = xyr[j]
                            xyr[j] = [(int(x), int(y)), int(radius), b]
                            xyr[len(xyr)] = temp
                            swapped = True

                if i == 0 or swapped == False:
                    xyr[len(xyr)] = [(int(x), int(y)), int(radius), b]

            self.__LedLocations__.clear()
            self.__LedLocations__ = xyr
        else:
            pass
        return xyr

    def IncrementLightCounter(self, lightId, isLightOn):
        addToArray = True
        count  = 0
        blinkcounterArray = [lightId, [isLightOn, int(isLightOn)]]
        ledindex , statusandBlinkCount = blinkcounterArray
        
        for  i in range(len(self.__LedBlinkCounter__)):
            id = self.__LedBlinkCounter__[i][0]
            if id == lightId:
                addToArray = False
                prevcounterArr = self.__LedBlinkCounter__[i][1]
                prevLightState = prevcounterArr[0]
                count = self.__LedBlinkCounter__[i][1][1]
                if prevLightState != isLightOn:
                    if prevLightState == False:
                        if i != 0:
                            self.__LedBlinkCounter__[i][1][1] += 1
                        else:
                            if self.__LedBlinkCounter__[i][1][1] == 0:
                                self.__LedBlinkCounter__[i][1][1] = 1
                            else:
                                 pass
                    self.__LedBlinkCounter__[i][1][0] = isLightOn


        if addToArray == True:
            self.__LedBlinkCounter__.append(blinkcounterArray)
            count = 1
        return count

    def ResetBlinkcounters(self):
        self.__LedBlinkCounter__.clear()

    def GetBlinkCounters(self):
        return self.__LedBlinkCounter__

    def GenerateVerdict(self):
        for  i in range(len(self.__LedBlinkCounter__)):
            print ('Blink Count of Led => ' + str (i) + ' : ' + str (self.__LedBlinkCounter__[i][1][1])) 
        self.__LedBlinkCounter__.clear()
        self._sameValue = 0
        self.__VerdictTimer__.stop()
   