# haproxy-service-discovery-orchestrator
Orchestrated Service Discovery for HAProxy, using the Runtime API.

No server creation/deletion, only modifications on-the-fly: no file management or reloading.

HSDO has a Server/Client architecture:

1. The Server is a single instance that updates Ready servers list from AWS API.
2. The Server sorts and saves this list inside a DynamoDB table.
3. The client runs alongside HAProxy and updates the list every X seconds from DynamoDB.
4. The client compares HAProxy's running configuration (using: `show stat`) to the desired state stored in DynamoDB and applies changes when needed.

![HSDO Simple](doc/hsdo-simple.png)

Features list:

* Works with AWS AutoScaling Groups and DynamoDB. Other providers may be supported (Consul has been proof tested but is not prod ready), but must be maintained by the community as we only use AWS right now,
* No file management or reloads: only API calls,
* DynamoDB query frequency is configurable,
* Gradual ramping up of new servers, using HAProxy weight: frequency and weight steps are configurable,
* The Server can track multiple AWS AutoScalingGroups,
* The Client can focus to specific ASGs (by using several single-AZ ASGs, it is possible to have a single-AZ topology and avoid prohibitive inter-AZ costs),
* Fallback backend: the Client can configure a second HAProxy backend with focus on different ASGs as the first backend,

## Why HSDO

AWS load balancers don't allow algorithms different from round robin.

HSDO allows to use HAProxy in front of one or multiple AutoScalingGroups on AWS.

HSDO implements ordered backend servers lists to use functionalities like consistent hashing, which makes it possible to use all the power of HAProxy, but on AWS.

By design, HSDO is able to run several HAProxy instances, to load balance from ten to hundreds of backend servers and separate traffic depending of AvailabilityZone.
It is reliable and fault tolerant, as each HAProxy server updates its configuration asynchronously from a DynamoDB table.

We wanted a very simple and efficient implementation for HSDO, which we didn't find in Consul.

## Prerequisities

This project is using pipenv. If you don't have it, please see [here](https://github.com/pypa/pipenv#installation).

You need to have `AWS_PROFILE`, `AWS_DEFAULT_REGION` setted and to be authenticated to access your DynamoDB table.

## Usage

In project directory:

```sh
pipenv install
pipenv shell
python3 src/main.py --[client|server] (--[debug]) (--[help])
```

## Configuration

Parameters can be defined through a config file or environment variables.
Environment variables will overwrite `conf/env.yaml`.

### Server Only

Configuration that is specific to HSDO Server.

`SERVER_ASG_NAMES`: List of ASG names where to find target servers (EC2 instances for which HAProxy will load balance traffic). May be a list, separated with comma. If `aws` mode enabled. Default to ` `.

`SERVER_CONSUL_API_URL`: Consul address where to find your target servers. If `consul` mode enabled. Default to ` `.

`SERVER_CONSUL_SERVICE_NAME`: Consul service name where to find your target servers. May be a list, separated with comma. If `consul` mode enabled. Default to ` `.

`SERVER_HAPROXY_BACKEND_SERVER_MIN_WEIGHT`: Minimum weight of a newly added backend server. Default to `1`.

`SERVER_HAPROXY_BACKEND_SERVER_MAX_WEIGHT`: Maximum weight of a backend server. Default to `10`.

`SERVER_HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT`: Defines the level of increase in the weight of the newly added servers. Every 'SERVER_HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL', the weight of a new server will be increased by this value. Default to `1`.

`SERVER_HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL`: In seconds, time between each weight increasing. For example, if we want a new server to have its target weight 5mns after it has been added to the backend, going from weight 1 to 10, we would use interval 30: 30s interval, 10 times between 1 and 10: 300secs. Default to `30`.

`SERVER_MODE`: Can be `aws` or `consul`. Default to ` `. `consul` is higly experimental, it probably doesn't work. Only `aws` mode is prod ready.

### Client Only

Configuration that is specific to each HSDO Client, next to HAProxy.

