from device_static import static_info
from device_dynamic import dynamic_info
from os import getenv
import subprocess
import threading
import time as t
import json,requests
import urllib3
from flask import Flask, jsonify, request
from requests.exceptions import ConnectionError
import requests
#from requests.adapters import HTTPAdapter
#from urllib3.util import Retry
from datetime import datetime
import docker
docker_client2 = docker.from_env()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
example = None
isStarted = False
isStarted1 = False
switch_flag = False

class Main():

    print("The Resource-Categorization module is about to be start.....")

    def __init__(self, interval=10):
        #self.db_lock = threading.Lock()
        self.isLeader = False
        self.sensorType = None
        self.sensorModel = None
        self.sensorConnection = None
        self.interval = interval
        self.thread_module = threading.Thread(name='thread-module', target=self.th_module, daemon=True)
        self.Key = None
        self._running = False
        self.deviceID_cimiresource = None

        self.deviceID_cimiresource = None
        self.deviceDynamicID_cimiresource = None
        self.fogresourceid = None
        self.agentresourceid = "agent"
        self.status = "connected"
        self.cimi_endpoint = getenv("LEADER_ENDPOINT","http://cimi:8201")

##Start the program##

    def start(self,userid, leaderid, isleader):
        self.userID = userid
        self.detectedLeaderID = leaderid
        self.isLeader = isleader
        self._running = True
        self.thread_module.start()

##Switch to normal agent to leader agent###

    def switch(self, userid, switch_flag, isleader):
        global sf
        self.userID = userid
        self.isLeader = isleader
        self.switchFlag = switch_flag
        sf = self.switchFlag
        self._running = True
        self.thread_module = threading.Thread(name='thread-module-switch', target=self.th_module, daemon=True)
        self.thread_module.start()


##Sensor information passing##

    # def sensor(self, sensortype, sensormodel, sensorconnection):
    #     self.sensorType = sensortype
    #     self.sensorModel = sensormodel
    #     self.sensorConnection = sensorconnection

##Threading Module is starting##

    def th_module(self):
        if not self._running:
            return

            ## Threads for the Normal agent side
        if not self.isLeader:
            thread1 = threading.Thread(target=self.static, daemon=True, name='sta')
            thread1.start()
            self.thread_dyn = threading.Thread(target=self.dynamic, daemon=True, name='dyn')
            self.thread_dyn.start()
            self.thread_agentres = threading.Thread(target=self.agentresource, daemon=True, name='ageres')
            self.thread_agentres.start()

            ## Threads for the Leader-side
        else:
            thread1 = threading.Thread(target=self.staticLeader, daemon=True, name='staLe')
            thread1.start()

            self.thread_dyn = threading.Thread(target=self.dynamicLeader, daemon=True, name='dynLe')
            self.thread_dyn.start()

            self.thread_agentres = threading.Thread(target=self.agentresourceLeader, daemon=True, name='ageresLe')
            self.thread_agentres.start()

            self.thread_fogareainfo = threading.Thread(target=self.fogarea, daemon=True, name='leader')
            self.thread_fogareainfo.start()


