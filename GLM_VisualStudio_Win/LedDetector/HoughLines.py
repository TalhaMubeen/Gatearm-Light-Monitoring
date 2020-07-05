#from __future__ import print_function

#import cv2 as cv
#import numpy as np

#import sys
#import math

#def main():
#    try:
#        fn = sys.argv[1]
#    except IndexError:
#        fn = 'Led.jpg'


#    src = cv.imread(cv.samples.findFile(fn) , 0)
#    img = cv.medianBlur(src,5)

#    th3 = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,\
#            cv.THRESH_BINARY,11,2)
#    cdst = th3;
#    cv.imshow("Adaptive Edges", th3);
#    dst = cv.Canny(th3, 100, 200)
#    cv.imshow("Adaptive Edges", dst);
#    #cv.imshow("Edges", dst);
#    #cdst = cv.cvtColor(dst, cv.COLOR_GRAY2BGR)

#    lines = cv.HoughLinesP(dst, 1, math.pi/180.0, 40, np.array([]), 50, 10)
#    a,b,c = lines.shape
#    for i in range(a):
#        cv.line(cdst, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (0, 0, 255), 3, cv.LINE_AA)


#    cv.imshow("detected lines", cdst)

#    cv.imshow("source", src)
#    cv.waitKey(0)
#    print('Done')


#if __name__ == '__main__':
#    main()
#    cv.destroyAllWindows()

from __future__ import print_function
import cv2 as cv
import argparse
max_value = 255
#max_value_H = 360//2
max_value_H = 255
low_H = 0
low_S = 0
low_V = 0
high_H = max_value_H
high_S = max_value
high_V = max_value
window_capture_name = 'Video Capture'
window_detection_name = 'Object Detection'
low_H_name = 'Low H'
low_S_name = 'Low S'
low_V_name = 'Low V'
high_H_name = 'High H'
high_S_name = 'High S'
high_V_name = 'High V'
def on_low_H_thresh_trackbar(val):
    global low_H
    global high_H
    low_H = val
    low_H = min(high_H-1, low_H)
    cv.setTrackbarPos(low_H_name, window_detection_name, low_H)
def on_high_H_thresh_trackbar(val):
    global low_H
    global high_H
    high_H = val
    high_H = max(high_H, low_H+1)
    cv.setTrackbarPos(high_H_name, window_detection_name, high_H)
def on_low_S_thresh_trackbar(val):
    global low_S
    global high_S
    low_S = val
    low_S = min(high_S-1, low_S)
    cv.setTrackbarPos(low_S_name, window_detection_name, low_S)
def on_high_S_thresh_trackbar(val):
    global low_S
    global high_S
    high_S = val
    high_S = max(high_S, low_S+1)
    cv.setTrackbarPos(high_S_name, window_detection_name, high_S)
def on_low_V_thresh_trackbar(val):
    global low_V
    global high_V
    low_V = val
    low_V = min(high_V-1, low_V)
    cv.setTrackbarPos(low_V_name, window_detection_name, low_V)
def on_high_V_thresh_trackbar(val):
    global low_V
    global high_V
    high_V = val
    high_V = max(high_V, low_V+1)
    cv.setTrackbarPos(high_V_name, window_detection_name, high_V)
#parser = argparse.ArgumentParser(description='Code for Thresholding Operations using inRange tutorial.')
#parser.add_argument('--camera', help='Camera divide number.', default=0, type=int)
#args = parser.parse_args()
#cap = cv.VideoCapture('http://172.19.91.240:8000/stream.mjpg')
cv.namedWindow(window_capture_name)
cv.namedWindow(window_detection_name)
cv.createTrackbar(low_H_name, window_detection_name , low_H, max_value_H, on_low_H_thresh_trackbar)
cv.createTrackbar(high_H_name, window_detection_name , high_H, max_value_H, on_high_H_thresh_trackbar)
cv.createTrackbar(low_S_name, window_detection_name , low_S, max_value, on_low_S_thresh_trackbar)
cv.createTrackbar(high_S_name, window_detection_name , high_S, max_value, on_high_S_thresh_trackbar)
cv.createTrackbar(low_V_name, window_detection_name , low_V, max_value, on_low_V_thresh_trackbar)
cv.createTrackbar(high_V_name, window_detection_name , high_V, max_value, on_high_V_thresh_trackbar)

def colorRange(image):
#while True:
    #ret, frame = cap.read()
    ret, frame = True, image

    frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    cropped = frame[0:450, 200:390]

    frame_threshold = cv.inRange(frame, (low_H, low_S, low_V), (high_H, high_S, high_V))
    
    # cv.imshow(window_capture_name, cropped)
    cv.imshow(window_detection_name, frame_threshold)
    cv.waitKey(0)