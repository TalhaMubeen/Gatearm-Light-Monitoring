import logging
import time
import datetime
import sys
import os

class LocalLogger(object):

    #chnage this as per requirements
    __DefaultDiagnosticsDir__ = "E:/logger/"

    #these are logging levels mentioned by logging python lib 
    CRITICAL    = 50
    ERROR	    = 40
    WARNING	    = 30
    INFO	    = 20
    DEBUG	    = 10

    #gives the current system date only
    def __get_current_date__(self):
        return datetime.datetime.now().strftime("%Y-%m-%d")

    def __init__(self, FileName, ApiName):
        """
        initialize the localLogger class object
        parm1 Filename : (String) This will be used for logging 
        parm2 ApiName :  (String) API/Class or any individual function name which is creating the logger object
        use whoami function for this purpose
        """
        self.fileame  = FileName
        self.api_name = ApiName
        self.__Log_Dir__        = self.__DefaultDiagnosticsDir__
        self.__current_date__   = self.__get_current_date__()
        self.__FileHandler__    = None
        self.__diagnostics__    = self.__get_logger_object__()


    def __change_logger_dir_on_date_change__(self):
        """
        call this function on date change to create a new working directory for logging 
        this funcation automatically creates a new file and chnage the filehandler of logging object
        """
        self.__current_date__ = self.__get_current_date__()

        self.__diagnostics__.removeHandler(self.__FileHandler__)
        self.__diagnostics__ = self.__get_logger_object__()


    def log(self, level, str, isDetailed = False):
        """
        This is a public function used to log data
        parm1 level : Interger is the logging level i.e. error / warning / debug etc 
        parm2 str : String to be logged into the file
        """

        if type(level) is int:
            if self.__get_current_date__() != self.__current_date__:
                __change_logger_dir_on_date_change__()

            self.__diagnostics__.log(level, str)
#            self.__diagnostics__.handlers[0].flush()


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
        handler = logging.FileHandler(log_file); #setting the file path
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s : %(message)s" , datefmt='%d-%b-%y %H:%M:%S')
        handler.setFormatter(formatter)
        self.__FileHandler__ = handler
        logger.addHandler(handler)
        return logger