## Child Static information storing to the CIMI+Dataclay ##

    def static(self):
        global jsonString_merged_static
        deviceID = self.userID
        dID= str(deviceID)
        devID = {"deviceID":dID}
        isleader1 = {"isLeader":False}
        stat = static_info()
        staticinfo = json.loads(stat)
        devStatic= {**devID, **staticinfo, **isleader1}
        jsonString_merged_static = devStatic
        print("Device information for micro agent: ", jsonString_merged_static)

        try:
            r = requests.post("{}/api/device".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"}, json=jsonString_merged_static, verify=False)
            print("Posting device resource info for micro-agent: ", r, r.request, r.reason, r.json())

            #capturing the corresponding cimi resource-id
            self.deviceID_cimiresource = r.json()['resource-id']
            r1 = requests.get("{}/api/device".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
            print("Response to see posted device resource info for micro-agent: ", r1, r1.request, r1.reason, r1.json())

        except Exception as e:
            print (e)
            r = "No response"
            print(r)
        while (not switch_flag):
            t.sleep(0.1)


## Child Dynamic information storing to the CIMI+Dataclay ##

    def dynamic(self):
        global jsonString_merged_dynamic
        while self.deviceID_cimiresource is None:
            t.sleep(0.1)
        devID = {"device": {'href': str(self.deviceID_cimiresource)}}
        target_deviceSensor = getenv('targetDeviceSensor')
        if target_deviceSensor == 'B':
            sensors = {
                "sensors": [
                    {
                        "sensorType": "[\"acceleration\", \"satelliteCount\", \"voltage\", \"battery\", \"inclination\", \"proximity\", \"bearing\", \"velocity\", \"current\", \"waterLevel\", \"temperature\", \"humidity\", \"pressure\", \"latitude\", \"longitude\"]",
                        "sensorConnection": "{\"bluetoothMac\": \"12:23:34:45:56:67\"}",
                        "sensorModel": "smartboat-bm"
                    }
                ]
            }

        elif target_deviceSensor == 'I':
            sensors = {
                "sensors": [
                    {
                        "sensorType": "[\"acceleration\", \"satelliteCount\", \"voltage\", \"battery\", \"inclination\", \"proximity\", \"bearing\", \"velocity\", \"current\", \"waterLevel\", \"temperature\", \"humidity\", \"pressure\", \"latitude\", \"longitude\"]",
                        "sensorConnection": "{\"bluetoothMac\": \"12:23:34:45:56:67\"}",
                        "sensorModel": "Inclinometer"
                    }
                ]
            }
        else:
            sensortype = None
            sensormodel = None
            sensorconnection = None
            sensors = {"sensors": [{'sensorType': str(sensortype), 'sensorModel': str(sensormodel),
                                    'sensorConnection': str(sensorconnection)}]}

        statusinfo = {"status": str(self.status)}

        while self._running:
            t.sleep(0.1)
            dyna = dynamic_info()
            print("dyna: ", dyna)
            dynamicinfo = json.loads(dyna)
            wifi_ip = dynamicinfo['wifiAddress']
            if wifi_ip == "Null":
                print("IP Address is not retrieve yet!!!")
            else:
                devDynamic = {**devID, **dynamicinfo, **sensors, **statusinfo}
                jsonString_merged_dynamic = devDynamic
                print("Device-Dynamic information for Micro Agent: ", jsonString_merged_dynamic)
                try:
                    if self.deviceDynamicID_cimiresource is None:
                        r2 = requests.post("{}/api/device-dynamic".format(self.cimi_endpoint),
                                           headers={"slipstream-authn-info": "internal ADMIN"},
                                           json=jsonString_merged_dynamic, verify=False)
                        print("Posting device-dynamic resource info for micro-agent: ", r2, r2.request, r2.reason,
                              r2.json())
                        self.deviceDynamicID_cimiresource = r2.json()['resource-id']
                        r3 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),
                                          headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                        print("Response to see posted device-dynamic resource info for micro-agent: ", r3, r3.request,
                              r3.reason, r3.json())
                    else:
                        cimiResourceID = {"resource-id": self.deviceDynamicID_cimiresource}
                        devDynamic = {**devID, **dynamicinfo, **sensors, **cimiResourceID}
                        jsonString_merged_dynamic = devDynamic
                        r4 = requests.put("{}/api/device-dynamic".format(self.cimi_endpoint),
                                          headers={"slipstream-authn-info": "internal ADMIN"},
                                          json=jsonString_merged_dynamic, verify=False)
                        print("Updating device-dynamic resource info for micro-agent: ", r4, r4.request, r4.reason,
                              r4.json())
                        r5 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),
                                          headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                        print("Response to see updated device-dynamic resource info for micro-agent: ", r5, r5.request,
                              r5.reason, r5.json())
                except ConnectionError as e:
                    print(e)
                    r = "No response"
                    print(r)
                t.sleep(10)
                if switch_flag:
                    break

