from device_static import static_info
from device_dynamic import dynamic_info
from os import getenv
import threading
import time as t
import json
import urllib3
from flask import Flask, jsonify, request
from requests.exceptions import ConnectionError
import requests
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

            ## Threads for the Leader-side
        # else:
        #     thread1 = threading.Thread(target=self.staticLeader, daemon=True, name='staLe')
        #     thread1.start()
        #
        #     self.thread_dyn = threading.Thread(target=self.dynamicLeader, daemon=True, name='dynLe')
        #     self.thread_dyn.start()
        #
        #
        #     self.thread_fogareainfo = threading.Thread(target=self.fogarea, daemon=True, name='leader')
        #     self.thread_fogareainfo.start()


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
            dynamicinfo = json.loads(dyna)
            wifi_ip = dynamicinfo['wifiAddress']
            if wifi_ip == "Null" or wifi_ip == "":
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
                        devDynamic = {**devID, **dynamicinfo, **sensors}
                        jsonString_merged_dynamic = devDynamic
                        r4 = requests.put("{}/api/{}".format(self.cimi_endpoint, self.deviceDynamicID_cimiresource),
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
#@app.route('/api/v1/resource-management/categorization/leader-switch', methods=['GET', 'POST'], strict_slashes=False)
#def switch():

 #   global switch_flag
  #  userid = request.json['deviceID'] ## Need to get the CIMI deviceID ##
   # switch_flag = True
   # isleader = True
   # main.switch(userid, switch_flag, isleader)
   # return jsonify({'started': True})





#Application running on localhost and port='46070'
app.run(host='0.0.0.0',port=46070)