# haproxy-service-discovery-orchestrator
Orchestrate Service Discovery for HAProxy

- ASG or Consul is listing available servers
- HAProxy SDO Server gets servers from ASG, sort them, and save them in DynamoDB
- HAproxy SDO Clients get sorted servers from DynamoDB and send configuration to HAProxy Runtime API
- HAProxy server have all same configuration

![HSDO Simple](doc/hsdo-simple.png)

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

`SERVER_ASG_NAMES`: List of ASG names where to find target servers (EC2 instances for which HAProxy will load balance traffic). May be a list, separated with comma. If `aws` mode enabled. Default to ` `.

`CONSUL_API_URL`: Consul address where to find your target servers. If `consul` mode enabled. Default to ` `.

`CONSUL_SERVICE_NAME`: Consul service name where to find target servers. May be a list, separated with comma. If `consul` mode enabled. Default to ` `.

`HAPROXY_BACKEND_SERVER_MIN_WEIGHT`: Default to `1`.

`HAPROXY_BACKEND_SERVER_MAX_WEIGHT`: Default to `10`.

`HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT`: Default to `1`.

`HAPROXY_BACKEND_SERVER_INCREASE_WEIGHT_INTERVAL`: In seconds, time between each weight increasing. For example, if we want to increase weight from 1 to 10 every 30 seconds, we need to wait for 5min. Default to `30`.

`SERVER_MODE`: Can be `aws` or `consul`. Default to ` `.

### Client Only

`CLIENT_ASG_NAMES`: List of names of ASG where servers are. May be a list, separated with comma. If `aws` mode enabled. Default to ` `.

`HAPROXY_SOCKET_PATH`: HAProxy socket to use [Runtime API](https://cbonte.github.io/haproxy-dconv/2.0/management.html#9.3). Default to `/var/run/haproxy/admin.sock`.

`HAPROXY_BACKEND_NAME`: HAProxy backend name. Default to ` `.

`HAPROXY_BACKEND_BASE_NAME`: HAProxy backend base name for server template. Default to ` `.

`HAPROXY_FALLBACK_BACKEND_NAME`: HAProxy fallback backend name. Needed by `AZ_LIMITER` Default to ` `.

`HAPROXY_FALLBACK_BACKEND_BASE_NAME`: HAProxy fallback backend base name for server template. Needed by `AZ_LIMITER`. Default to ` `.

`HAPROXY_BACKEND_SERVER_PORT`: Port of target servers. Default to `80`.

`AZ_LIMITER`: Need a second HAProxy backend. If server ASG in not present in `CLIENT_ASG_NAMES`, it will be set in the fallback backend define in `HAPROXY_FALLBACK_BACKEND_NAME`. Default to `false`.

`ALL_SERVERS_IN_FALLBACK_BACKEND`: to put also all primary backend servers in the fallback backend. Default to `false`.

HAProxy backend configuration can be seen in `haproxy.cfg`:
```
backend {{ HAPROXY_BACKEND_NAME }}
server-template  {{ HAPROXY_BACKEND_BASE_NAME }} 1-{{ HAPROXY_BACKEND_SERVERS_LIST_SIZE }} 127.0.0.2:{{ HAPROXY_BACKEND_SERVER_PORT }} check disabled
```

For example, with :
```
backend http-back
server-template mywebapp 1-10 127.0.0.2:80 check disabled
```
You will have this kind of statistique page : 

![](doc/backend-servers-list.png)

### Both

`INTERVAL`: Interval between each loop for client/server. Default to `1`.

`HAPROXY_BACKEND_SERVERS_LIST_SIZE`: As max range describe [here](https://cbonte.github.io/haproxy-dconv/2.0/configuration.html#4-server-template). Default to `10`.

`DEBUG`: (true|false) To enable debug log. Default to `false`.

`DYNAMODB_TABLE_NAME`: Name of dynamodb table. Default to ` `.

`AWS_DEFAULT_REGION`: default region needed for dynamodb access. Default to ` `.

`EXPORTER_PORT`: port for prometheus exporter. Default to `6789`

## DynamoDB

What dynamodb table should look like :

```
resource "aws_dynamodb_table" "service_discovery_orchestrator_table" {
  name           = "${var.project}-service-discovery-orchestrator"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "BackendServerID"

  attribute {
    name = "BackendServerID"
    type = "N"
  }

  tags = {
    Name         = "${var.project}-service-discovery-orchestrator"
    name         = "${var.project}-service-discovery-orchestrator"
    project      = var.project
    team         = var.team
    product_line = var.product_line
    tenant       = var.tenant
    customer     = var.customer
  }
}
```

## AZ Limiter
To reduce inter-AZ costs, you can configure HSDO Client to register in each HAProxy only backend servers in same AZ.

When AZ Limiter is enabled, HSDO while compare the ASG (Autoscaling Group) name of each server listed in the database, with the ASG list defined in `CLIENT_ASG_NAMES`.
If the server's ASG name is in `CLIENT_ASG_NAMES`, then the server is put in backend.

If needed, other AZ backend servers can be add as "fallback" backend servers to increase resilience.
If the `ALL_SERVERS_IN_FALLBACK_BACKEND` option is enabled, the servers will be put in the backend AND in the fallback backend.


## Tests

From root directory

```sh
pipenv shell
python3 -m unittest
```
