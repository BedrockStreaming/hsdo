##
# Imports
##
import boto3
from typing import List, Any
from common.configuration import Configuration
from common.logger import Logger
from common.server_model import ServerModel
from server.source_interface import SourceInterface

##
# Get AWS Informations
##
class AWS(SourceInterface):
    ##
    # Initialization
    ##
    def __init__(self):
        self.asgClient = boto3.client('autoscaling')
        self.ec2Client = boto3.client('ec2')
        self.asgNames = Configuration().get("SERVER_ASG_NAMES").split(",")
        self.logger = Logger("HSDO.server.aws")

    ##
    # Get Servers available in asg
    ##
    def getServers(self) -> List[ServerModel]:
        servers = []
        instanceIds = []
        asgs = {}

        ## Get instances ids
        asgResponse = self.asgClient.describe_auto_scaling_groups(AutoScalingGroupNames=self.asgNames)

        result = self.readASG(asgResponse)
        instanceIds = result["instanceIds"]
        asgs = result["asgs"]
        # If previous aws request contains a "NextToken", we need to paginate to have all our results.
        # So we need to do what's done before, again and again, while there is a "NextToken" in result
        while result["nextToken"]:
            asgResponse = self.asgClient.describe_auto_scaling_groups(AutoScalingGroupNames=self.asgNames, NextToken = result["nextToken"])
            result = self.readASG(asgResponse)
            instanceIds.extend(result["instanceIds"])
            asgs.extend(result["asgs"])

        # Get instances details
        ec2Response = self.ec2Client.describe_instances(InstanceIds = instanceIds)

        result = self.readEC2(ec2Response, asgs)
        servers = result["servers"]
        # If previous aws request contains a "NextToken", we need to paginate to have all our results.
        # So we need to do what's done before, again and again, while there is a "NextToken" in result
        while result["nextToken"]:
            ec2Response = self.ec2Client.describe_instances(InstanceIds = instanceIds, NextToken = result["nextToken"])
            result = self.readEC2(ec2Response)
            servers.extend(result["servers"])

        return servers

    def readASG(self, response, token = None) -> Any:
        instanceIds = []
        asgs = {}
        nextToken = None
        for asg in response['AutoScalingGroups']:
            for instance in asg['Instances']:
                instanceIds.append(instance['InstanceId'])
                asgs[instance['InstanceId']] = asg['AutoScalingGroupName']
        if "NextToken" in response:
            nextToken = response["NextToken"]

        return {"instanceIds" : instanceIds, "asgs" : asgs, "nextToken" : nextToken}
    
    def readEC2(self, response, asgs) -> Any:
        servers = []
        nextToken = None
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if "PrivateIpAddress" in instance and "InstanceId" in instance and "State" in instance and instance["State"]["Name"] == "running":
                    s = ServerModel()
                    s.IPAddress = instance["PrivateIpAddress"]
                    s.serverName = instance["InstanceId"]
                    s.ASG = asgs[instance["InstanceId"]]
                    servers.append(s)
        if "NextToken" in response:
            nextToken = response["NextToken"]

        return {"servers" : servers, "nextToken" : nextToken}

