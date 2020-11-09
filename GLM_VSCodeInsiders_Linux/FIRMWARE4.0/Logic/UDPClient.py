import Logic
import subprocess as sp
import time
import threading

TOTAL_DOTS_IN_IPADDRESS = 3
EIP_UDP_SERVER_PORT = 5050


class UDPClient(object):
    __instance__ = None
    """This class is responsible for UDP handshake with EIP, This class is to be used as Singleton Class"""

    def whoami(self):
        """returns the class name as string"""
        return type(self).__name__

    def __init__(self, configs):
        try:
            self.logger = Logic.GetLogger()
            self.MY_ID = configs['GLM']['MY_ID']
            self.EIP_IP_ADDRESS = ""
            th = threading.Thread(target=self.Process)
            th.start()
            if UDPClient.__instance__ is None:
                UDPClient.__instance__ = self
            self.logger.log(self.logger.INFO, 'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ')
            raise ValueError()
        pass

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance."""
        return UDPClient.__instance__

    def GetSystemCmdOutput(self, cmd):
        ret = sp.check_output(cmd, shell=True, universal_newlines=True)
        ret = ret.replace('\n', '')
        return ret

    def SetEIPIPAddress(self, eip_ip):
        if self.EIP_IP_ADDRESS is not eip_ip:
            self.EIP_IP_ADDRESS = eip_ip
            self.logger.log(self.logger.INFO, 'EIP IP ADDRESS : ' + str(eip_ip))


    def SendHandshakeMessage(self):
        """This Sends Handshake Message Over UDP Broadcast Network Address Format => {MY_IP, MY_MAC, RSSI,
        EIP_IP_ADDRESS} """
        IPAddress = self.GetSystemCmdOutput("ifconfig wlan0 | awk '$1 == \"inet\" {print $2}'")

        if IPAddress.count(".") == TOTAL_DOTS_IN_IPADDRESS:
            BroadCastAddress = self.GetSystemCmdOutput("ifconfig wlan0 | awk '$1 == \"inet\" {print $6}'")
            # MacAddress = self.GetSystemCmdOutput("ifconfig wlan0 | awk '$1 == \"ether\" {print $2}'")
            # MacAddress = MacAddress.replace(":", '')

            RSSI = self.GetSystemCmdOutput("iw dev wlan0 link | awk '$1 == \"signal:\" {print $2}'")

            # Formating Command to send data over UDP Port using NetCat
            cmd = ("echo '" + IPAddress + "," + self.MY_ID + "," + RSSI + "," + self.EIP_IP_ADDRESS + "' | nc -ub " + BroadCastAddress + " " + str(EIP_UDP_SERVER_PORT) + " -w 1")
            self.GetSystemCmdOutput(cmd)
        else:
            pass

    def Process(self):
        while True:
            self.SendHandshakeMessage()
            time.sleep(20)
