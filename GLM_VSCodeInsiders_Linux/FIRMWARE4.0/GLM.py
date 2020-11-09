import Logic
import json
import time
import inspect

class GLM(object):

	def whoami(self):
		"""
		returns the class name as string
		"""
		return type(self).__name__

	def LoadConfigurations(self):
		"""Returns configurations json object if loaded correctly else None"""
		try:
			with open("/home/GLM/Current/Logic/Configurations.json")as config_file:
				data = json.load(config_file)
				return data
		except:
			return {}
		pass

	def __init__(self):
		try:
			self.ObjectsToProcess 		= []
			self.configs                = {}
			self.configs                = self.LoadConfigurations()
			self.Init(config=self.configs)
			self.logger     			= Logic.GetLogger()
			self.logger.log(self.logger.INFO,'INIT Classes SUCCESSFULLY ' )
			self.Start()
			self.logger.log(self.logger.INFO,'Classes LOGIC STARTED SUCCESSFULLY ' )	
			self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ' )

		except:
			self.logger.log(self.logger.ERROR, 'Failed to Init ' )
		pass

	def Init(self,config):
		_Diagnostics = Logic.LocalLogger("GLM_Diagnostics",config)

		MY_ID = config['GLM']['MY_ID']
		ledPath = config['GLM']['LedDetector']['LedCordinatesFilePath']
		ledPath = ledPath.replace("#", MY_ID)

		Logic.UDPClient(config)
		Logic.HttpClient(config)
		Logic.MQTTClient(config)
		Logic.LedDetector(config)
		Logic.BlinkCounter(ledPath,config)
		Logic.WIFIZMQClient(config)
		Logic.VideoRecorder(config)
		Logic.ZMQDataProcessor(config)
		Logic.MQTTDataProcessor(config)
		Logic.LiveCommandHandler(config)
		Logic.VideoRecordingProcessor(config)
		
		#Appending Objects so that we don't have to Get Instances in Process

		self.ObjectsToProcess.append(Logic.GetHTTPClient())
		self.ObjectsToProcess.append(Logic.GetMQTTClient())
		self.ObjectsToProcess.append(Logic.GetVideoRecordingProcessor())

	def Start(self):
		Logic.VideoRecordingProcessor.Instance().Start()
		Logic.LiveCommandHandler.Instance().Start()
		Logic.ZMQDataProcessor.Instance().Start()
		Logic.MQTTDataProcessor.Instance().Start()

	def EXECUTE(self):
		try:
			while True:
				self.Process()
				time.sleep(30/1000)
		except:
			stack = inspect.stack()
			the_class = stack[1][0].f_locals["self"].__class__.__name__
			the_method = stack[1][0].f_code.co_name
			self.logger.log(self.logger.ERROR, "Terminating App | Class = " + the_class + " FUNC = "+ the_method )

	def Process(self):
		for obj in self.ObjectsToProcess:
			obj.Process()


if __name__ == "__main__":
	try:
		glmObj = GLM()
		glmObj.EXECUTE()
	except:
		pass
