# __init__.py
from .UDPClient import UDPClient
from .HttpClient import HttpClient
from .MQTTClient import MQTTClient
from .Diagnostics import LocalLogger
from .LedDetector import LedDetector
from .BlinkCounter import BlinkCounter
from .RepeatedTimer import PeriodicTimer
from .WIFIZMQClient import WIFIZMQClient
from .VideoRecorder import VideoRecorder
from .ZMQDataProcessor import ZMQDataProcessor
from .MQTTDataProcessor import MQTTDataProcessor
from .LiveCommandHandler import LiveCommandHandler
from .VideoRecordingProcessor import VideoRecordingProcessor

def GetUDPClient():
    return UDPClient.Instance()

def GetHTTPClient():
    return HttpClient.Instance()

def GetMQTTClient():
    return MQTTClient.Instance()

def GetLedDetector():
    return LedDetector.Instance()

def GetBlinkCounter():
    return BlinkCounter.Instance()

def GetZMQClient():
    return WIFIZMQClient.Instance()

def GetVideoRecorder():
    return VideoRecorder.Instance()

def GeZMQDataProcessor():
    return ZMQDataProcessor.Instance()

def GetMQTTDataProcessor():
    return MQTTDataProcessor.Instance()

def GetLiveCmdHandler():
    return LiveCommandHandler.Instance()

def GetVideoRecordingProcessor():
    return VideoRecordingProcessor.Instance()

def GetLogger():
    return LocalLogger.Instance()
