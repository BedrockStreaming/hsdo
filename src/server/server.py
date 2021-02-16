##
# Imports
##
import threading, time, sys
from typing import List
from datetime import datetime, timedelta

from server.source.aws import AWS
from server.source.consul import Consul
from server.source_interface import SourceInterface
from common.logger import Logger
from common.dynamodb import DynamoDB
from common.configuration import Configuration
from common.server_model import ServerModel
from common.prometheus import Prometheus

##
# Handle server mode
##
class Server(threading.Thread):
    ##
    # Initialization
    ##
    def __init__(self):
        threading.Thread.__init__(self)
        self.mode = Configuration().get("SERVER_MODE")
        self.logger = Logger("HSDO.server.server")
        self.source = None
        self.dynamodb = DynamoDB()
        self.backendListSize = Configuration().get("HAPROXY_BACKEND_SERVERS_LIST_SIZE")
        self.minWeight = int(Configuration().get("HAPROXY_BACKEND_SERVER_MIN_WEIGHT"))
        self.maxWeight = int(Configuration().get("HAPROXY_BACKEND_SERVER_MAX_WEIGHT"))
        self.increaseWeight = int(Configuration().get("HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT"))
        self.increaseWeightInterval = int(Configuration().get("HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL"))

    def run(self):
        self.dynamodb.checkTableReady()
        if self.mode == "aws":
            self.source = AWS()
        elif self.mode == "consul":
            self.source = Consul()
        else:
            self.logger.error("Server mode could be [aws|consul], %s is given" % (self.mode))
            sys.exit(2)

        oldDynamodbServers = []
        dynamodbServers = []
        while True:
            sourceServers = self.source.getServers()
            if sourceServers == None:
                time.sleep(Configuration().get("INTERVAL"))
                continue

            oldDynamodbServers = dynamodbServers
            dynamodbServers = self.dynamodb.listServers()

            # Need to create backend servers if not found in dynamodb
            if not dynamodbServers:
                for i in range (1, self.backendListSize +1):
                    server = ServerModel()
                    server.backendServerID = i
                    self.dynamodb.createServer(server)
                    dynamodbServers.append(server)

            if len(dynamodbServers) < self.backendListSize:
                self.logger.info("Creating missing servers.")
                for i in range (len(dynamodbServers) + 1, self.backendListSize +1):
                    server = ServerModel()
                    server.backendServerID = i
                    self.dynamodb.createServer(server)
                    dynamodbServers.append(server)

            if len(dynamodbServers) > self.backendListSize:
                self.logger.error("HAProxy backend size is lower than registered servers in dynamoDB. Please correct it by hand.")
                sys.exit(2)

            # Remove servers that does not exists anymore
            self.removeUnexistingServers(dynamodbServers, sourceServers, oldDynamodbServers)

            # Do not keep track of already registered servers
            sourceServersToAdd = self.removeDoublonServers(sourceServers, dynamodbServers)

            # Add new servers
            self.addServer(sourceServersToAdd, dynamodbServers)

            # Update weight for newly registered servers
            self.updateWeight(dynamodbServers)

            # Update list
            for server in dynamodbServers:
                if server.backendServerStatus == "enabled":
                    Prometheus().serverWeightMetric(server)
                
                match = False
                #Update only modified servers
                for oldServer in oldDynamodbServers:
                    if server.equals(oldServer):
                        match = True
                if not match:
                    self.logger.debug(server.toString())
                    self.dynamodb.updateServer(server)

            time.sleep(Configuration().get("INTERVAL"))

    # Update weight for newly registered servers
    def updateWeight(self, dynamodbServers : List[ServerModel]):
        for server in dynamodbServers:
            if server.weight >= self.minWeight and server.weight < self.maxWeight and (datetime.now() - datetime.fromisoformat(server.lastWeightUpdate)) > timedelta(seconds=self.increaseWeightInterval):                
                self.logger.debug("Need to update weight of %s:%s to %s" % (server.backendServerID, server.IPAddress, str(server.weight + 1)) )
                server.lastWeightUpdate = str(datetime.now())
                server.weight = server.weight + self.increaseWeight
                if server.weight > self.maxWeight:
                    server.weight = self.maxWeight

    def addServer(self, sourceServersToAdd : List[ServerModel], dynamodbServers : List[ServerModel]):
        for sServer in sourceServersToAdd:
            for dServer in dynamodbServers:
                if dServer.IPAddress == "none":
                    dServer.IPAddress = sServer.IPAddress
                    dServer.serverName = sServer.serverName
                    dServer.ASG = sServer.ASG
                    dServer.backendServerStatus = "enabled"
                    dServer.lastWeightUpdate = str(datetime.now())
                    dServer.weight = 1
                    self.logger.info("Added : " + dServer.toString())
                    break

    # Do not keep track of already registered servers
    def removeDoublonServers(self, sourceServers : List[ServerModel], dynamodbServers : List[ServerModel]) ->  List[ServerModel]:
        sourceServersToAdd = []
        while sourceServers:
            match = False
            sServer = sourceServers.pop()
            for dServer in dynamodbServers:
                if sServer.IPAddress == dServer.IPAddress:
                    match = True
            if not match:
                sourceServersToAdd.append(sServer)
        return sourceServersToAdd

    # Remove servers that does not exists anymore
    def removeUnexistingServers(self, dynamodbServers : List[ServerModel], sourceServers : List[ServerModel], oldDynamodbServers : List[ServerModel]):
        for oldServer in oldDynamodbServers:
            match = False
            for dServer in dynamodbServers:
                if oldServer.IPAddress == dServer.IPAddress:
                    match = True
            if not match:
                Prometheus().removeMetric(oldServer)
                self.logger.info("Removed : " + oldServer.toString())
        for dServer in dynamodbServers:
            match = False
            for sServer in sourceServers:
                if sServer.IPAddress == dServer.IPAddress:
                    match = True
            if not match and dServer.backendServerStatus != "disabled":
                Prometheus().removeMetric(dServer)
                self.logger.info("Removed : " + dServer.toString())
                dServer.backendServerStatus = "disabled"
                dServer.ASG = "none"
                dServer.serverName = "none"
                dServer.IPAddress = "none"
                dServer.lastWeightUpdate = "0-0-0 00:00:00.000000"
                dServer.weight = 0
        
