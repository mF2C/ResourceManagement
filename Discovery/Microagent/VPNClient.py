import docker,pprint,ast,requests,json
import socket,netifaces,subprocess,time

VPNCLIENTCONFIG = {
    "image":"mf2c/vpnclient:1.1.5arm",
    "network_mode":"host",
    "extra_hosts":{'vpnserver':'213.205.14.13'},
    "cap_add": ["NET_ADMIN"],
    "volumes":{'pkidata': {'bind': '/pkidata', 'mode': 'rw'},
               'vpninfo': {'bind': '/vpninfo', 'mode': 'rw'}},
    "environment":{"VPNINFO":"/vpninfo/vpnclient.status"},
    "name":"mf2c_micro_vpnclient",
    "labels":{"mf2c.component":"True","mf2c.agent.type":"microagent"}
    }

def is_internet_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    
    return False

def is_vpn_connected():
    try:
        res = requests.get('http://localhost:1999/api/get_vpn_ip')
        status = res.json()['status']
        if status == "connected":
            return True
        else:
            return False
    except Exception as e:
        return False

def get_running_vpnclients():
    #find the containers running based on the vpnclient image
    client = docker.from_env()
    running_containers = client.containers.list(filters={"status":"running"})
    
    running_vpn_containers = []
    for container in running_containers:
        container_im = container.attrs['Config']['Image']
        if "vpnclient" in container_im:
            running_vpn_containers.append(container)
    return running_vpn_containers

def connect_to_vpn():
    
    #check if already connected
    vpn_connected = is_vpn_connected()

    if vpn_connected:
        print("[Discovery] "+"Already connected to VPN!")
    else:
        if is_internet_connected():
            
            running_vpn_cl_list = get_running_vpnclients()
            if len(running_vpn_cl_list) > 0:
                for running_vpn_cl in running_vpn_cl_list:
                    running_vpn_cl.remove(force=True)
            try:
                print("[Discovery] "+"Connecting to VPN with the following parameters: \n")
                pprint.pprint(VPNCLIENTCONFIG)
                print("\n")
                client = docker.from_env()
                container = client.containers.run(VPNCLIENTCONFIG["image"],
                                      network_mode=VPNCLIENTCONFIG["network_mode"],
                                      extra_hosts=VPNCLIENTCONFIG["extra_hosts"],
                                      cap_add = VPNCLIENTCONFIG["cap_add"],
                                      volumes=VPNCLIENTCONFIG["volumes"],
                                      environment=VPNCLIENTCONFIG["environment"],
                                      labels=VPNCLIENTCONFIG["labels"],
                                      name=VPNCLIENTCONFIG["name"],
                                      detach=True)
                for line in container.logs(stream=True):
                    print ("[VPN Client] "+line.strip().decode("utf-8"))
                    if "INFO OVPN created; launching client" in line.strip().decode("utf-8"):
                        break
                
                timeout = time.time()+120
                while True:
                    if is_vpn_connected() or time.time() > timeout:
                        break

            except Exception as e:
                print(e)
                    
        else:
            print("[Discovery] No internet connection available! Unable to connect to the VPN.")
