import time
#import picamera
import datetime
import os
from  Diagnostics import LocalLogger
from PeriodicTimer import PeriodicTimer
import StreamHandler
import io
import cv2

class VideoRecorder(object):
    """
    This class records the video 
    """
    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self, configs):
        try:
   
            self.logger         = LocalLogger('GLM_Diagnostics', self.whoami(),configs)
            self.__picam__      = None
            self.stream         = io.BytesIO()
            self.__config__     = configs['GLM']
            self.resolution_width  = self.__config__['Recording']['Resolution_Width']
            self.resolution_height = self.__config__['Recording']['Resolution_Height']
            self.recordingTimeout  = self.__config__['Recording']['Recording_Timeout']
            self.framesPerSecond   = self.__config__['Recording']['FramePerSecond']
            self.VideoWriter       = None
            self.VideoCapture      = None
            tempLogDir = configs['GLM']['DIAGNOSTICS'] 
            self.default_images_dir = tempLogDir['IMAGE_LOG_PATH']
            self.default_videos_dir = tempLogDir['VIDEO_LOG_PATH']

            self.__timer__       = PeriodicTimer(self.recordingTimeout * 60, self.stop_recording)
            self.__recordVideo__ = PeriodicTimer(1 , self.StartRecording)
            self.is_recording           = False
            self.__is_streaming__       = False
            self.__last_recorded_file__ = ""
            #self.__StreamOutput__ = StreamHandler.StreamingOutput()
            #address = ('', 8000)
            #self.__StreamingServer__ = StreamHandler.StreamingServer(address, StreamHandler.StreamingHandler)
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' +  self.whoami())
            raise ValueError()

    def InitPiCameraObject(self):
        try:
            if self.__picam__ != None:
                self.stop_recording()
            self.__picam__ = picamera.PiCamera()
        except:
            self.__picam__ = None

    def isRecording(self):
        """
        function returns True if it's recording any video else False
        """
        return self.is_recording

    def stop_recording(self):
        """
        use this function to stop any ongoing video recording
        """
        ret = self.is_recording
        self.logger.log(self.logger.INFO, 'Stop Recording Request Recieved')
        self.is_recording = False
        return ret

    def IncreaseVideoRecordingInterval(self, interval = None):
        if interval == None:
            interval = self.recordingTimeout * 60

        if self.__timer__.is_running == True and self.is_recording == True:
            self.__timer__.IncreaseInterval(interval)
            self.logger.log(self.logger.INFO, 'New Recording Interval is ' + str(self.__timer__.interval/60) + ' minutes')

    def start_video_recording(self, duration = None):
        """
        Starts recording video if there is no ongoing recording process going-on
        Records video for next 10-minutes
        """
        if duration != None:
            self.__timer__.interval = (duration ) * 60

        if self.is_recording == False:
            captureOpened = False
            try:
                self.VideoCapture = cv2.VideoCapture(0)
                captureOpened = True
            except:
                self.logger.log(self.logger.ERROR, 'Can Not Init Video Capture at index 0')
                raise ValueError()

            if captureOpened == True:
                self.is_recording = True
                self.logger.log(self.logger.INFO, 'VideoCapture Init Successfull')
                
                fileName = self.__get_file_name__(self.default_videos_dir,".avi")
                self.__last_recorded_file__ = fileName
                self.logger.log(self.logger.INFO, 'Recording FileName =' + fileName)
                
                #self.VideoCapture.set(3, self.resolution_width)
                #self.VideoCapture.set(4, self.resolution_height)
                self.logger.log(self.logger.INFO, 'Recording Resolution Width =' + str(self.resolution_width) + "  Height= " + str(self.resolution_height) + ' FPS='+ str(self.framesPerSecond))
                self.logger.log(self.logger.INFO, 'Recording Interval is ' + str(self.__timer__.interval/60) + ' minutes')

                self.__recordVideo__.restart()
                self.__timer__.restart()
            else:
                self.logger.log(self.logger.ERROR, 'Failed to Init VideoCapture')
        else:
            self.logger.log(self.logger.ERROR, 'Already Recording a Video File')
            
    def StartRecording(self):
        if self.VideoCapture != None:
            ret, frame = self.VideoCapture.read()
            if ret == True:
                imageHeight = frame.shape[0]
                imageWidth  = frame.shape[1]
                self.VideoWriter = cv2.VideoWriter(self.__last_recorded_file__, cv2.VideoWriter_fourcc(*'MJPG'), self.framesPerSecond, (imageWidth, imageHeight))
                while ret == True and self.isRecording():
                    self.VideoWriter.write(frame)
                    ret, frame = self.VideoCapture.read()

                self.logger.log(self.logger.INFO, 'Video Recording Stopped')   
                self.VideoCapture.release()
                self.VideoWriter.release()

    def __get_file_name__(self, directory, extension):
        """
        Get the filename having complete directory path with current date time
        """
        currDate = datetime.datetime.now().strftime("%Y-%m-%d")

        #checking if current date directory exists 
        if not os.path.exists(directory + currDate):
            os.makedirs(directory + currDate)
        if extension == '.jpg':
            file = directory + currDate + "/" +  "_IMG_"+str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())) + extension

        else:
            file = directory + currDate + "/" +  "_VID_"+str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())) + extension
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
            self.__picam__ = picamera.PiCamera()
            if self.__picam__ != None:
                self.__picam__.resolution = (self.resolution_width, self.resolution_height)
                filename = self.__get_file_name__(self.default_images_dir, ".jpg")
                self.__picam__.capture(filename)
                self.__picam__.close()
                self.__picam__ = None
                return filename
        else:
            self.logger.log(self.logger.ERROR, 'Already Recording a Video File')
    
    def StartStreamOverIP(self):
        if self.isRecording():
            self.logger.log(self.logger.ERROR, 'Failed to Start Stream Over IP, Video Recording is in progress')

        else:
            self.__picam__ = picamera.PiCamera()
            if self.__picam__ != None:
                self.__picam__.resolution = (self.resolution_width, self.resolution_height)
                self.__picam__.start_recording(self.__StreamOutput__, format = 'mjpeg')
                threading.Thread(target= self.__StreamingServer__.serve_forever)
                #self.__StreamingServer__.
                try:
                    if not self.__is_streaming__:
                        self.__is_streaming__ = True
                except:
                    pass

    def StopStream(self):
        if self.__is_streaming__ == True:
            self.stop_recording()
            self.__StreamingServer__.shutdown()
