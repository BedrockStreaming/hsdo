import unittest, sys, os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from client.haproxy import HAProxy
from common.configuration import Configuration
from common.server_model import ServerModel

class TestHAProxy(unittest.TestCase):
    
    def testCheckSockConf(self):
        """
        Test that check sock file is ok
        """
        os.environ["HAPROXY_SOCKET_PATH"] = "/tmp/haproxy.sock"
        Configuration()
        haproxy = HAProxy()
        self.assertFalse(haproxy.sockConfExists()["result"])

    
    def testBackendConfReadyIfGoodBackend(self):
        """
        Test that check backend conf is ok
        """
        os.environ["AZ_LIMITER"] = "false"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        Configuration()
        haproxy = HAProxy()
        stat = "test,test1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,"
        self.assertTrue(haproxy.backendConfReady(stat)["result"])

    def testBackendConfReadyIfGoodFallbackBackend(self):
        """
        Test that check backend conf fallback is ok
        """
        os.environ["AZ_LIMITER"] = "true"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        os.environ["HAPROXY_FALLBACK_BACKEND_NAME"] = "test_b"
        os.environ["HAPROXY_FALLBACK_BACKEND_BASE_NAME"] = "test_b"
        Configuration()
        haproxy = HAProxy()
        stat = "test,test1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,\n"
        stat += "test_b,test_b1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,"
        self.assertTrue(haproxy.backendConfReady(stat)["result"])

    def testBackendConfReadyIfBadBackend(self):
        """
        Test that check backend conf if bad backend is ok
        """
        os.environ["AZ_LIMITER"] = "false"
        os.environ["HAPROXY_BACKEND_NAME"] = "bad"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        Configuration()
        haproxy = HAProxy()
        stat = "test,test1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,"
        self.assertFalse(haproxy.backendConfReady(stat)["result"])
        self.assertEqual(haproxy.backendConfReady(stat)["message"], "Backend bad/test not found, please set env HAPROXY_BACKEND_NAME and HAPROXY_BACKEND_BASE_NAME correctly\n")

    def testBackendConfReadyIfBadBackendBase(self):
        """
        Test that check backend conf if bad backend is ok
        """
        os.environ["AZ_LIMITER"] = "false"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "bad"
        Configuration()
        haproxy = HAProxy()
        stat = "test,test1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,"
        self.assertFalse(haproxy.backendConfReady(stat)["result"])
        self.assertEqual(haproxy.backendConfReady(stat)["message"], "Backend test/bad not found, please set env HAPROXY_BACKEND_NAME and HAPROXY_BACKEND_BASE_NAME correctly\n")

    def testBackendConfReadyIfBadFallbackBackend(self):
        """
        Test that check backend conf if bad falback is ok
        """
        os.environ["AZ_LIMITER"] = "true"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        os.environ["HAPROXY_FALLBACK_BACKEND_NAME"] = "bad"
        os.environ["HAPROXY_FALLBACK_BACKEND_BASE_NAME"] = "test_b"
        Configuration()
        haproxy = HAProxy()
        stat = "test,test,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,\n"
        stat += "test_b,test_b1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,"
        self.assertFalse(haproxy.backendConfReady(stat)["result"])
        self.assertEqual(haproxy.backendConfReady(stat)["message"], "Backend bad/test_b not found, please set env HAPROXY_FALLBACK_BACKEND_NAME and HAPROXY_FALLBACK_BACKEND_BASE_NAME correctly")

    def testBackendConfReadyIfBadFallbackBackendBase(self):
        """
        Test that check backend conf if bad fallback is ok
        """
        os.environ["AZ_LIMITER"] = "true"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        os.environ["HAPROXY_FALLBACK_BACKEND_NAME"] = "test_b"
        os.environ["HAPROXY_FALLBACK_BACKEND_BASE_NAME"] = "bad"
        Configuration()
        haproxy = HAProxy()
        stat = "test,test1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,\n"
        stat += "test_b,test_b1,0,0,0,0,,0,0,0,,0,,0,0,0,0,UP,10,1,0,0,1,330587,0,,1,4,2,,0,,2,0,,0,L4OK,,0,0,0,0,0,0,0,,,,,0,0,,,,,-1,,,0,0,0,0,,,,Layer4 check passed,,2,3,4,,,,10.14.34.198:80,,http,,,,,,,,0,0,0,,,0,,0,0,0,0,"
        self.assertFalse(haproxy.backendConfReady(stat)["result"])
        self.assertEqual(haproxy.backendConfReady(stat)["message"], "Backend test_b/bad not found, please set env HAPROXY_FALLBACK_BACKEND_NAME and HAPROXY_FALLBACK_BACKEND_BASE_NAME correctly")

    def testPrepareFallbackDisabledServer(self):
        """
        Test that prepare fallback disabled server is ok
        """
        os.environ["AZ_LIMITER"] = "true"
        os.environ["HAPROXY_FALLBACK_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_FALLBACK_BACKEND_BASE_NAME"] = "test"
        Configuration()
        haproxy = HAProxy()
        server = ServerModel()
        server.IPAddress = "none"
        server.backendServerID = 1
        commandsMock = ["set server test/test1 state maint"]
        commands = haproxy.prepareServer(server)

        self.assertEqual(commands, commandsMock)

    def testPrepareDisabledServer(self):
        """
        Test that prepare disabled server is ok
        """
        os.environ["AZ_LIMITER"] = "false"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        Configuration()
        haproxy = HAProxy()
        server = ServerModel()
        server.IPAddress = "none"
        server.backendServerID = 1
        commandsMock = ["set server test/test1 state maint"]
        commands = haproxy.prepareServer(server)

        self.assertEqual(commands, commandsMock)

    def testPrepareEnabledServer(self):
        """
        Test that prepare enabled server is ok
        """
        os.environ["AZ_LIMITER"] = "false"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_SERVER_PORT"] = "8765"
        Configuration()
        haproxy = HAProxy()
        server = ServerModel()
        server.IPAddress = "10.0.0.1"
        server.weight = 10
        server.backendServerID = 1
        commandsMock = [
            "set server test/test1 addr 10.0.0.1 port 8765",
            "set server test/test1 weight 10",
            "set server test/test1 state ready",
        ]
        commands = haproxy.prepareServer(server)

        self.assertEqual(commands, commandsMock)


    def testPrepareFallbackEnabledServer(self):
        """
        Test that prepare fallback enabled server is ok
        """
        os.environ["AZ_LIMITER"] = "true"
        os.environ["HAPROXY_BACKEND_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_BASE_NAME"] = "test"
        os.environ["HAPROXY_BACKEND_SERVER_PORT"] = "8765"
        Configuration()
        haproxy = HAProxy()
        server = ServerModel()
        server.IPAddress = "10.0.0.1"
        server.weight = 10
        server.backendServerID = 1
        commandsMock = [
            "set server test/test1 addr 10.0.0.1 port 8765",
            "set server test/test1 weight 10",
            "set server test/test1 state ready",
        ]
        commands = haproxy.prepareServer(server)

        self.assertEqual(commands, commandsMock)
