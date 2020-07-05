import threading 
import time

class PeriodicTimer(object):
    def __init__(self, interval, function):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.next_call  = time.time()
        #self.args = args
        #self.kwargs = kwargs
        self.runOnce    = False
        self.is_running = False
        
        #self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function()

    def start(self):
        if not self.is_running:
          #self.next_call    += self.interval
          #self._timer       = threading.Timer(self.next_call - time.time(), self._run)
          self._timer       = threading.Timer(self.interval, self._run)
          self._timer.start()
          self.is_running   = True

    def stop(self):
        if self._timer != None:
            self._timer.cancel()
        self.is_running = False
        self.runOnce = True
    
    def restart(self):
        self.stop()
        self.start()
