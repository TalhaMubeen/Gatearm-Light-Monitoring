import threading 
import time

class PeriodicTimer(object):

	def whoami(self):
		"""
		returns the class name as string
		"""
		return type(self).__name__

	def __init__(self, interval, function):
		try:
			self._timer     = None
			self.interval   = interval
			self.function   = function
			self.next_call  = time.time()
			#self.args = args
			#self.kwargs = kwargs
			self.runOnce    = False
			self.is_running = False
		except:
			raise ValueError()
		pass

	def _run(self):
		self.start()
		self.function()
		self.is_running = False

	def start(self):
		if not self.is_running:
			#self.next_call    += self.interval
			#self._timer       = threading.Timer(self.next_call - time.time(), self._run)
			self._timer       = threading.Timer(self.interval, self._run)
			self._timer.daemon = True
			self.is_running   = True
			self._timer.start()
		else:
			pass

	def stop(self):
		if self._timer != None:
			self._timer.cancel()
		self.is_running = False
		self.runOnce = True
    
	def restart(self):
		self.stop()
		self.start()

	def IncreaseInterval(self, duration):
		if self._timer != None:
			self._timer.interval = self._timer.interval + duration
			self.interval = self.interval + duration
		else:
			pass