## Child-side agent-resource Information sending to the CIMI+Dataclay for storing ##

    def agentresource(self):
        global agresid, end_url_point, wifi_address_NIC, ethe_address_NIC, devIP, devips
        while self.deviceID_cimiresource is None:
            t.sleep(0.1)
        deviceID = self.userID
        dID = ""
        MyleaderID = (str(self.deviceID_cimiresource))


        while self._running:
            t.sleep(0.1)
            leddevip = ""
            childip = []
            backupip = ''
            authenticated = True
            connect = True
            isleader = False
            try:
                client = docker.from_env()
                running_containers = client.containers.list(filters={"status": "running"})
                running_discovery_containers = []
                for container in running_containers:
                    container_im = container.attrs['Config']['Image']
                    try:
                        if "discovery" in container_im:
                            running_discovery_containers.append(container)
                    except:
                        running_discovery_containers=[]

                if len(running_discovery_containers) == 1:
                    disc_cont_id = running_discovery_containers[0]
                    cmd = 'python get_ip_addr.py'
                    try:
                        exit_code, output = disc_cont_id.exec_run(cmd, stderr=True, stdout=True, demux=True)
                        if exit_code == 0:
                            ip = output[0]  # output[0] is the stdout
                            devip = str(ip)
                        else:
                            devip = "None"
                    except:
                        devip = "None"
                    agentResource1_info = {"device_id": MyleaderID, "device_ip": devip, "leader_id": dID, "leader_ip": leddevip,"authenticated": authenticated, "connected": connect, "isLeader": isleader,"backup_ip": backupip, "childrenIPs": childip}
                    agentResource_info = {"device_id": deviceID, "device_ip": devip}
                    agentRes1_info = json.dumps(agentResource1_info)
                    agentRes_info = json.dumps(agentResource_info)

                else:
                    try:
                        response_vpn = requests.get("http://localhost:1999/api/get_vpn_ip", verify=False)
                        res_vpn = response_vpn.json()
                        devvpnIP = res_vpn['ip']
                        devip = str(devvpnIP)
                    except:
                        devip = "None"

                    agentResource1_info = {"device_id": MyleaderID, "device_ip": devip, "leader_id": dID, "leader_ip": leddevip,"authenticated": authenticated, "connected": connect, "isLeader": isleader,"backup_ip": backupip, "childrenIPs": childip}
                    agentResource_info = {"device_id": deviceID, "device_ip": devip}
                    agentRes1_info = json.dumps(agentResource1_info)
                    agentRes_info = json.dumps(agentResource_info)


                    if agentResource_info['device_ip'] is "Null" and agentResource1_info['device_ip'] is "Null":
                        print("Device IP is not retrieve yet!!!")
                    elif agentResource_info['device_ip'] is "" and agentResource1_info ['device_ip'] is "":
                        print("Device IP is not retrieve yet!!!")
                    else:
                        try:
                            r91 = requests.get("{}/api/agent".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"},verify=False)
                            print("Getting the Agent resource info for normal-agent: ", r91, r91.request, r91.reason, r91.json())
                            agentresource = r91.json()
                            try:
                                self.agentresourceid = next(item['id'] for item in agentresource['agents'] if 'id' in item)
                                agresid = str(self.agentresourceid)
                                url_point = "{}/api/".format(self.cimi_endpoint)
                                end_url_point = str(url_point + agresid)
                            except:
                                pass

                            if self.agentresourceid is "agent":
                                print("Agent resource is not yet created!!! Wait for few times")
                            else:
                                r6 = requests.put(end_url_point,headers={"slipstream-authn-info": "internal ADMIN"},json=agentResource_info, verify=False)
                                print("Updating agent resource info: ", r6, r6.request, r6.reason, r6.json())
                                r9 = requests.get(end_url_point, headers={"slipstream-authn-info": "internal ADMIN"},verify=False)
                                print("Response to see updated agent resource info: ", r9, r9.request, r9.reason, r9.json())

                        except ConnectionError as e:
                            print("Agent resource is not yet created!!! Wait for few times")
            except:
                print("Device IP is not retrieve yet!!!")

            t.sleep(10)
            if switch_flag:
               break


## Leader Static Information sending to the CIMI+Dataclay for storing ##

    def staticLeader(self):
        global jsonString_merged_static
        deviceID = self.userID
        dID = str(deviceID)
        devID = {"deviceID": dID}
        isleader1 = {"isLeader": True}
        stat = static_info()
        staticinfo = json.loads(stat)
        devStatic= {**devID, **staticinfo, **isleader1}
        jsonString_merged_static = devStatic
        print("Device information for leader-agent: ", jsonString_merged_static)

        try:
            r = requests.post("{}/api/device".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"},
                              json=jsonString_merged_static, verify=False)
            print("Posting device resource info for leader-agent: ", r, r.request, r.reason, r.json())

            # capturing the corresponding cimi resource-id
            self.deviceID_cimiresource = r.json()['resource-id']
            r1 = requests.get("{}/api/device".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"},
                              verify=False)
            print("Response to see posted device resource info for leader-agent: ", r1, r1.request, r1.reason, r1.json())

        except Exception as e:
            print(e)
            r = "No response"
            print(r)


## Leader Dynamic Information sending to the CIMI+Dataclay for storing ##

    def dynamicLeader(self):
        global jsonString_merged_dynamic
        while self.deviceID_cimiresource is None:
            t.sleep(0.1)
        ## TODO:- need to add some lines of code and also change some code in order to add the CIMI provided reosurce-id and leaderID ##
        devID = {"device": {'href': str(self.deviceID_cimiresource)}}
        target_deviceSensor = getenv('targetDeviceSensor')
        if target_deviceSensor == 'B':
            sensors = {
                "sensors": [
                    {
                        "sensorType": "[\"acceleration\", \"satelliteCount\", \"voltage\", \"battery\", \"inclination\", \"proximity\", \"bearing\", \"velocity\", \"current\", \"waterLevel\", \"temperature\", \"humidity\", \"pressure\", \"latitude\", \"longitude\"]",
                        "sensorConnection": "{\"bluetoothMac\": \"12:23:34:45:56:67\"}",
                        "sensorModel": "smartboat-bm"
                    }
                ]
            }

        elif target_deviceSensor == 'I':
            sensors = {
                "sensors": [
                    {
                        "sensorType": "[\"acceleration\", \"satelliteCount\", \"voltage\", \"battery\", \"inclination\", \"proximity\", \"bearing\", \"velocity\", \"current\", \"waterLevel\", \"temperature\", \"humidity\", \"pressure\", \"latitude\", \"longitude\"]",
                        "sensorConnection": "{\"bluetoothMac\": \"12:23:34:45:56:67\"}",
                        "sensorModel": "Inclinometer"
                    }
                ]
            }
        else:
            sensortype = None
            sensormodel = None
            sensorconnection = None
            sensors = {"sensors": [{'sensorType': str(sensortype), 'sensorModel': str(sensormodel),
                                    'sensorConnection': str(sensorconnection)}]}

        statusinfo = {"status": str(self.status)}



        while self._running:
            t.sleep(0.1)
            dyna = dynamic_info()
            dynamicinfo = json.loads(dyna)
            wifi_ip = dynamicinfo['wifiAddress']
            if wifi_ip == "Null":
                print("IP Address is not retrieve yet!!!")
            else:
                devDynamic = {**devID, **dynamicinfo, **sensors, **statusinfo}
                jsonString_merged_dynamic = devDynamic
                print("Device-Dynamic information for Leader-agent: ", jsonString_merged_dynamic)
                try:
                    if self.deviceDynamicID_cimiresource is None:
                        r2 = requests.post("{}/api/device-dynamic".format(self.cimi_endpoint),
                                           headers={"slipstream-authn-info": "internal ADMIN"},
                                           json=jsonString_merged_dynamic, verify=False)
                        print("Posting device-dynamic resource info for leader-agent: ", r2, r2.request, r2.reason,
                              r2.json())
                        self.deviceDynamicID_cimiresource = r2.json()['resource-id']
                        r3 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),
                                          headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                        print("Response to see posted device-dynamic resource info for leader-agent: ", r3, r3.request,
                              r3.reason, r3.json())
                    else:
                        cimiResourceID = {"resource-id": self.deviceDynamicID_cimiresource}
                        devDynamic = {**devID, **dynamicinfo, **sensors, **cimiResourceID}
                        jsonString_merged_dynamic = devDynamic
                        r4 = requests.put("{}/api/device-dynamic".format(self.cimi_endpoint),
                                          headers={"slipstream-authn-info": "internal ADMIN"},
                                          json=jsonString_merged_dynamic, verify=False)
                        print("Updating device-dynamic resource info for leader-agent: ", r4, r4.request, r4.reason,
                              r4.json())
                        r5 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),
                                          headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                        print("Response to see updated device-dynamic resource info for leader-agent: ", r5, r5.request,
                              r5.reason, r5.json())
                except ConnectionError as e:
                    print(e)
                    r = "No response"
                    print(r)
                t.sleep(10)

