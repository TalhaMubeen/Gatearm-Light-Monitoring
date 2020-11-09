import Logic
import json
import enum


class CommandTypes(enum.Enum):
    Undefined = 0
    CaptureImage = 1
    UploadFirmware = 2
    UploadConfiguration = 3
    Ping = 4
    Reset = 5
    Progress = 6

    UploadAudio = 8
    UploadImage = 9
    UploadData = 10
    MQTTUploadData = 11

    Set = 12
    Get = 13
    List = 14
    Download = 15
    ActivateNodeFirmware = 16
    DeActivateNodeFirmware = 17
    ActivateGatewayPackage = 18
    FirmwareInfoRequest = 19

    StoreAccelPitchRoll = 20

    GLMStartRecording = 21
    GLMStopRecording = 22


class IPCMessageType(enum.Enum):
    Undefined = 0
    IamAliveMessage = 1
    LiveCommandMessage = 2
    LiveCommandResponse = 3
    SlmNodeMessage = 4


class ApplicationType(enum.Enum):
    Unknown = 0
    CloudCommunicationApplication = 1
    WatchdogApplication = 2
    ZMQForwarderApplication = 3
    SLMNodeApplication = 4
    GLMApplication = 5


class ZMQDataProcessor(object):
    """This class Process the ZMQ Clients Data"""

    def whoami(self):
        """returns the class name as string"""
        return type(self).__name__

    __instance__ = None

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance."""
        return ZMQDataProcessor.__instance__

    def __str_to_json(self, str_data):
        """This module converts string to json object"""
        if type(str_data) is str:
            return json.loads(str_data)
        else:
            return None

    def __init__(self, configs):
        try:
            self.logger = Logic.GetLogger()
            self.__ZMQEIPCommandType__ = {}
            # Setting Static Instance
            if ZMQDataProcessor.__instance__ is None:
                ZMQDataProcessor.__instance__ = self
            self.logger.log(self.logger.INFO, 'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ')
            raise ValueError()
        pass

    def Start(self):
        Logic.GetZMQClient().SetZMQDataRcvCallback(self.OnZMQDataRecieved)
        self.InitZMQCommandsMap()

    def InitZMQCommandsMap(self):
        self.__ZMQEIPCommandType__["GLMStartRecording"] = Logic.GetVideoRecordingProcessor().OnStartRecordingRcvd
        self.__ZMQEIPCommandType__["GLMStopRecording"] = Logic.GetVideoRecordingProcessor().OnStopRecordingRcvd

    def OnZMQDataRecieved(self, data):
        arr = bytearray(data)
        if arr.count(b"i") > 0:
            self.DecodePayload(arr)
        else:
            pass

    def DecodePayload(self, payload):
        payloadIndex = 7
        # Skipping non-used decoding, Un-comment all below lines and make initial value of payloadindex to 1
        # # m_CommandType = int(payload[payloadIndex])
        # # payloadIndex += 1
        # # #if IPCMessageType(m_CommandType) == IPCMessageType.LiveCommandMessage:
        # # isWifiMessage = bool(int(payload[payloadIndex]))
        # # payloadIndex +=1
        # # senderNodeId = int(payload[payloadIndex])
        # # payloadIndex +=1
        # # sourceApp = ApplicationType(int(payload[payloadIndex]))
        # # payloadIndex +=1
        # # destinationApp = ApplicationType(int(payload[payloadIndex]))
        # # payloadIndex +=1
        # # sessionID = int(payload[payloadIndex])
        # # payloadIndex +=1
        nodeIdSize = int(int(payload[payloadIndex]) << 8 | int(payload[payloadIndex + 1]))
        payloadIndex += nodeIdSize + 2
        # pyloadSize = int(payload[payloadIndex] << 8 | payload[payloadIndex+1])
        payloadIndex += 2  # Payload Size Increment
        command = CommandTypes(int(payload[payloadIndex]))
        if self.__ZMQEIPCommandType__.get(command.name) is not None:
            self.__ZMQEIPCommandType__[command.name]()
        pass
