import unittest, sys, os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from common.dynamodb import DynamoDB

class TestDynamoDB(unittest.TestCase):
    
    def testFillServer(self):
        item={
            "ServerName": "i-009249e852ef68dfe",
            "BackendServerStatus": "enabled",
            "ASG": "usp-origin-eu-west-1b-rtlmutu",
            "Weight": 10,
            "IPAddress": "10.17.10.189",
            "LastWeightUpdate": "2020-11-12 17:29:08.597604",
            "BackendServerID": 1
        }
        dynamodb = DynamoDB()
        server = dynamodb.fillServer(item)
        self.assertEqual(server.backendServerID, 1)
        self.assertEqual(server.serverName, "i-009249e852ef68dfe")
        self.assertEqual(server.IPAddress, "10.17.10.189")
        self.assertEqual(server.ASG , "usp-origin-eu-west-1b-rtlmutu")        
        self.assertEqual(server.weight, 10)
        self.assertEqual(server.backendServerStatus, "enabled")
        self.assertEqual(server.lastWeightUpdate, "2020-11-12 17:29:08.597604")

