##
# Imports
##
from prometheus_client import start_http_server
from prometheus_client import Gauge
from prometheus_client import REGISTRY
from common.logger import Logger
from common.configuration import Configuration
import sys

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

##
# Export metrics to prometheus
##
class Prometheus:
    __metaclass__ = SingletonMetaClass
    gauge = Gauge("hsdo_server_weight", "Weight of server in backend", ["id", "name", "ip", "asg"])
    logger = Logger("hsdo.prometheus")

    def startServer(self):
        start_http_server(Configuration().get("EXPORTER_PORT"))

    def removeMetric(self, server):
        try:
            self.gauge.remove(server.backendServerID, server.serverName, server.IPAddress, server.ASG)
        except:
            self.logger.error("Unexpected error: %s" % sys.exc_info()[0])

    def serverWeightMetric(self, server):
        self.gauge.labels(server.backendServerID, server.serverName, server.IPAddress, server.ASG).set(server.weight)
