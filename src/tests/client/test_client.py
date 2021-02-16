import unittest, sys, os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from client.client import Client
from common.configuration import Configuration
from common.server_model import ServerModel

class TestClient(unittest.TestCase):
    
    def testIsServerInList(self):
        """
        Test that server is in list
        """
        Configuration()
        client = Client()
        server = ServerModel()
        server.IPAddress = "10.0.0.1"
        serverList = []
        for i in range(1,6):
            s = ServerModel()
            s.IPAddress = "10.0.0." + str(i)
            serverList.append(s)
        self.assertTrue(client.isServerInList(server, serverList))
        serverList.pop(0)
        self.assertFalse(client.isServerInList(server, serverList))

