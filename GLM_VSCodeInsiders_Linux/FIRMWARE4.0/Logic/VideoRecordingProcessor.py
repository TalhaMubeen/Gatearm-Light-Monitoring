import Logic

import io
import time
import datetime
import os


class VideoRecordingProcessor(object):
    """This class provides driving logic for VideoRecorder API """

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    __instance__ = None

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        return VideoRecordingProcessor.__instance__

    def __init__(self, configs):
        try:
            self.logger = Logic.GetLogger()
            self.EIP_ID = configs['GLM']['EIP_ID']
            self.MY_ID = configs['GLM']['MY_ID']

            timeout = configs['GLM']['Recording']['Recording_Timeout']
            self.__ProcessVideoLightDetectionTimer__ = Logic.PeriodicTimer(timeout * 60, self.ProcessVideoLightDetectionOnTimer)

            self.UploadVideoFilePath = ""
            self.isWaitingUpload = False
            self.StartRecordingPktRcvd = False
            self.StopRecordingPktRcvd = False
            self.ProcessingVideo = False
            self.TS = ""
            # Setting Static Instance
            if VideoRecordingProcessor.__instance__ is None:
                VideoRecordingProcessor.__instance__ = self
            self.logger.log(self.logger.INFO, 'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ')
            raise ValueError()
        pass

    def Start(self):
        Logic.GetVideoRecorder().RegisterFileRecordedCallback(self.OnVideoRecorded)
        Logic.GetLedDetector().SetProcessedVideoUploadCallback(self.OnVideoProcessingComplete)

    def ProcessVideoLightDetectionOnTimer(self):
        # no detection status msg rcvd in first Timeout window
        if self.StopRecordingPktRcvd and (".mp4" in self.UploadVideoFilePath):  # Recording stopped before Timeout
            path = os.path.splitext(self.UploadVideoFilePath)[0]
            if not ('.mp4' in path):
                Logic.GetLedDetector().AddToProcessQueue(path, self.TS)
                self.ProcessingVideo = True
        else:
            self.logger.log(self.logger.ERROR, 'No Stop Recording MSG RCVD FOR VIDEO: ' + self.UploadVideoFilePath)

        self.TS = ""
        self.UploadVideoFilePath = ""
        self.StopRecordingPktRcvd = False
        self.isWaitingUpload = False
        self.StartRecordingPktRcvd = False
        self.logger.log(self.logger.INFO, 'VIDEO UPLOAD API RESET SUCCESSFULLY')

    def OnStopRecordingRcvd(self):
        """
        stop any on-going video recording
        """
        self.StopRecordingPktRcvd = True
        ret = Logic.GetVideoRecorder().stop_recording()
        if ret == True:
            self.logger.log(self.logger.DEBUG, 'Stop Recording Packet Recieved from EIP ' + self.EIP_ID)
        else:
            if self.isWaitingUpload:
                self.logger.log(self.logger.INFO, 'Uploading Video NOW')
                self.__ProcessVideoLightDetectionTimer__.stop()
                self.ProcessVideoLightDetectionOnTimer()
            else:
                self.logger.log(self.logger.ERROR,'Stop Recording Packet Recieved: No Video Recording | No Pending Upload')
        return

    def OnStartRecordingRcvd(self):
        if self.ProcessingVideo:
            return
        if Logic.GetVideoRecorder().isRecording() == False and not self.StartRecordingPktRcvd:
            self.StartRecordingPktRcvd = True
            self.logger.log(self.logger.INFO, 'Start Recording Packet Recieved From EIP ' + self.EIP_ID)
            self.StopRecordingPktRcvd = False
            Logic.GetVideoRecorder().start_video_recording()
        else:
            pass

    def OnVideoRecorded(self, path, TimeStamp):
        self.UploadVideoFilePath = path
        self.TS = TimeStamp
        self.isWaitingUpload = False

        if self.StopRecordingPktRcvd == True:
            self.logger.log(self.logger.INFO, 'Uploading Video NOW')
            self.ProcessVideoLightDetectionOnTimer()
        else:
            self.logger.log(self.logger.INFO,'Video Upload API Waiting For STOP RECORDING PACKET from EIP ' + self.EIP_ID)
            self.isWaitingUpload = True
            self.__ProcessVideoLightDetectionTimer__.restart()

    def OnVideoProcessingComplete(self, videoFile):
        if '.mp4' in videoFile:
            self.ProcessingVideo = False
            Logic.GetHTTPClient().PostVideo(videoFile)
        else:
            pass

    def Process(self):
        Logic.GetVideoRecorder().Process()

        #if Logic.GetLedDetector().isProcessingvideo():
        #    Logic.GetLedDetector().ProcessVideoFrame()

        if Logic.GetLedDetector().inQueue():
            # processing video queue to find leds
            Logic.GetLedDetector().Process()
