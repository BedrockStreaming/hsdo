##
# Imports
##
import boto3, json, sys
from botocore.exceptions import ClientError
from common.configuration import Configuration
from common.server_model import ServerModel
from common.logger import Logger


class DynamoDB:
    def __init__(self):
        dynamodb = boto3.resource('dynamodb')
        self.logger = Logger("HSDO.dynamodb")
        self.table = dynamodb.Table(Configuration().get("DYNAMODB_TABLE_NAME"))
        self.backendListSize = Configuration().get("HAPROXY_BACKEND_SERVERS_LIST_SIZE")

    def checkTableReady(self):
        try:
            self.table.table_status
        except ClientError:
            self.logger.error("Table %s not found." % self.table)
            sys.exit(2)

    def updateServer(self, server):
        self.table.update_item(
            Key={
                "BackendServerID": server.backendServerID,
            },
            UpdateExpression="SET IPAddress = :IPAddress, ServerName = :ServerName, ASG = :ASG, Weight = :Weight, BackendServerStatus = :BackendServerStatus, LastWeightUpdate = :LastWeightUpdate",
            ExpressionAttributeValues={
                ':IPAddress': server.IPAddress,
                ':ASG': server.ASG,
                ':ServerName': server.serverName,
                ':Weight': server.weight,
                ':BackendServerStatus': server.backendServerStatus,
                ':LastWeightUpdate': server.lastWeightUpdate,
            }
        )

    def createServer(self, server):
        self.table.put_item(
            Item={
                'BackendServerID': server.backendServerID,
                'IPAddress': server.IPAddress,
                'ASG': server.ASG,
                'ServerName': server.serverName,
                'Weight': server.weight,
                'BackendServerStatus': server.backendServerStatus,
                'LastWeightUpdate': server.lastWeightUpdate,
            }
        )

    def listServers(self):
        servers = []

        response = self.table.scan()
        for item in response['Items']:
            servers.append(self.fillServer(item))
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            for item in response['Items']:
                servers.append(self.fillServer(item))

        return servers

    def fillServer(self, item):
        s = ServerModel()
        s.backendServerID = int(item["BackendServerID"])
        # if ASG column does not exist (problem occured when migrating from v2 to v3)
        if "ASG" in item:
            s.ASG = item["ASG"]
        s.IPAddress = item["IPAddress"]
        s.serverName = item["ServerName"]
        s.weight = int(item["Weight"])
        s.lastWeightUpdate = item["LastWeightUpdate"]
        s.backendServerStatus = item["BackendServerStatus"]
        return s
