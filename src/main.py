##
# Imports
##
import os, sys, getopt, pprint
from datetime import datetime
from common.logger import Logger
from server.server import Server
from client.client import Client
from common.configuration import Configuration
from common.prometheus import Prometheus

##
# Usage
##
def usage():
    print('main.py <options>')
    print(' -c, --client  enable client mode')
    print(' -s, --server  enable server mode')
    print(' -d, --debug  enable debug mode')
    print(' -s, --server  enable server mode')

###
# Main
##
def main(argv):
    ##
    # Handle command line params
    ##
    mode = None
    try:
        opts, args = getopt.getopt(argv[0:],"hdsc", ["help", "debug", "server", "client"])
    except getopt.GetoptError:
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-d", "--debug"):
            os.environ["DEBUG"] = "true"
        elif opt in ("-s", "--server") and opt in ("-c", "--client"):
            print("Client and server mode are mutually exclusive")
            sys.exit(2)
        elif opt in ("-s", "--server"):
            mode = "server"
        elif opt in ("-c", "--client"):
            mode = "client"

    ##
    # Prepare logger
    ##
    logger = Logger("HSDO.main")

    ##
    # Handle configuration
    ##
    Configuration()

    Prometheus().startServer()
    if mode == "server":
        server = Server()
        server.start()
    elif mode == "client":
        client = Client()
        client.start()

##
# Launch only if src/main.py if called directly with python3 command line
##
if __name__ == "__main__":
    main(sys.argv[1:])
