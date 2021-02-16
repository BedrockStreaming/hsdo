import unittest, sys, os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from common.dynamodb import DynamoDB

class TestDynamoDB(unittest.TestCase):
    
    def testFillServer(self):
        item={
            "ServerName": "i-054512545121",
            "BackendServerStatus": "enabled",
            "ASG": "ASG1",
            "Weight": 10,
            "IPAddress": "10.0.0.1",
            "LastWeightUpdate": "2020-11-12 17:29:08.597604",
            "BackendServerID": 1
        }
        dynamodb = DynamoDB()
        server = dynamodb.fillServer(item)
        self.assertEqual(server.backendServerID, 1)
        self.assertEqual(server.serverName, "i-054512545121")
        self.assertEqual(server.IPAddress, "10.0.0.1")
        self.assertEqual(server.ASG , "ASG1")        
        self.assertEqual(server.weight, 10)
        self.assertEqual(server.backendServerStatus, "enabled")
        self.assertEqual(server.lastWeightUpdate, "2020-11-12 17:29:08.597604")

