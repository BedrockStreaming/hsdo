##
# Imports
##
import logging
from common.configuration import Configuration

class SingletonMetaClass(type):
    def __init__(cls,name,bases,dict):
        super(SingletonMetaClass,cls)\
          .__init__(name,bases,dict)
        original_new = cls.__new__
        def my_new(cls,*args,**kwds):
            if cls.instance == None:
                cls.instance = \
                  original_new(cls,*args,**kwds)
            return cls.instance
        cls.instance = None
        cls.__new__ = staticmethod(my_new)

class Loggers:
    loggers = {}
    __metaclass__ = SingletonMetaClass

    def getLogger(self, name):
        if name in self.loggers.keys():
            return self.loggers[name]

        # Configure logging
        logger = logging.getLogger(name)
        if Configuration().get("DEBUG") == "true":
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        streamHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)
        self.loggers[name] = logger
        return logger

##
# Short class to handle logging
##
class Logger:
    ##
    # Initialization
    ##
    def __init__(self, name):
        self.logger = Loggers().getLogger(name)
          
    ##
    # Info messages
    ##
    def info(self, message):
        self.logger.info("\033[0;0m%s\033[0;0m" % str(message))

    ##
    # Error message
    ##
    def error(self, message):
        self.logger.error("\033[1;31m%s\033[0;0m" % str(message))

    ##
    # Debug messages
    ##
    def debug(self, message):
        self.logger.debug("\033[0;32m%s\033[0;0m" % str(message))
