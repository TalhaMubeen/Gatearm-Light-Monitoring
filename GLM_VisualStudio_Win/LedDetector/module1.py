import time
import picamera
import datetime
import os
from PeriodicTimer import PeriodicTimer

save_directory = "/home/GLM/RECORDINGS/"
cam = picamera.PiCamera()
is_recording = False


def stop_recording():
    if is_recording == True:
        cam.stop_preview()
        cam.stop_recording()
        is_recording = False

recordingTimer = PeriodicTimer(10 * 60, stop_recording)   


def get_file_name():
    currDate = datetime.datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(save_directory + currDate):
        os.makedirs(save_directory + currDate)
    return currDate + "/" + datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.h264")


def start_video_recording():
    if is_recording == False:
        fileName = "%s%s" % (save_directory, get_file_name())
        #cam.resolution = (1960, 1080)
        cam.resolution = (1280, 720)
        cam.framerate = 30
        cam.start_preview()
        cam.start_recording(fileName)
        is_recording = True
        recordingTimer.restart()
        