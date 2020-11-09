import logging
import time
import datetime
import sys
import os
import inspect

class LocalLogger(object):
	#these are logging levels mentioned by logging python lib 
	CRITICAL    = 50
	ERROR	    = 40
	WARNING	    = 30
	INFO	    = 20
	DEBUG	    = 10

	#gives the current system date only
	def __get_current_date__(self):
		return datetime.datetime.utcnow().strftime("%Y-%m-%d")

	__instance__ = None
	@staticmethod
	def Instance():
		""" Static method to fetch the current instance.
		"""
		return LocalLogger.__instance__

	def SetAPIName(self, ApiName):
		self.api_name = ApiName
		self.__diagnostics__.name = ApiName
		return self

	def __init__(self, FileName, configs):
		"""
		initialize the localLogger class object
		parm1 Filename : (String) This will be used for logging 
		parm2 ApiName :  (String) API/Class or any individual function name which is creating the logger object
		use whoami function for this purpose
		"""
		#__DefaultDiagnosticsDir__ init this
		try:
			self.fileame  = FileName
			self.api_name = "GLM"
			self.__Log_Dir__        = configs['GLM']['DIAGNOSTICS']['LOG_PATH']
			self.isDeatiledLog      = configs['GLM']['DIAGNOSTICS']['DetailLogEnabled']

			self.__current_date__   = self.__get_current_date__()
			self.__FileHandler__    = None
			self.__diagnostics__    = self.__get_logger_object__()
			#Setting Static Object
			if LocalLogger.__instance__ is None:
				LocalLogger.__instance__ = self
		except:
			raise ValueError()
		pass

	def __change_logger_dir_on_date_change__(self):
		"""
		call this function on date change to create a new working directory for logging 
		this funcation automatically creates a new file and chnage the filehandler of logging object
		"""
		self.__current_date__ = self.__get_current_date__()

		self.__diagnostics__.removeHandler(self.__FileHandler__)
		self.__diagnostics__ = self.__get_logger_object__()
		try:
			os.system("find /home/GLM/DIAGNOSTICS/RECORDINGS/* -mmin +$((60*24)) -delete")
		except:
			self.__diagnostics__.log(self.ERROR, 'Failed to Delete Old Recording Files')
		pass

	def log(self, level, str, isDetailed = False):
		"""
		This is a public function used to log data
		parm1 level : Interger is the logging level i.e. error / warning / debug etc 
		parm2 str : String to be logged into the file
		"""
		stack = inspect.stack()
		the_class = stack[1][0].f_locals["self"].__class__.__name__
		the_method = stack[1][0].f_code.co_name
		self.__diagnostics__.name = the_class + " " + the_method
  
		if type(level) is int:
			if self.__get_current_date__() != self.__current_date__:
				self.__change_logger_dir_on_date_change__()
			if isDetailed:
				if self.isDeatiledLog:
					self.__diagnostics__.log(level, str)
				else:
					pass
			else:
				self.__diagnostics__.log(level, str)
		else:
			pass

	def __get_log_dir_filePath__(self, name):
		"""
		this returns the complete path of the logging file 
		parm1 name : (String) name of the file to be used for logging
		"""
		currDate = self.__get_current_date__()
		if not os.path.exists(self.__Log_Dir__ + currDate):
			os.makedirs(self.__Log_Dir__ + currDate)
		return self.__Log_Dir__ + '/'+ currDate +'/' + name + ".txt"

	def __get_logger_object__(self):
		"""
		Returns a formated logging object, Logging format is as follow :
		ascitime - API name - logging level : Log
		"""
		logger = logging.getLogger(self.api_name) #setting api name for logging 
		logger.setLevel(logging.DEBUG)

		log_file = self.__get_log_dir_filePath__(self.fileame)
		handler = logging.FileHandler(log_file) #setting the file path
		handler.setLevel(logging.DEBUG)

		formatter = logging.Formatter("[%(asctime)s.%(msecs)03d %(levelname)s %(name)s] : %(message)s" , datefmt='%b-%d-%y %H:%M:%S')
		handler.setFormatter(formatter)
		self.__FileHandler__ = handler
		logger.addHandler(handler)

		return logger
