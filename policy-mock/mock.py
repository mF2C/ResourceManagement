import json, requests,sys, logging,time
import http.client as http_client

int_name = sys.argv[2]
how_run = sys.argv[3]

if how_run == "script":
    DISCOVERY_NAME = 'discovery'
else:
    DISCOVERY_NAME = '127.0.0.1'

if sys.argv[1] == "leader":
    
    print("\nPerforming the REST call to get the IP address of the leader")
    #Getting IP
    r_ip = requests.get('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/my_ip/')
    print(r_ip.json())
    
    print("\nPerforming REST call to start broadcasting")
    r = requests.post('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/broadcast/',
        json={"broadcast_frequency":"100", "interface_name":int_name, "config_file":"mF2C-VSIE.conf", "leader_id":"0f848d8fb78cbe5615507ef5a198f660ac89a3ae03b95e79d4ebfb3466c20d54e9a5d9b9c41f88c782d1f67b32231d31b4fada8d2f9dd31a4d884681b784ec5a"})
    
    print ("Response code: ",r.status_code)
    print(r.json()["message"])
    
    print ("\nPerforming REST call to start the DHCP server")
    r_dns = requests.post('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/dhcp/',json={"interface_name":int_name})
    print ("Response code: ",r_dns.status_code)
    print(r_dns.json()["message"])
    
    print ("\nPerforming REST call to start watching for agents leaving/joining")
    r_w = requests.get('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/watch/')
    print ("Response code: ",r_w.status_code)
    print(r_w.json()["message"])

    
elif sys.argv[1] == "agent":  
    
    print("\nPerforming the REST call to get the assigned IP")
    #Getting IP
    r3 = requests.get('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/my_ip/')
    print(r3.json())
    
    # REST call to scan 10 times or until results not empty
    print("\nPerforming REST call to scan 10 times or until results are not empty")
    
    found_leaders = [] 
    nb_attempts = 0     
    
    while len(found_leaders) == 0 and nb_attempts<5:
        r = requests.get('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/scan/'+int_name)
        print ("Response code: ",r.status_code)
        found_leaders = r.json()['found_leaders']
        print ("Found leaders:\n",len(found_leaders))
        print("Found leader:\n",found_leaders)
        nb_attempts+=1
        time.sleep(5)
    
    if len(found_leaders) == 0:
        print ("No leader found. Not continuing the flow")
    else:
        bssid = found_leaders[0]['Bssid']
        
        print("\nPerforming REST call to JOIN")
        r2 = requests.post('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/join/',
                            json={"interface":int_name, "bssid":bssid})
        print ("Response code: ",r2.status_code)
         
        print(r2.json()["message"])
        
        
        print("\nPerforming the REST call to get the assigned IP")
        #Getting IP
        r3 = requests.get('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/my_ip/')
        print(r3.json())
         
        print("\nREST call to start watching")
        payload = {'key': 'start'}
        r4 = requests.get('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/watch_agent_side/',params=payload)
        print(r4.json()["message"]) #will return 'message': "Started watching connection to leader!"
        
        print("\nREST call to check whether the agent is DISCONNECTED or not")
        nb_attempts2 = 0
        while nb_attempts2<10:
            payload = {'key': 'get'}
            r5 = requests.get('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/watch_agent_side/',params=payload)
            print("Disconnected= ",r5.json()["DISCONNECTED"])
            nb_attempts2+=1
            time.sleep(5)
            
        print("\nPerforming REST call to UNJOIN")
        r6 = requests.put('http://'+DISCOVERY_NAME+':46040/api/v1/resource-management/discovery/join/')
        print ("Response code: ",r6.status_code)
         
        print(r6.json()["message"])
            
