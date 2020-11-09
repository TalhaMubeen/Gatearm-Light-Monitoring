import cv2
import os
import time
import datetime
import Logic

class LedDetector(object):
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
		return LedDetector.__instance__

	def __init__(self, configs):
		try:
			self.logger    			= Logic.GetLogger()
			self.fps                = configs['GLM']['Recording']['FramePerSecond']
			self.LocStart_Y         = configs['GLM']['AreaOfInterest']['LocStart_Y']
			self.LocEnd_Y           = configs['GLM']['AreaOfInterest']['LocEnd_Y']
			self.LocStart_X         = configs['GLM']['AreaOfInterest']['LocStart_X']
			self.LocEnd_X           = configs['GLM']['AreaOfInterest']['LocEnd_X']

			self.MYID               = configs['GLM']["MY_ID"]
			self.capture            = None
			self.outputFile         = ""
			self.InputFileQueue     = []
			self.foundOneLED        = [False,False,False]
			self.frameCount         = 0
			self.TotalFrame         = 0
			self.OnVideoProcessComplete = None
			self.TempDirPath        = "/home/temp/"
			self.inputFileName      = ""
			self.TS                 = ""

			#Setting Static Instance 
			if LedDetector.__instance__ is None:
				LedDetector.__instance__ = self
			self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ' )
		except:
			self.logger.log(self.logger.ERROR,'Failed to Init ' )
			raise ValueError()
		pass

	def SetProcessedVideoUploadCallback(self, func):
		self.OnVideoProcessComplete = func

	def AddToProcessQueue(self, fileName, ts):
		self.InputFileQueue.append([fileName, ts])

	def init_video_process(self, filename, ts):
		self.TS = ts
		self.inputFileName = filename + ".mp4"
		self.capture = cv2.VideoCapture(self.inputFileName)

		self.TotalFrame = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
		if self.TotalFrame == 0:
			self.logger.log(self.logger.ERROR, "Failed to Find Video File " + filename + '.mp4')
			self.capture = None
			return
		self.logger.log(self.logger.INFO, "Total Video Frames : " + str(self.TotalFrame))

		self.outputFile = filename
		if os.path.isdir(self.TempDirPath):
			os.system("rm -rf " + self.TempDirPath)
		os.mkdir(self.TempDirPath)



	def inQueue(self):
		ret = False
		if (len(self.InputFileQueue) > 0) or (self.capture and self.outputFile):
			ret = True  
		return ret

	def isProcessingvideo(self):
		if self.TotalFrame > 0 and self.frameCount < self.TotalFrame:
			return True
		else:
			return False


	def ResetDetectionState(self):

		blinks = Logic.GetBlinkCounter().GetBlinkCounters()

		for  i in range(len(blinks)):
			self.logger.log(self.logger.INFO, 'Blink Count of Recording '+self.inputFileName +' : Led =>' + str (i) + ' : ' + str (blinks[i][1][1]))

		Logic.GetBlinkCounter().ResetBlinkcounters()

		self.foundOneLED = [False,False,False]
		self.capture = None
		self.outputFile  = ""
		self.TotalFrame = 0
		self.frameCount = 0

		self.logger.log(self.logger.INFO, 'Blink Counter State Reset Successfully')

	def Process(self):
		if len(self.InputFileQueue) > 0:
			if self.capture == None and self.outputFile == "":
				fileinprocess, ts = self.InputFileQueue[0][0], self.InputFileQueue[0][1]
				self.init_video_process(fileinprocess, ts)
				del self.InputFileQueue[0]
		if self.capture and self.outputFile:
			self.ProcessVideoFrame()
		return

	def ProcessVideoFrame(self):
		if self.capture == None:
			return

		for fcount in range(6):
			ret1, frame1 = self.capture.read()
			if ret1 == True:
				self.frameCount += 1
				self.logger.log(self.logger.INFO, "Processing Frame No: " + str(self.frameCount) + ' Out of ' + str(self.TotalFrame), True)
				image2 = frame1[self.LocStart_Y:self.LocEnd_Y, self.LocStart_X:self.LocEnd_X]
				ret, LightLoc = Logic.GetBlinkCounter().GetLastLedBlinkState(image2)
				cv2.putText(frame1, self.MYID  + ' '+ self.TS , ( 5  , 30),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
				del image2
				for  i in range(len(LightLoc)):
					(cX, cY), radius, ret =  LightLoc[i][0] , LightLoc[i][1], LightLoc[i][2]
					if ret == False and not self.foundOneLED[i]:
						continue
					else: 
						self.foundOneLED[i] = True
						count = Logic.GetBlinkCounter().IncrementLightCounter(i, ret)
						yloc = 60 + (30 * i)
						if count > 0:
							cv2.putText(frame1, 'LIGHT ' + str(i+1) + ' : '+ str(count), ( 5  , yloc),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
				del LightLoc
				cv2.imwrite(self.TempDirPath+"image"+str(self.frameCount)+".jpg", frame1, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
				del frame1
				time.sleep(6/1000)
			else:
				break

		if self.frameCount >= self.TotalFrame and self.TotalFrame is not 0:
			try:
				self.TS = ""
				self.outputFile += ('_'+str(int(datetime.datetime.utcnow().timestamp())) + '.mp4')
				self.logger.log(self.logger.INFO, "Init Video Stitching at path" + self.outputFile)
				#cmd ="cd "+self.TempDirPath +"; ffmpeg -y -loglevel error -framerate "+str(self.fps)+" -start_number 1 -i image%d.jpg -codec h264_omx -b:v 2048k -an " +self.outputFile+ " > /dev/null"
				cmd ="cd "+self.TempDirPath +"; ffmpeg -y -loglevel error -framerate 8 -start_number 1 -i image%d.jpg -codec h264_omx -b:v 2048k -an " +self.outputFile+ " > /dev/null"
				os.system(cmd)
				if os.path.exists(self.outputFile):
					self.logger.log(self.logger.INFO, "Video Saved Successfully at path" + self.outputFile)
					os.system("rm -rf " + self.TempDirPath)
					self.OnVideoProcessComplete(self.outputFile)
				else:
					self.logger.log(self.logger.ERROR, "Faile to Save video File at path" + self.outputFile)
				self.ResetDetectionState()
			except:
				self.logger.log(self.logger.ERROR, "Faile to Stitch Video" + self.outputFile)