## Leader-side agent-resource Information sending to the CIMI+Dataclay for storing ##

    def agentresourceLeader(self):
        global agresid, end_url_point, wifi_address_NIC, ethe_address_NIC
        childip = []
        while self.deviceID_cimiresource is None:
            t.sleep(0.1)
        deviceID = self.userID
        dID = str(deviceID)
        MyleaderID = (str(self.deviceID_cimiresource))
        while self._running:
            t.sleep(0.1)
            try:
                client = docker.from_env()
                running_containers = client.containers.list(filters={"status": "running"})
                running_discovery_containers = []
                for container in running_containers:
                    container_im = container.attrs['Config']['Image']
                    try:
                        if "discovery" in container_im:
                            running_discovery_containers.append(container)
                    except:
                        running_discovery_containers = []

                if len(running_discovery_containers) == 1:
                    disc_cont_id = running_discovery_containers[0]
                    cmd = 'python get_ip_addr.py'
                    try:
                        exit_code, output = disc_cont_id.exec_run(cmd, stderr=True, stdout=True, demux=True)
                        if exit_code == 0:
                            ip = output[0]  # output[0] is the stdout
                            devip = str(ip)
                        else:
                            devip = "None"
                    except:
                        devip = "None"

                    r22 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                    dynamics_info = r22.json()
                    rs_info = dynamics_info['deviceDynamics']
                    ips1 = [item['wifiAddress'] for item in rs_info]

                    childip = [y for y in ips1 if y!= None and y!= "192.168.7.1"]

                    backupip = ""
                    authenticated = True
                    connect = True
                    isleader = True


                    agentResource1_info = {"device_id": dID, "device_ip": devip, "leader_id": dID, "leader_ip": devip, "authenticated": authenticated, "connected": connect, "isLeader": isleader, "backup_ip": backupip, "childrenIPs": childip}
                    agentResource_info = {"device_id": dID, "device_ip": devip, "leader_id": MyleaderID, "backup_ip": backupip, "childrenIPs": childip}
                    agentRes_info = json.dumps(agentResource_info)
                    agentRes1_info = json.dumps(agentResource1_info)

                else:
                    try:
                        response_vpn = requests.get("http://localhost:1999/api/get_vpn_ip", verify=False)
                        res_vpn = response_vpn.json()
                        devvpnIP = res_vpn['ip']
                        devip = str(devvpnIP)
                    except:
                        devip = "None"

                    r22 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                    dynamics_info = r22.json()
                    rs_info = dynamics_info['deviceDynamics']
                    ips1 = [item['wifiAddress'] for item in rs_info]

                    childip = [y for y in ips1 if y!= None and y!= "192.168.7.1"]

                    backupip = ""
                    authenticated = True
                    connect = True
                    isleader = True


                    agentResource1_info = {"device_id": dID, "device_ip": devip, "leader_id": dID, "leader_ip": devip, "authenticated": authenticated, "connected": connect, "isLeader": isleader, "backup_ip": backupip, "childrenIPs": childip}
                    agentResource_info = {"device_id": dID, "device_ip": devip, "leader_id": MyleaderID, "backup_ip": backupip, "childrenIPs": childip}
                    agentRes_info = json.dumps(agentResource_info)
                    agentRes1_info = json.dumps(agentResource1_info)


                    if agentResource_info['device_ip'] is "Null" and agentResource1_info['device_ip'] is "Null":
                        print("Device IP is not retrieve yet!!!")
                    elif agentResource_info['device_ip'] is "" and agentResource1_info ['device_ip'] is "":
                        print("Device IP is not retrieve yet!!!")
                    elif agentResource_info['device_ip'] is "None, None" and agentResource1_info ['device_ip'] is "None, None":
                        print("Device IP is not retrieve yet!!!")
                    elif agentResource_info['device_ip'] is "Null, Null" and agentResource1_info ['device_ip'] is "Null, Null":
                        print("Device IP is not retrieve yet!!!")
                    else:
                        try:
                            r91 = requests.get("{}/api/agent".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"},verify=False)
                            print("Getting the Agent resource info for leader-agent: ", r91, r91.request, r91.reason, r91.json())
                            agentresource = r91.json()
                            try:
                                self.agentresourceid = next(item['id'] for item in agentresource['agents'] if 'id' in item)
                                agresid = str(self.agentresourceid)
                                url_point = "{}/api/".format(self.cimi_endpoint)
                                end_url_point = str(url_point + agresid)
                            except:
                                pass

                            if self.agentresourceid is "agent":
                                print("Agent resource is not yet created!!! Wait for few times")
                            else:
                                print("Updating information of agent resource in leader-side (before posting): ", agentRes_info)
                                r6 = requests.put(end_url_point, headers={"slipstream-authn-info": "internal ADMIN"},json=agentResource_info, verify=False)
                                print("Updating agent resource info: ", r6, r6.request, r6.reason, r6.json())
                                r9 = requests.get(end_url_point, headers={"slipstream-authn-info": "internal ADMIN"},verify=False)
                                print("Response to see updated agent resource info: ", r9, r9.request, r9.reason, r9.json())


                        except ConnectionError as e:
                            print("Agent resource is not yet created!!! Wait for few times")
            except:
                print("Leader's Device IP is not retrieved yet!!!")

            t.sleep(10)


#Fog Area resource information storing into the CIMI+Dataclay
    def fogarea(self):

        t.sleep(20)
        global fogarea_info
        self.fogresourceid =None
        while self.deviceID_cimiresource is None:
            t.sleep(0.1)
        deviceID = self.userID
        dID = str(deviceID)
        devID = {"device": dID}
        MyleaderID = {"leaderDevice": {'href': str(self.deviceID_cimiresource)}}

        while self._running:

            r23 = requests.get("{}/api/device".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"},
                               verify=False)

            devices_info = r23.json()
            ss_info = devices_info['devices']
            try:

                r24 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)

                dynamics_info = r24.json()
                rs_info = dynamics_info['deviceDynamics']

            ##Sorting out the devices those are die-out and update the status field value##
                for dd in rs_info:
                    timestamp = ((datetime.strptime(dd['updated'], '%Y-%m-%dT%H:%M:%S.%fZ')) - datetime(1970, 1,1)).total_seconds()
                    dd['updated'] = timestamp

                rsmd_info = rs_info
                ts = [item0['updated'] for item0 in rsmd_info]
                maxts = max(ts)
                maxtsl = (maxts - 600)
                for mdd in rsmd_info:
                    if (maxtsl > mdd['updated']):
                        mdst = "unavailable"
                        ddresid = mdd['id']
                        ddsresid = str(ddresid)
                        url_point = "{}/api/".format(self.cimi_endpoint)
                        dd_end_url_point = str(url_point + ddsresid)
                        mdstatus = {"status": mdst}
                        try:
                            try:
                                r411 = requests.put(dd_end_url_point,
                                                headers={"slipstream-authn-info": "internal ADMIN"}, json=mdstatus,
                                                verify=False)
                                print("For Fog-Area, updating device-dynamic resource info for die-out device: ", r411, r411.request, r411.reason, r411.json())
                            except:
                                pass
                            r511 = requests.get("{}/api/device-dynamic".format(self.cimi_endpoint),
                                                headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                            print("For Fog-Area, response to see updated device-dynamic resources info: ", r511, r511.request, r511.reason, r511.json())

                        except ConnectionError as e:
                            print(e)
                            r = "No response"
                            print(r)


                    else:
                        pass

                mdrs_info = rsmd_info

                dynamics_info['deviceDynamics'] = mdrs_info
                modifiedDynamic_info = dynamics_info
                mdDdyna = json.dumps(modifiedDynamic_info)

                res_info = [i for i in mdrs_info if not (i['status'] == "unavailable" or i['status'] == "disconnected")]

                ts = [item0['updated'] for item0 in res_info]
                deviceno = len(ts)

                physicalcores_set = [item5['physicalCores'] for item5 in ss_info]
                logicalcores_set = [item6['logicalCores'] for item6 in ss_info]

                ram_set = [item2['ramFree'] for item2 in res_info]
                storage_set = [item3['storageFree'] for item3 in res_info]
                cpu_set = [item4['cpuFreePercent'] for item4 in res_info]
                remsec_set = [item7['powerRemainingStatusSeconds'] for item7 in res_info]

                string_power = []
                integer_power = []
                z = None

                for z in remsec_set:
                    if z == "Unlimited":
                        string_power.append(z)
                    elif z == "BatteryTime.POWER_TIME_UNLIMITED":
                        string_power.append(z)
                    else:
                        integer_power.append(int(z))


                if len(ram_set) > 1:
                    max_ram = float(max(ram_set))
                    min_ram = float(min(ram_set))
                    total_ram = float(sum(ram_set))

                elif len(ram_set) == 1:
                    max_ram = float(ram_set[0])
                    min_ram = float(ram_set[0])
                    total_ram = float(ram_set[0])

                else:
                    max_ram = float(0.0)
                    min_ram = float(0.0)
                    total_ram = float(0.0)

                if len(storage_set) > 1:
                    max_store = float(max(storage_set))
                    min_store = float(min(storage_set))
                    total_store = float(sum(storage_set))

                elif len(storage_set) == 1:
                    max_store = float(storage_set[0])
                    min_store = float(storage_set[0])
                    total_store = float(storage_set[0])
                else:
                    max_store = float(0.0)
                    min_store = float(0.0)
                    total_store = float(0.0)

                if len(cpu_set) > 1:
                    max_cpu = float(max(cpu_set))
                    min_cpu = float(min(cpu_set))
                    avg_cpu = float(sum(cpu_set) / len(cpu_set))

                elif len(cpu_set) == 1:
                    max_cpu = float(cpu_set[0])
                    min_cpu = float(cpu_set[0])
                    avg_cpu = float(cpu_set[0])

                else:
                    max_cpu = float(0.0)
                    min_cpu = float(0.0)
                    avg_cpu = float(0.0)

                if len(physicalcores_set) > 1:
                    max_phycore = int(max(physicalcores_set))
                    min_phycore = int(min(physicalcores_set))
                    avg_phycore = int(round(sum(physicalcores_set) / len(physicalcores_set)))

                elif len(physicalcores_set) == 1:
                    max_phycore = int(physicalcores_set[0])
                    min_phycore = int(physicalcores_set[0])
                    avg_phycore = int(physicalcores_set[0])
                else:
                    max_phycore = int(0)
                    min_phycore = int(0)
                    avg_phycore = int(0)

                if len(logicalcores_set) > 1:
                    max_logicore = int(max(logicalcores_set))
                    min_logicore = int(min(logicalcores_set))
                    avg_logicore = int(round(sum(logicalcores_set) / len(logicalcores_set)))

                elif len(logicalcores_set) == 1:
                    max_logicore = int(logicalcores_set[0])
                    min_logicore = int(logicalcores_set[0])
                    avg_logicore = int(logicalcores_set[0])
                else:
                    max_logicore = int(0)
                    min_logicore = int(0)
                    avg_logicore = int(0)

                if z is not None and z != []:
                    max_powremain = "one or more devices has/have external power sources"
                    if len(integer_power) > 1:
                        min_powremain = str(min(integer_power))
                    elif len(integer_power) == 1:
                        min_powremain = str(integer_power[0])
                    else:
                        min_powremain = '100.0'
                else:
                    if len(integer_power) > 1:
                        max_powremain = str(max(integer_power))
                        min_powremain = str(min(integer_power))
                    elif len(integer_power) == 1:
                        max_powremain = str(integer_power[0])
                        min_powremain = str(integer_power[0])
                    else:
                        max_powremain = "100.0"
                        min_powremain = "100.0"

                if total_ram != float(0.0) and total_store != float(0.0) and avg_cpu != float(0.0):


                    fogarea_par_info = {"numDevices": deviceno, "ramTotal": total_ram, "ramMax": max_ram, "ramMin": min_ram,
                                "storageTotal": total_store, "storageMax": max_store, "storageMin": min_store,
                                "avgProcessingCapacityPercent": avg_cpu, "cpuMaxPercent": max_cpu,
                                "cpuMinPercent": min_cpu, "avgPhysicalCores": avg_phycore,
                                "physicalCoresMax": max_phycore, "physicalCoresMin": min_phycore,
                                "avgLogicalCores": avg_logicore, "logicalCoresMax": max_logicore,
                                "logicalCoresMin": min_logicore, "powerRemainingMax": max_powremain,
                                "powerRemainingMin": min_powremain}

                    fogarealo_info = {**MyleaderID, **fogarea_par_info}
                    fogarea_info = json.dumps(fogarealo_info)
                    print("Fog Area info :", fogarealo_info)
                    try:
                        if self.fogresourceid is None:
                            r7 = requests.post("{}/api/fog-area".format(self.cimi_endpoint),
                                       headers={"slipstream-authn-info": "internal ADMIN"}, json=fogarealo_info,
                                       verify=False)
                            print("Posted Fog-Area resource info: ", r7, r7.request, r7.reason, r7.json())
                            r71 = requests.get("{}/api/fog-area".format(self.cimi_endpoint), headers={"slipstream-authn-info": "internal ADMIN"},verify=False)
                            print("Response to GET the Fog-Area resource info: ", r71, r71.request, r71.reason, r71.json())

                            try:
                                self.fogresourceid = r7.json()['resource-id']
                            except KeyError as k:
                                print(k)
                                print("No devices are attached with the leader")
                        else:
                            r8 = requests.put("{}/api/fog-area".format(self.cimi_endpoint),
                                      headers={"slipstream-authn-info": "internal ADMIN"}, json=fogarealo_info,
                                      verify=False)
                            print("Updated Fog-Area resource info: ", r8, r8.request, r8.reason, r8.json())
                            r81 = requests.get("{}/api/fog-area".format(self.cimi_endpoint),
                                           headers={"slipstream-authn-info": "internal ADMIN"}, verify=False)
                            print("Response to GET the updated Fog-Area resource info: ", r81, r81.request, r81.reason, r81.json())

                    except ConnectionError as e:
                        print("Wait for sometimes to prepare the Fog Area resource Information")
                else:
                    print("Wait for the Alpine container to up and get all the relevant information")
            except:
                print("The Fog-Area resources have some problem!!! Please wait for sometimes!!!")

            t.sleep(10)


#Calling the Main Class
main = Main()



#Starting point of the resource-categorization module
@app.route('/api/v1/resource-management/categorization/start', methods=['GET', 'POST'], strict_slashes=False)
def start():
    global example, isStarted
    if isStarted:
        return jsonify({'error':True})
    getje = request.get_json()
    userid = request.json['deviceID']
    if 'detectedLeaderID' not in getje:
        leaderid = 'Not attached with any Leader Agent'
    else:
        leaderid = request.json['detectedLeaderID']
    if 'isLeader' not in getje:
        isleader = False
    else:
        isleader = request.json['isLeader']

    main.start(userid, leaderid, isleader)
    isStarted = True
    return jsonify({'started': True})


#Switch the normal agent to leader agent
@app.route('/api/v1/resource-management/categorization/leader-switch', methods=['GET', 'POST'], strict_slashes=False)
def switch():
    # global example, isStarted
    global switch_flag
    # if isStarted:
    # return jsonify({'started':'It was started'})
    userid = request.json['deviceID'] ## Need to get the CIMI deviceID ##
    # leaderid = request.json['detectedLeaderID']
    switch_flag = True
    isleader = True
    # print('DEBUG', 'I\'m a leader {}'.format(isleader))
    main.switch(userid, switch_flag, isleader)
    # isStarted = True
    return jsonify({'started': True})





#Application running on localhost and port='46070'
app.run(host='0.0.0.0',port=46070)
