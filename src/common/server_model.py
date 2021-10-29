
class ServerModel:
    backendServerID = 0
    serverName = "none"
    IPAddress = "none"
    ASG = "none"
    weight = 0
    backendServerStatus = "disabled"
    lastWeightUpdate = "0-0-0 00:00:00.000000"

    def toString(self):
        return "id:%s ip:%s weight:%s status:%s ASG:%s" % (self.backendServerID, self.IPAddress, self.weight, self.backendServerStatus, self.ASG)

    def equals(self, server):
        if self.backendServerID == server.backendServerID and self.serverName == server.serverName and self.IPAddress == server.IPAddress and self.ASG == server.ASG and self.weight == server.weight and self.backendServerStatus == server.backendServerStatus and self.lastWeightUpdate == server.lastWeightUpdate:
            return True
        return False 
 