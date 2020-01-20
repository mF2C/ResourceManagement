# Policies Module

> Policies - Resource Management
> CRAAX - UPC, 2019
> The Policies module is a component of the European Project mF2C.

---

- [Description](#Description)
- [Environment variables](#Environment variables)
- [Leader Election](#Leader Election)
- [API Endpoints](#API Endpoints)
- [LICENSE](#LICENSE)

----

### Description

The policies module is responsible for:

- Define the resilience and clustering policies.
- Enforce the protection of the area (Leader and Backup).
- Definition and Execution of the Leader Election Algorithm.
- Orchestration of the Resource Manager Block.

## Usage

The Policies module can be run ussing the dockerized version or directly from source.

#### Docker

Last build version from docker hub: `docker run --rm mf2c/policies:<version>`

Replace *<version>* with a valid uploaded version [here](https://cloud.docker.com/u/mf2c/repository/docker/mf2c/policies/tags).

#### Source

`Python 3.7.x` is required to execute this code.

1. Clone the repository with Git. It's hightly recomended to create a Python virtual environment.
2. Install all the library dependencies: `pip3 install -r requirements.txt`
2. Execute the following command: `python3 main.py`


### Environment variables

To run policies module along other mF2C components, is necessary to specify the following environment variables:

```yaml
- "MF2C=True"
```

##### The interface used by discovery is specified in:

```yaml
- "WIFI_DEV_FLAG="
```

**NOTE**: Specific configurations are required in Discovery to attach the interface. This parameter is only used to inform Discovery at the startup.

##### To modify the role of the agent (normal/leader): 

```yaml
- "isLeader=False"
```

##### To deploy in Cloud

```yaml
- "isCloud=True"
```

##### To specify static leader and device IPs:

```yaml
- "leaderIP="
- "deviceIP="
```

**NOTE**: Only used when Discovery cannot detect a nearby Leader. These variables should only be used for testing purposes and internal mF2C procedures may fail if they are modified.

##### To specify the address of the Cloud Agent (Ignored if deployed as Cloud Agent)

```yaml
- "MF2C_CLOUD_AGENT=172.0.0.1"
``` 

##### To specify the amount of retry attempts to register a device

```yaml
- "REGISTRATION_MAX_RETRY=20"
```

#### To specify the amount of retry attempts to check the leader before takeover

```yaml
- "MAX_RETRY_ATTEMPTS=20"
```

*Retry period: 2 seconds*

#### To specify the amount of time (seconds) before a backup is considered down

```yaml
- "MAX_TTL=10"
```

Once the leader is setup and running, the Area Resilience submodule starts looking for an agent to become the backup. The backup checks if the leader is running correctly using the Keepalive Protocol defined in the module. Either the Leader or the Backup are protected, meaning that if the Leader fails, the backup takes its place or if the backup fails, the leader elects a new one when it's possible. The election is performed using the Leader Election Algorithm.

##### Leader Reelection (LR)

When is necessary to replace the actual Leader, the reelection mechanism allow us to select a new agent to be the Leader and demote the current one into a normal agent.
 

### API Endpoints

All the API calls are made via REST. The endpoints and required parameters can be consulted on [http://{policies_address}:46050/](http://localhost:46050/)

**Note:** Replace *policies_address* with the real address of the container or device where the code is running

**IMPORTANT**: The new route to the policies module is now `api/v2/resource-management/policies`

#### Resource Manager Status

Get resource manager module start status and errors on triggers.

- **GET**  /rm/components

```bash
curl -X GET "http://localhost/rm/components" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Success
    - **Response Payload:** 
    ```json
    {
  "started": true,                              // The agent is started
  "running": true,                              // The agent is currently running
  "modules": [                                  // List of modules that are triggered on starting
    "string"
  ],
  "discovery": true,                            // Discovery module is started
  "identification": true,                       // Identification module is started
  "cau_client": true,                           // CAUClient module is started
  "categorization": true,                       // Categorization module is started
  "policies": true,                             // Area Resilience module is started
  "discovery_description": "string",            // Discovery module description / parameters received
  "identification_description": "string",       // Identification module description / parameters received
  "categorization_description": "string",       // Categorization module description / parameters received
  "policies_description": "string",             // Policies module description / parameters received
  "cau_client_description": "string",           // CAUClient module description / parameters received
  "leader_discovery_description": "string"      // Discovery Leader startup description
    }
    ```

#### Healthcheck

Health of the Policies module. Policies only works properly under GREEN and YELLOW status codes.

> **GREEN:** All components successfully triggered, IPs correctly setup, Backup elected (if Leader) and deviceID generated.
>
> **YELLOW:** Discovery failed or leader not found (only in agent side) but IPs correctly setup, Backup not elected (if Leader).
>
> **RED:** Component(s) trigger failed, IPs not set, deviceID not generated, or Agent resource not created
>
> **ORANGE:** YELLOW or RED status, but still starting. 

If docker healthcheck if set: `docker inspect mf2c_policies_1 | jq -e ".[0].State.Health"` 

- **GET** /api/v2/resource-management/policies/healthcheck

```bash
curl -X GET "http://localhost/api/v2/resource-management/policies/healthcheck" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Health OK GREEN or YELLOW
    - **400** - Health NOK ORANGE or RED 
    - **Response Payload:**
    ```json
        {
        "health": true,                        // 'True if the component is considered to work properly (GREEN and YELLOW status).'),
        "startup": true,                       // "True if the module has finished the agent startup flow."),
        "startup_time": 40.0,                  // "Time considered as startup (ORANGE status when failure)"),
        "status": "GREEN",                     // "Status code of the component. GREEN: all OK, YELLOW: failure detected but working, ORANGE: Failed but starting, RED: critical failure."),
        "API": true,                           // "True if API working"),
        "discovery": true,                     // "True if Discovery not failed on trigger"),
        "identification": true,                // "True if Identification not failed on trigger"),
        "cau-client":  true,                   // "True if CAU-client not failed on trigger"),
        "res-cat": true,                       // "True if Res. Categorization not failed on trigger"),
        "area-resilience": true,               // "True if sub-module Area Resilience started"),
        "vpn-client": true,                    // "True if VPN is stablished and got IP"),
        "deviceIP": true,                      // "True if deviceIP not empty"),
        "leaderIP": true,                      // "True if leaderIP not empty or isCloud = True"),
        "cloudIP": true,                       // "True if cloudIP not empty"),
        "deviceID": true,                      // "True if deviceID not empty"),
        "backupElected": true,                 // "True if (activeBackups > 0 and isLeader=True) or isCloud=True"),
        "leaderfound": true,                   // "True if leader found by discovery or (isCloud = True || isLeader = True)"),
        "JOIN-MYIP": true,                     // "True if joined and IP from discovery obtained or (isCloud = True || isLeader = True)"),
        "wifi-iface": true,                    // "True if wifi iface not empty or (isCloud = True)")
        "agent-resource": true                 // "True if agent resource created"
        }
    ```

#### Keepalive

Keepalive entrypoint for Leader. Backups send message to this address and check if the Leader is alive. Only registered backups are allowed to send keepalives, others will be rejected.

- **POST** /api/v2/resource-management/policies/keepalive
- **PAYLOAD**  `{"deviceID": "agent/1234"}`

```bash
curl -X POST "http://localhost/api/v2/resource-management/policies/keepalive" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"deviceID\": \"agent/1234\"}"
```

- **RESPONSES**
    - **200** - Success
    - **403** - Agent not authorized
    - **405** - Device is not a Leader
    - **Response Payload:** `{
  "deviceID": "leader/1234",
  "backupPriority": 0
}` 

#### Leader Info

Check if the agent is a Leader or Backup.

- **GET** /api/v2/resource-management/policies/leaderinfo

```bash
curl -X GET "http://localhost/api/v2/resource-management/policies/leaderinfo" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Success
    - **Response Payload:** `{
  "imLeader": false,
  "imBackup": false,
  "imCloud": false
}`

#### Reelection

Send a message to trigger the reelection process. The specified agent will be the reelected leader if it accepts.

- **POST** /api/v2/resource-management/policies/reelection
- **PAYLOAD** `{
  "deviceID": "agent/1234"
}`

```bash
curl -X POST "http://localhost/api/v2/resource-management/policies/reelection" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"deviceID\": \"agent/1234\"}"
```

- **RESPONSES**
    - **200** - Reelection Successful
    - **401** - The Agent is not authorized to trigger the reelection
    - **403** - Reelection failed
    - **404** - Device not found or IP not available
    - **Response Payload:** `{
  "imLeader": false,
  "imBackup": false
}`

#### Start Area Resilience

Starts the Area Resilience submodule (in charge of the Leader Protection)

- **GET** /api/v2/resource-management/policies/startAreaResilience

```bash
curl -X GET "http://localhost/api/v2/resource-management/policies/startAreaResilience" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Started
    - **403** - Already Started
    
#### Start Agent

Start the agent (start as Leader or Normal agent + Discovery, CAU Client and Categorization Triggers)

- **GET** /api/v2/resource-management/policies/policiesstartAgent

```bash
curl -X GET "http://localhost/api/v2/resource-management/policiesstartAgent" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Started
    - **403** - Already Started

    
#### Role Change

Change the agent from current role to specified one (leader, backup or agent).

- **GET** /api/v2/resource-management/policies/roleChange/{role}

```bash
curl -X GET "http://localhost/api/v2/resource-management/policies/roleChange/agent" -H "accept: application/json"
curl -X GET "http://localhost/api/v2/resource-management/policies/roleChange/backup" -H "accept: application/json"
curl -X GET "http://localhost/api/v2/resource-management/policies/roleChange/leader" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Successful
    - **403** - Not Successful
    - **404** - Role not found

### LICENSE

The Policies module application is licensed under [Apache License, Version 2.0](LICENSE.txt)
