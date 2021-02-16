import unittest, sys, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from server.server import Server
from common.server_model import ServerModel
from common.configuration import Configuration
from common.prometheus import Prometheus

class TestServer(unittest.TestCase):

    def testUpdateweight(self):
        os.environ["HAPROXY_BACKEND_SERVER_MIN_WEIGHT"] = "1"
        os.environ["HAPROXY_BACKEND_SERVER_MAX_WEIGHT"] = "10"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL"] = "30"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT"] = "1"
        Configuration()
        s = ServerModel()
        s.lastWeightUpdate = datetime.now().isoformat()
        s.weight = 1
        servers = [s]
        server = Server()
        server.updateWeight(servers)
        self.assertEqual(servers[0].weight, 1)

        s.lastWeightUpdate = (datetime.now() - timedelta(seconds = 40)).isoformat()
        server.updateWeight(servers)
        self.assertEqual(servers[0].weight, 2)

    def testAddServer(self):
        os.environ["HAPROXY_BACKEND_SERVER_MIN_WEIGHT"] = "1"
        os.environ["HAPROXY_BACKEND_SERVER_MAX_WEIGHT"] = "10"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL"] = "30"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT"] = "1"
        Configuration()

        dynamodbServers = [] 
        s = ServerModel()
        s.backendServerID = 1
        s.IPAddress = "6.6.6.6"
        dynamodbServers.append(s)
        s = ServerModel()
        for i in range(2,5):
            s = ServerModel()
            s.backendServerID = i
            dynamodbServers.append(s)
        s = ServerModel()
        s.backendServerID = 5
        s.IPAddress = "1.1.1.1"
        dynamodbServers.append(s)

        sourceServersToAdd = []
        for i in range(2,4):
            s = ServerModel()
            s.backendServerID = i
            s.IPAddress = "%s.%s.%s.%s" % (i, i, i, i)
            sourceServersToAdd.append(s)

        server = Server()
        server.addServer(sourceServersToAdd, dynamodbServers)
        self.assertEqual(dynamodbServers[0].IPAddress, "6.6.6.6")
        self.assertEqual(dynamodbServers[1].IPAddress, "2.2.2.2")
        self.assertEqual(dynamodbServers[2].IPAddress, "3.3.3.3")
        self.assertEqual(dynamodbServers[3].IPAddress, "none")
        self.assertEqual(dynamodbServers[4].IPAddress, "1.1.1.1")

    def testRemoveDoublonServers(self):
        os.environ["HAPROXY_BACKEND_SERVER_MIN_WEIGHT"] = "1"
        os.environ["HAPROXY_BACKEND_SERVER_MAX_WEIGHT"] = "10"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL"] = "30"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT"] = "1"
        Configuration()

        dynamodbServers = [] 
        sourceServers = []
        s = ServerModel()
        s.backendServerID = 1
        s.IPAddress = "6.6.6.6"
        dynamodbServers.append(s)
        sourceServers.append(s)
        s = ServerModel()
        for i in range(2,5):
            s = ServerModel()
            s.backendServerID = i
            s.IPAddress = "%s.%s.%s.%s" % (i, i, i, i)
            dynamodbServers.append(s)
        s = ServerModel()
        s.backendServerID = 5
        s.IPAddress = "1.1.1.1"
        dynamodbServers.append(s)

        for i in range(2,4):
            s = ServerModel()
            s.backendServerID = i
            s.IPAddress = "%s.%s.%s.%s" % (i, i, i, i)
            sourceServers.append(s)
        s = ServerModel()
        s.backendServerID = 7
        s.IPAddress = "7.7.7.7"
        sourceServers.append(s)

        server = Server()
        sourceServersToAdd = server.removeDoublonServers(sourceServers, dynamodbServers)
        self.assertEqual(sourceServersToAdd[0].IPAddress, "7.7.7.7")

    def testRemoveUnexistingServers(self):
        os.environ["HAPROXY_BACKEND_SERVER_MIN_WEIGHT"] = "1"
        os.environ["HAPROXY_BACKEND_SERVER_MAX_WEIGHT"] = "10"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL"] = "30"
        os.environ["HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT"] = "1"
        Configuration()

        dynamodbServers = [] 
        oldDynamodbServers = [] 
        sourceServers = []

        s = ServerModel()
        s.backendServerID = 1
        s.IPAddress = "6.6.6.6"
        s.backendServerStatus = "enabled"
        Prometheus().serverWeightMetric(s)
        dynamodbServers.append(s)
        oldDynamodbServers.append(s)
        s = ServerModel()
        for i in range(2,5):
            s = ServerModel()
            s.backendServerID = i
            s.IPAddress = "%s.%s.%s.%s" % (i, i, i, i)
            s.backendServerStatus = "enabled"
            dynamodbServers.append(s)
            Prometheus().serverWeightMetric(s)
        s = ServerModel()
        s.backendServerID = 5
        s.IPAddress = "1.1.1.1"
        dynamodbServers.append(s)

        for i in range(2,4):
            s = ServerModel()
            s.backendServerID = i
            s.IPAddress = "%s.%s.%s.%s" % (i, i, i, i)
            sourceServers.append(s)
        s = ServerModel()
        s.backendServerID = 7
        s.IPAddress = "7.7.7.7"
        sourceServers.append(s)

        s = ServerModel()
        s.backendServerID = 8
        s.IPAddress = "8.8.8.8"
        Prometheus().serverWeightMetric(s)
        oldDynamodbServers.append(s)

        server = Server()
        server.removeUnexistingServers(dynamodbServers, sourceServers, oldDynamodbServers)

        self.assertEqual(dynamodbServers[0].IPAddress, "none")
        self.assertEqual(dynamodbServers[1].IPAddress, "2.2.2.2")
        self.assertEqual(dynamodbServers[2].IPAddress, "3.3.3.3")
        self.assertEqual(dynamodbServers[3].IPAddress, "none")
        self.assertEqual(dynamodbServers[4].IPAddress, "1.1.1.1")
