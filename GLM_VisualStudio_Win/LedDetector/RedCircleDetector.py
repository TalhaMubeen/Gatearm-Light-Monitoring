import os
import cv2
import numpy as np


def detect(filepath, file):

    font = cv2.FONT_HERSHEY_SIMPLEX
    img = cv2.imread(filepath+file)
    img = cv2.medianBlur(img,5)
    #cv2.imshow('Orignal Image', img)
    cimg = img
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0,50,40])
    upper_red1 = np.array([10,255,255])

    lower_red2 = np.array([165,50,40])
    upper_red2 = np.array([179,255,255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    maskr = cv2.add(mask1, mask2)

    #cv2.imshow('maskr', maskr)
    #cv2.waitKey(0)
    size = img.shape

    roi_copy = maskr.copy()
    cnts, hierarchy = cv.findContours(thresh_img.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key = cv.contourArea, reverse = True)[:6] # get largest five contour area
    rects = []
    for c in cnts:
        peri = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.02 * peri, True)
        x, y, w, h = cv.boundingRect(approx)
        #if h >= 15:
            # if height is enough
            # create rectangle for bounding
        rect = (x, y, w, h)
        rects.append(rect)
        cv.rectangle(roi_copy, (x, y), (x+w, y+h), (0, 255, 0), 1);

    return (roi_copy, rects) 

if __name__ == '__main__':
    path = os.path.abspath('..')+"\\LedDetector\\GateArmOnly\\"
    for f in os.listdir(path):
        print (f)
        if f.endswith('.jpg') or f.endswith('.JPG'):
             detect(path, f)
            