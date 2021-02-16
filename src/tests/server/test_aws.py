import unittest, sys, os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from common.server_model import ServerModel
from server.source.aws import AWS

class TestAWS(unittest.TestCase):

    def testRead(self):
        aws = AWS()
        response = {
            'AutoScalingGroups': [
                {
                    'AutoScalingGroupName' : "asg1",
                    'Instances': [
                        {
                            'InstanceId': 'instance1',
                        },
                        {
                            'InstanceId': 'instance2',
                        },
                        {
                            'InstanceId': 'instance3',
                        },
                    ],
                },
                {
                    'AutoScalingGroupName' : "asg2",
                    'Instances': [
                        {
                            'InstanceId': 'instance4',
                        },
                        {
                            'InstanceId': 'instance5',
                        },
                        {
                            'InstanceId': 'instance6',
                        },
                    ],
                },
            ],
        }
        result = aws.readASG(response)

        self.assertEqual(result["instanceIds"][0], "instance1")
        self.assertEqual(result["instanceIds"][1], "instance2")
        self.assertEqual(result["asgs"][result["instanceIds"][0]], "asg1")
        self.assertEqual(result["asgs"][result["instanceIds"][1]], "asg1")
    
        response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'instance2',
                            'PrivateIpAddress': '2.2.2.2',
                            'State': {
                                'Name': 'stopping'
                            }
                        },
                        {
                            'InstanceId': 'instance1',
                            'PrivateIpAddress': '1.1.1.1',
                            'State': {
                                'Name': 'running'
                            }
                        },
                    ],
                },
            ],
        }
        result = aws.readEC2(response, result["asgs"])
        self.assertEqual(result["servers"][0].IPAddress, "1.1.1.1")
        self.assertEqual(len(result["servers"]), 1)
