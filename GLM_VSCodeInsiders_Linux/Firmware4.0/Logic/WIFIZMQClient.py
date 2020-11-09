import Logic
import time
import zmq


class WIFIZMQClient(object):
    """
	This class is responsible to eastablish zmq communication 
	"""

    def whoami(self):
        """
		returns the class name as string
		"""
        return type(self).__name__

    __instance__ = None

    @staticmethod
    def Instance():
        """
		Static method to fetch the current instance.
		"""
        return WIFIZMQClient.__instance__

    def __init__(self, configs):
        try:
            self.logger = Logic.GetLogger().SetAPIName(self.whoami())
            self.__eip_address__ = ""
            self.__sub__ = None
            self.__pub__ = None
            self.__message__ = None
            self.__zmq_ctx__ = None
            # Binding Subscriber to generic socket
            self.__ConnectSubscriber__()
            self.OnDataRcvCallback = None

            # Setting Static Object
            if WIFIZMQClient.__instance__ is None:
                WIFIZMQClient.__instance__ = self
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' + self.whoami())
            raise ValueError()
        pass

    def SetZMQDataRcvCallback(self, callback):
        self.OnDataRcvCallback = callback

    def __ConnectSubscriber__(self):
        """
		This Subscribes to all topics
		"""
        context = zmq.Context()
        self.__sub__ = context.socket(zmq.SUB)
        self.__sub__.setsockopt(zmq.SUBSCRIBE, b'')
        self.__sub__.bind("tcp://*:6669")
        time.sleep(1)

    def __ConnectPubSocket__(self, eip_ip):
        pub_ip = "tcp://" + eip_ip + ":6666"
        if self.__pub__ != None:
            # New EIP IP ADDRESS is different from the prev EIP IP ADDRESS
            self.__pub__.disconnect(pub_ip)
            self.__pub__.close()
            self.__pub__ = None
            self.__eip_address__ = ""

        if self.__pub__ == None:
            # Connect to the given EIP IP ADDRESS
            context = zmq.Context()
            self.__pub__ = context.socket(zmq.PUB)
            self.__sub__.connect(pub_ip)
            time.sleep(1)
            self.__eip_address__ = eip_ip

    def SendMessage(self, data):
        if self.__pub__ == None:
            return
        self.__pub__.send(data)

    def Process(self):
        try:
            raw_msg = self.__sub__.recv(flags=zmq.NOBLOCK, copy=True)
            raw_msg = raw_msg.replace('\n', '')
            if len(raw_msg) > 0:
                if raw_msg.count('@') > 0:  # we recieved EIP IP Address
                    eip_address = raw_msg.replace('@', '')

                    if self.__eip_address__ != eip_address:
                        # Eastablishing Publish Socket using EIP IP ADDRESS
                        Logic.GetUDPClient().SetEIPIPAddress(eip_address)
                        self.__ConnectPubSocket__(eip_address)
                    else:
                        # do nothing we have already eastblished socket with current EIP IP ADDRESS
                        pass
                else:
                    self.OnDataRcvCallback(raw_msg)
            else:
                pass
        except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
                pass
            else:
                self.logger.log(self.logger.ERROR, traceback.print_exc() + self.whoami())
