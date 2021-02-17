##
# Imports
##
from typing import List, Any
import urllib3, urllib.parse, json, os
from common.configuration import Configuration
from common.logger import Logger
from common.server_model import ServerModel
from server.source_interface import SourceInterface

##
# Get Consul Informations
##
class Consul(SourceInterface):
    ##
    # Initialization
    ##
    def __init__(self):
        self.url = Configuration().get("SERVER_CONSUL_API_URL")
        if "," in Configuration().get("SERVER_CONSUL_SERVICE_NAME"):
            self.service = Configuration().get("SERVER_CONSUL_SERVICE_NAME").split(",")
        else:
            self.service = Configuration().get("SERVER_CONSUL_SERVICE_NAME")
        self.logger = Logger("HSDO.server.consul")

    ##
    # Get Servers available in consul service
    ##
    def getServers(self) -> List[ServerModel]:
        self.logger.debug("Get service information : %s" % self.service)
        http = urllib3.PoolManager()
        data = ""
        headers = {'Accept': 'application/json'}
        servers = []
        
        if type(self.service) is str:
            servers = self.__handleRequest(http, data, headers, self.service)
        elif type(self.service) is list:
            for service in self.service:
                result = self.__handleRequest(http, data, headers, service)
                if result == None:
                    servers = None
                    break; 
                else:
                    servers += result 
        return servers

    def __handleRequest(self, http, data, headers, service) -> List[ServerModel]:
        servers = []
        response = http.request(
            "GET",
            "%s/v1/catalog/service/%s" % (self.url, service),
            body=data.encode('utf-8'),
            headers=headers
        )
        if response.status != 200:
            self.logger.error("Consul reponse error %s : %s" % (response.status, response.data))
            return None
        for server in json.loads(response.data.decode('utf-8')):
            s = ServerModel()
            s.IPAddress = server["Address"]
            s.serverName = server["Node"]
            servers.append(s)
        return servers

    
