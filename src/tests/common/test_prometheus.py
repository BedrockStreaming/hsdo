import unittest, sys, os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from common.prometheus import Prometheus
from common.server_model import ServerModel

class TestPrometheus(unittest.TestCase):
    
    def testMetric(self):
        prometheus = Prometheus()

        server = ServerModel()
        server.backendServerID = 1
        server.serverName = "i-009249e852ef68dfe"
        server.IPAddress = "10.17.10.189"
        server.ASG = "usp-origin-eu-west-1b-rtlmutu"    
        server.weight = 10
        server.backendServerStatus = "enabled"
        server.lastWeightUpdate = "2020-11-12 17:29:08.597604"

        prometheus.serverWeightMetric(server)
        prometheus.removeMetric(server)