`CLIENT_HAPROXY_SOCKET_PATH`: HAProxy socket to use [Runtime API](https://cbonte.github.io/haproxy-dconv/2.2/management.html#9.3). Default to `/var/run/haproxy/admin.sock`.

`CLIENT_HAPROXY_BACKEND_LIST`: HAProxy backend list. Default to ` `.

`CLIENT_HAPROXY_BACKEND_SERVER_PORT`: Port of target servers. Default to `80`.

HAProxy default backend configuration can be seen in `haproxy.cfg`:
```
backend {{ CLIENT_HAPROXY_BACKEND_NAME }}
server-template  {{ CLIENT_HAPROXY_BACKEND_BASE_NAME }} 1-{{ HAPROXY_BACKEND_SERVERS_LIST_SIZE }} 127.0.0.2:{{ CLIENT_HAPROXY_BACKEND_SERVER_PORT }} check disabled
```

For example, with :
```
backend http-back
server-template mywebapp 1-10 127.0.0.2:80 check disabled
```
You will have this kind of statistic page : 

![](doc/backend-servers-list.png)

### Both

`INTERVAL`: Interval between each loop for client/server. Default to `1`.

`HAPROXY_BACKEND_SERVERS_LIST_SIZE`: As max range describe [here](https://cbonte.github.io/haproxy-dconv/2.0/configuration.html#4-server-template). Default to `10`.

`DEBUG`: To enable debug log. Default to `false`.

`DYNAMODB_TABLE_NAME`: Name of Dynamodb table. Default to ` `.

`AWS_DEFAULT_REGION`: default region needed for Dynamodb access. Default to ` `.

`EXPORTER_PORT`: port for Prometheus exporter. Default to `6789`

## Dedicated ASG Configuration (AWS Only)

HSDO Client can be configured to follow specific ASGs that are present in `SERVER_ASG_NAMES`.

For example, if `SERVER_ASG_NAMES` contains `ASG1,ASG2,ASG3`, `CLIENT_ASG_NAMES` may follow `ASG2`. 

This is usefull if you want to split traffic per AZ.

![Dedicated ASG Implementation Example](doc/HSDO_AZ_Limiter.png)

This is possible if you enable `CLIENT_DEDICATED_ASG`.

If the target's ASG name is in `CLIENT_ASG_NAMES`, then the target is put in default HAProxy backend.

If the target's ASG name is not in `CLIENT_ASG_NAMES`, then the target is put in fallback HAProxy backend.

If needed, ASG name in `CLIENT_ASG_NAMES` can alse be added in fallback HAProxy backend with `CLIENT_ALL_SERVERS_IN_FALLBACK_BACKEND` enabled.

Fallback from default HAProxy backend to fallback HAProxy backend are not handled by HSDO Client.

### Client only

`CLIENT_DEDICATED_ASG`: HSDO Client will use `CLIENT_ASG_NAMES` to configure default HAProxy backend, and put the other ones in fallbackend HAProxy backend. Default to `false`.

`CLIENT_ASG_NAMES`: List of ASG that HSDO Client will use in default HAProxy backend. May be a list, separated with comma. Needed with `CLIENT_DEDICATED_ASG`. Default to ` `.

`CLIENT_HAPROXY_FALLBACK_BACKEND_NAME`: HAProxy fallback backend name. Needed with `CLIENT_DEDICATED_ASG`. Default to ` `.

`CLIENT_HAPROXY_FALLBACK_BACKEND_BASE_NAME`: HAProxy fallback backend base name for server template. Needed with `CLIENT_DEDICATED_ASG`. Default to ` `.

`CLIENT_ALL_SERVERS_IN_FALLBACK_BACKEND`: to put also all default HAProxy backend servers in the fallback HAProxy backend. Default to `false`.

## DynamoDB

What dynamodb table should look like (terraform code):

```
resource "aws_dynamodb_table" "haproxy_service_discovery_orchestrator_table" {
  name           = "haproxy-service-discovery-orchestrator"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "BackendServerID"

  attribute {
    name = "BackendServerID"
    type = "N"
  }

  tags = {
    name         = "haproxy-service-discovery-orchestrator"
  }
}
```

## Tests

From root directory

```sh
pipenv shell
python3 -m unittest
```
