##
# Imports
##
import os, socket, sys, time
from common.configuration import Configuration
from common.logger import Logger
from common.server_model import ServerModel

##
# Configure HAProxy through Runtime API
##
class HAProxy:
    ##
    # Initialization
    ##
    def __init__(self):
        self.azLimiter = Configuration().get("CLIENT_DEDICATED_ASG")
        self.optAllServersInFallback = Configuration().get("CLIENT_ALL_SERVERS_IN_FALLBACK_BACKEND")
        self.socketPath = Configuration().get("CLIENT_HAPROXY_SOCKET_PATH")
        self.backendList = Configuration().get("CLIENT_HAPROXY_BACKEND_LIST")
        ## Example backendList structure:
        # self.backendList = {
        #     "backend-web": {
        #         "baseName": "web-backend",
        #         "serverPort": "80"
        #     },
        #     "backend-api": {
        #         "baseName": "api-backend",
        #         "serverPort": "8080"
        #     }
        # }
        self.backendServerPort = str(Configuration().get("CLIENT_HAPROXY_BACKEND_SERVER_PORT"))
        self.fallbackBackendName = Configuration().get("CLIENT_HAPROXY_FALLBACK_BACKEND_NAME")
        self.fallbackBackendBaseName = Configuration().get("CLIENT_HAPROXY_FALLBACK_BACKEND_BASE_NAME")
        self.ASG = Configuration().get("CLIENT_ASG_NAMES").split(",")
        self.logger = Logger("HSDO.client.haproxy")

    def checkSockConf(self):
        check = self.sockConfExists()
        while not check["result"]:
            self.logger.error(check["message"])
            time.sleep(3)

    def sockConfExists(self):
        if not os.path.exists(self.socketPath):
            return {"result": False, "message": "Socket %s not found, please set env var CLIENT_HAPROXY_SOCKET_PATH correctly" % self.socketPath}
        return {"result": True, "message": ""}

    def checkBackendConf(self):
        stat = self.sendHaproxyCommand("show stat")
        check = self.backendConfReady(stat)
        if not check["result"]:
            self.logger.error(check["message"])
            sys.exit(2)

    def backendConfReady(self, stat):
        stat = stat.split("\n")
        backendsExist = False
        existingBackends = 0
        fallbackBackendExists = False
        for backend in stat:
            values = backend.split(",")
            ## Example backend line
            ## http_back,mywebapp2,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,
            for k,v in self.backendList.items():
                if values[0] == k and values[1].startswith(v["baseName"]):
                    existingBackends += 1
            if self.azLimiter == "true" and len(values) > 80 and values[0] == self.fallbackBackendName and values[1].startswith(self.fallbackBackendBaseName):
                fallbackBackendExists = True
            if existingBackends == len(self.backendList):
                backendsExist = True
        
        result = True
        message = ""
        if not backendsExist:
            result = False
            message = "Backend(s) not found, please set env CLIENT_HAPROXY_BACKEND_LIST correctly\n"
        if self.azLimiter == "true" and not fallbackBackendExists:
            result = False
            message += "Backend %s/%s not found, please set env CLIENT_HAPROXY_FALLBACK_BACKEND_NAME and CLIENT_HAPROXY_FALLBACK_BACKEND_BASE_NAME correctly" % (self.fallbackBackendName, self.fallbackBackendBaseName)
        return {"result": result, "message": message}

    def setServer(self, server):
        commands = self.prepareServer(server)
        for command in commands:
            self.sendHaproxyCommand(command)

    def prepareServer(self, server):
        # If --az-limiter option is used
        if server.ASG not in self.ASG and self.azLimiter == "true":
            return self.__addServerInBackend(server, self.fallbackBackendName, self.fallbackBackendBaseName, self.backendServerPort)
        # Read backend list
        commands = []
        for k,v in self.backendList.items():
            commands.extend(self.__addServerInBackend(server, k, v["baseName"], v["serverPort"]))
            if self.optAllServersInFallback == "true":
                commands.extend(self.__addServerInBackend(server, self.fallbackBackendName, self.fallbackBackendBaseName, self.backendServerPort))
        return commands

    def __addServerInBackend(self, server, bckndName, bckndbsName, bckndServerPort):
        commands = []
        if server.IPAddress == "none":
            commands.append(
                "set server %s/%s state maint"
                % (
                    bckndName,
                    bckndbsName + str(server.backendServerID)
                )
            )
        ## If server is enabled
        else:
            commands.append(
                "set server %s/%s addr %s port %s"
                % (
                    bckndName,
                    bckndbsName + str(server.backendServerID),
                    server.IPAddress,
                    bckndServerPort,
                )
            )
            commands.append(
                "set server %s/%s weight %s"
                % (
                    bckndName,
                    bckndbsName + str(server.backendServerID),
                    server.weight,
                )
            )
            commands.append(
                "set server %s/%s state ready"
                % (
                    bckndName,
                    bckndbsName + str(server.backendServerID),
                )
            )
        return commands

    ##
    # Send command to HAProxy Runtime API socket
    # https://cbonte.github.io/haproxy-dconv/2.0/management.html#9.3
    ##
    def sendHaproxyCommand(self, command):
        self.logger.debug(command)
        command = command + "\n"
        haproxySock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        haproxySock.settimeout(10)
        try:
            haproxySock.connect(self.socketPath)
            haproxySock.send(command.encode("utf-8"))
            retval = ""
            while True:
                buf = haproxySock.recv(16)
                if buf:
                    retval += buf.decode("utf-8")
                else:
                    break
            haproxySock.close()
        except:
            retval = ""
        finally:
            haproxySock.close()
        return retval
