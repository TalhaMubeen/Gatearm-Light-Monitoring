import time
import picamera
import datetime
import os
from  Diagnostics import LocalLogger
from RepeatedTimer import PeriodicTimer
import io
import cv2
import socketserver
from threading import Condition
import threading
from http import server

PAGE="""\
<html>
<head>
<title>GateArm Light Monitor</title>
</head>
<body>
<center><h1>GateArm Light Monitor</h1></center>
<center><img src="stream.mjpg" width="1024" height="1024"></center>
</body>
</html>
"""
class StreamingOutput(object):
	def __init__(self):
		self.frame = None
		self.buffer = io.BytesIO()
		self.condition = Condition()

	def write(self, buf):
		if buf.startswith(b'\xff\xd8'):
			# New frame, copy the existing buffer's content and notify all
			# clients it's available
			self.buffer.truncate()
			with self.condition:
				self.frame = self.buffer.getvalue()
				self.condition.notify_all()
			self.buffer.seek(0)
		return self.buffer.write(buf)
output = StreamingOutput()
class StreamingHandler(server.BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == '/':
			self.send_response(301)
			self.send_header('Location', '/index.html')
			self.end_headers()
		elif self.path == '/index.html':
			content = PAGE.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)
		elif self.path == '/stream.mjpg':
			self.send_response(200)
			self.send_header('Age', 0)
			self.send_header('Cache-Control', 'no-cache, private')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
			self.end_headers()
			try:
				while True:
					with output.condition:
						output.condition.wait()
						frame = output.frame
					self.wfile.write(b'--FRAME\r\n')
					self.send_header('Content-Type', 'image/mjpeg')
					self.send_header('Content-Length', len(frame))
					self.end_headers()
					self.wfile.write(frame)
					self.wfile.write(b'\r\n')
			except Exception as e:
				pass
		else:
			self.send_error(404)
			self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

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
			self.__picam__      = picamera.PiCamera()
			self.__picam__.resolution = (1024,1024)
			self.__picam__.rotation = 90

			self.stream         = io.BytesIO()
			self.__config__     = configs['GLM']

			self.resolution_width  = self.__config__['Recording']['Resolution_Width']
			self.resolution_height = self.__config__['Recording']['Resolution_Height']
			self.__picam__.resolution = (self.resolution_width , self.resolution_height)

			self.recordingTimeout  = self.__config__['Recording']['Recording_Timeout']
			self.framesPerSecond   = self.__config__['Recording']['FramePerSecond']
			self.__picam__.framerate = self.framesPerSecond

			self.VideoWriter       = None
			self.VideoCapture      = None

			tempLogDir = configs['GLM']['DIAGNOSTICS'] 
			self.default_images_dir = tempLogDir['IMAGE_LOG_PATH']
			self.default_videos_dir = tempLogDir['VIDEO_LOG_PATH']

			self.__StreamVideo__       = PeriodicTimer(1, self.StartStreamOverIP)
			self.__recordVideo__       = PeriodicTimer(1, self.StartRecording)
			self.is_recording           = False
			self.__is_streaming__       = False
			self.__last_recorded_file__ = ""
			self.OnFileRecordedCallback = None
		except:
			self.logger.log(self.logger.ERROR, 'Failed to Init ' +  self.whoami())
			raise ValueError()
		pass

	def isRecording(self):
		"""
		function returns True if it's recording any video else False
		"""
		return self.is_recording

	def RegisterFileRecordedCallback(self, callback):
		self.OnFileRecordedCallback = callback

	def stop_recording(self):
		"""
		use this function to stop any ongoing video recording
		"""
		ret = self.is_recording
		if self.is_recording:
			self.is_recording = False   
			self.__picam__.stop_recording(splitter_port=1)
			self.logger.log(self.logger.INFO, 'Video Recording Stopped')
			self.__recordVideo__.stop()
		return ret

	def start_video_recording(self, duration = None):
		"""
		Starts recording video if there is no ongoing recording process going-on
		Records video for next 5-minutes
		"""

		if self.is_recording == False:     
			self.__recordVideo__.restart()
		else:
			self.logger.log(self.logger.ERROR, 'Already Recording a Video File')

	def StartRecording(self):
		if self.is_recording:
			self.logger.log(self.logger.INFO, 'Already Recording a Video')
		else:
			self.is_recording = True
			fileName = ""
			fileName = self.__get_file_name__(self.default_videos_dir,".h264")
			fileMP4 = fileName.replace('h264', 'mp4')
			self.__last_recorded_file__ = fileName

			dt = datetime.datetime.utcnow().strftime("%b-%d-%Y %H:%M:%S")
			self.logger.log(self.logger.INFO, 'Starting Video Recording, File : ' + fileName) 

			self.__picam__.start_recording(fileName, splitter_port=1)
			self.__picam__.wait_recording(timeout = (self.recordingTimeout*60), splitter_port=1)

			if self.is_recording: # do not stop if stopped by signal already i.e stop_recording is called by external thread
				self.__picam__.stop_recording(splitter_port=1)

			self.logger.log(self.logger.INFO, 'Video Recorded Successfully')

			#Safety check while Converting video from h264 to MP4 so that any other video recording can not be called from external thread
			self.is_recording = True 

			#converting h264 to MP4 with fps info header
			os.system('MP4Box -noprog -add ' + fileName + ' -fps '+ str(self.framesPerSecond)+' '+ fileMP4)

			if os.path.isfile(fileMP4):
				os.remove(fileName)
				self.__last_recorded_file__ = fileMP4
				if self.OnFileRecordedCallback != None:
					self.OnFileRecordedCallback(fileMP4, dt+ ' UTC')
				else:
					self.logger.log(self.logger.ERROR, 'On Video File Recorded Callback Not Registered')
			else:
				self.logger.log(self.logger.ERROR, 'Failed To FIND VIDEO FILE : ' + fileName)   
			self.is_recording = False

	def __get_file_name__(self, directory, extension):
		"""
		Get the filename having complete directory path with current date time
		"""
		currDate = datetime.datetime.utcnow().strftime("%Y-%m-%d")

		#checking if current date directory exists 
		if not os.path.exists(directory + currDate):
			os.makedirs(directory + currDate)
		if extension == '.jpg':
			file = directory + currDate + "/" +  "_IMG_"+str(int(datetime.datetime.utcnow().timestamp())) + extension

		else:
			file = directory + currDate + "/" +  "_VID_"+str(int(datetime.datetime.utcnow().timestamp())) + extension
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
		if self.__picam__ != None:
			filename = self.__get_file_name__(self.default_images_dir, ".jpg")
			self.__picam__.capture(filename, splitter_port=0)
			return filename
		else:
			pass

	def Process(self):
		if self.__StreamVideo__.is_running:
			pass
		else:
			self.__StreamVideo__.restart()
			self.__StreamVideo__.is_running = True
	
	def StopStream(self):
		if self.__is_streaming__ == False:
			pass
		else:
			self.__picam__.stop_recording(splitter_port=2)
			self.__is_streaming__ = False
			self.__StreamingServer__.shutdown()

	def StartStreamOverIP(self):
		if self.__picam__ != None:
			self.__picam__.start_recording(output, splitter_port=2, format = 'mjpeg')
			try:
				address = ('', 8000)
				self.__is_streaming__ == True
				self.__StreamingServer__ = StreamingServer(address, StreamingHandler)
				self.__StreamingServer__.serve_forever()
			except:
				print('failed')
		else:
			pass