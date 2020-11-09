import Logic
import time
import zmq
import threading


class WIFIZMQClient(object):
    """This class is responsible to establish zmq communication """
    def whoami(self):
        """returns the class name as string"""
        return type(self).__name__

    __instance__ = None

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance."""
        return WIFIZMQClient.__instance__

    def __init__(self, configs):
        try:
            self.logger = Logic.GetLogger()
            self.__eip_address__ = ""
            self.__sub__ = None
            self.__pub__ = None
            self.__message__ = None
            self.__zmq_ctx__ = None
            # Binding Subscriber to generic socket
            self.__ConnectSubscriber__()
            self.OnDataRcvCallback = None
            th = threading.Thread(target=self.Process)
            th.start()
            # Setting Static Object
            if WIFIZMQClient.__instance__ is None:
                WIFIZMQClient.__instance__ = self
            self.logger.log(self.logger.INFO, 'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ')
            raise ValueError()
        pass

    def SetZMQDataRcvCallback(self, callback):
        self.OnDataRcvCallback = callback

    def __ConnectSubscriber__(self):
        """This Subscribes to all topics"""
        context = zmq.Context()
        self.__sub__ = context.socket(zmq.SUB)
        self.__sub__.setsockopt(zmq.SUBSCRIBE, b'')
        self.__sub__.bind("tcp://*:6669")
        time.sleep(1)

    def __ConnectPubSocket__(self, eip_ip):
        pub_ip = "tcp://" + eip_ip + ":6666"
        if self.__pub__ is not None:
            # New EIP IP ADDRESS is different from the prev EIP IP ADDRESS
            self.__pub__.disconnect(pub_ip)
            self.__pub__.close()
            self.__pub__ = None
            self.__eip_address__ = ""

        if self.__pub__ is None:
            # Connect to the given EIP IP ADDRESS
            self.__eip_address__ = eip_ip
            context = zmq.Context()
            self.__pub__ = context.socket(zmq.PUB)
            self.__sub__.connect(pub_ip)
            time.sleep(2)

    def SendMessage(self, data):
        if self.__pub__ is None:
            return
        data = "i" + data
        self.__pub__.send(data)

    def ProcessRcvdData(self, data):
        if data is None:
            return
        str_data = data.decode("utf-8")
        if str_data.count('@') > 0:  # we recieved EIP IP Address
            eip_address = str_data.replace('@', '')
            Logic.GetUDPClient().SetEIPIPAddress(eip_address)

            if self.__eip_address__ != eip_address:
                # Eastablishing Publish Socket using EIP IP ADDRESS
                self.__ConnectPubSocket__(eip_address)

            else:
                # do nothing we have already eastblished socket with current EIP IP ADDRESS
                pass
        else:
            self.OnDataRcvCallback(data)

    def Process(self):
        while True:
            if self.__sub__ is None:
                return
            try:
                raw_msg = self.__sub__.recv(flags=zmq.NOBLOCK, copy=True)
                if len(raw_msg) > 0:
                    # raw_msg = raw_msg.replace('\n', '')
                    self.ProcessRcvdData(raw_msg)
                else:
                    pass
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    pass
                else:
                    self.logger.log(self.logger.ERROR, "ZMQ Socket ERROR")
            time.sleep(20 / 1000)
