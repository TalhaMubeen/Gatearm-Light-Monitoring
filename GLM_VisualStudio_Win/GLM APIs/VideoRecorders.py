import time
import picamera
import datetime
import os
from RepeatedTimer import PeriodicTimer

class VideoRecorder(object):
    """
    This class records the video 
    """

    default_recording_dir = "/home/GLM/RECORDINGS/"
    default_images_dir = "/home/GLM/IMAGES/"
    video_resolution_W = 1280
    video_resolution_H = 720

    def __init__(self):
        self.__picam__ = picamera.PiCamera()
        self.__is_recording__ = False
        self.__timer__ = PeriodicTimer(10 * 60, self.stop_recording)
        self.__last_recorded_file__ = ""

    def isRecording(self):
        """
        function returns True if it's recording any video else False
        """
        return self.__is_recording__

    def stop_recording(self):
        """
        use this function to stop any ongoing video recording
        """
        ret = False
        if self.isRecording() == True:
            self.__picam__.stop_preview()
            self.__picam__.stop_recording()
            self.__is_recording__ = False
            ret = True
        return ret

    def __get_file_name__(self, directory, extension):
        """
        Get the filename having complete directory path with current date time
        """
        currDate = datetime.datetime.now().strftime("%Y-%m-%d")

        #checking if current date directory exists 
        if not os.path.exists(directory + currDate):
            os.makedirs(directory + currDate)
        if extension == 'jpg':
            file = directory + currDate + "/" +  "Img_"+datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S" + extension)
        else:
            file = directory + currDate + "/" +  "Rec_"+datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S" + extension)
        return file


    def get_last_recorded_file(self):
        """
        This function returns the file name and path of last recording done using this module 
        """
        return self.__last_recorded_file__
    
    def clear_last_record_name(self):
        """
        Clears the stored last record file name
        """
        self.__last_recorded_file__ = ""

    def capture_image(self):
        if not self.isRecording():
            self.__picam__.resolution = (video_resolution_W, video_resolution_H)
            self.__picam__.start_preview()
            # Camera warm-up time
            time.sleep(2)
            filename = self.__get_file_name__(default_images_dir, ".jpg")
            self.__picam__.capture(filename)
            self.__picam__.stop_preview()
            return filename

    def start_video_recording(self):
        """
        Starts recording video if there is no ongoing recording process going-on
        Records video for next 10-minutes
        """
        if self.isRecording() == False:
            fileName = self.__get_file_name__(default_recording_dir,".h264")
           
           #updating the last saved recording file name
            self.__last_recorded_file__ = fileName

            #__picam__.resolution = (1960, 1080)
            self.__picam__.resolution = (video_resolution_W, video_resolution_H)
            self.__picam__.framerate = 5
            self.__picam__.start_preview()
            time.sleep(2)
            self.__picam__.start_recording(fileName)
            self.__is_recording__ = True
            self.__timer__.restart()
