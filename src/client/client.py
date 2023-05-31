##
# Imports
##
import threading, sys, time
from client.haproxy import HAProxy
from common.logger import Logger
from common.dynamodb import DynamoDB
from common.configuration import Configuration
from common.server_model import ServerModel
from common.prometheus import Prometheus
from common.dynamodb import DynamoDB
##
# Handle client mode
##
class Client(threading.Thread):
    ##
    # Initialization
    ##
    def __init__(self):
        threading.Thread.__init__(self)
        self.logger = Logger("HSDO.client.client")
        self.haproxy = HAProxy()
        self.dynamodb = DynamoDB()

    def run(self):
        self.dynamodb.checkTableReady()
        self.haproxy.checkSockConf()
        self.haproxy.checkBackendConf()
        oldDynamodbServers = []
        dynamodbServers = []
        while True:
            oldDynamodbServers = dynamodbServers
            dynamodbServers = self.dynamodb.listServers()

            # Remove metric if dynamodb server is removed
            for oldServer in oldDynamodbServers:
                if not self.isServerInList(oldServer, dynamodbServers):
                    self.logger.info("Removed : " + oldServer.toString())
                    Prometheus().removeMetric(oldServer)
            # Display metric if dynamodb server is added
            for dServer in dynamodbServers:
                if not self.isServerInList(dServer, oldDynamodbServers) and dServer.backendServerStatus != "disabled":
                    self.logger.info("Added : " + dServer.toString())
                    Prometheus().serverWeightMetric(dServer)

            for server in dynamodbServers:
                self.haproxy.setServer(server)
            time.sleep(Configuration().get("INTERVAL"))

    def isServerInList(self, server, serverList):
        match = False
        for s in serverList:
            if s.IPAddress == server.IPAddress:
                match = True
        return match
