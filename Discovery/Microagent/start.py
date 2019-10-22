#!/usr/bin/env python3
from Watcher import *
from Scanner import *
from JoinConfig import *
from InformationElementAttribute  import *
import os, sys, threading,time
import netifaces, subprocess
import time,re
from VPNClient import *

NB_MAX_ATTEMPTS = 5

def get_found_leaders_list(interface_name):
    found_leaders=[]
    
    s = Scanner()
    results = s.start_scan(interface_name)
    #if no error occurred, parse and decode scan results
    if not results[0]:
        found_leaders = s.parse_scan_results(results[2])
    if_to_mac = netifaces.ifaddresses(interface_name)[netifaces.AF_LINK][0]["addr"]
    return {'error_message': results[1], 'found_leaders':found_leaders,"used_mac":if_to_mac}

def join_leader(bssid,interface):
    JoinConfig.config(bssid)
    msg=JoinConfig.join(interface)
    return {'message': msg}
    
def retrieve_ip(interface):
    ip = JoinConfig.get_ip(interface)
    return ip
    

###################################################
################# Main method #####################
###################################################
def main():
    interface = os.environ['interface']

    interfaces = netifaces.interfaces()

    #check if the given interface exists
    if interface not in interfaces:
        print ("[Discovery] "+interface+" does not exist!")
        #connect to vpn
        
        connect_to_vpn() 

    else:
        
        if os.path.exists('/etc/wpa_supplicant/wpa_supplicant.conf') == True and JoinConfig.check(interface):
            print("[Discovery] Already associated with leader!")
        else:

            found_leaders = [] 
            nb_attempts = 0 
            
            while len(found_leaders) == 0 and nb_attempts<NB_MAX_ATTEMPTS:
                print ("[Discovery] "+"Scan attempt # ",nb_attempts+1)
                found_leaders = get_found_leaders_list(interface)["found_leaders"]
                print("[Discovery] "+"Number of found leaders = "+str(len(found_leaders)))    
                nb_attempts += 1
                time.sleep(2)
            
            if len(found_leaders) == 0 :
                print ("[Discovery] "+"No leaders found after performing ",nb_attempts," scans!")
                connect_to_vpn() 
            else:
                bssid = found_leaders[0]['Bssid']
                result = join_leader(bssid,interface)
                print ("[Discovery] "+result["message"])
                if "Successfully" in result["message"]:
                    print("[Discovery] Getting IP address...")
                    ip = retrieve_ip(interface)
                    if ip!= None:
                        print("[Discovery] IP address of "+interface+" = "+ip)
                    else:
                        print("[Discovery] Unable to retrieve IP of "+interface)

if __name__ == '__main__':
    try:
        while True:
            main()
            time.sleep(5)
            print("\n")
    except KeyboardInterrupt:
        print("[Discovery] "+'Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
