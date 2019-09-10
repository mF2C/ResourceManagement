from Broadcaster import *
from Scanner import *
from JoinConfig import *
from InformationElementAttribute  import *
from JoinConfig import *
import os, sys
import netifaces


if __name__ == '__main__': 
        
    if os.getuid() != 0:
        print ("[mF2C/Discovery] Did you forget to use \"sudo\"?")
    else:
        
        if len(sys.argv) < 3: #checking minimum number of arguments
            
            print ("[mF2C/Discovery] This program should run as:\nsudo python3 main.py interface_name function(b/s/j) (broadcast_frequency) (config_file)")
            sys.exit()
        interfaces = netifaces.interfaces()
        if sys.argv[1] not in interfaces:
            print ("[mF2C/Discovery] "+sys.argv[1] +" does not exist.")
            sys.exit()
   
        if sys.argv[2] == "b":
            if len(sys.argv) != 5: # if arg#2 was 'b', then the following two arguments should be set, we check if this is true
                print ("[mF2C/Discovery] This program should run as:\nsudo python3 main.py interface_name function(b/s) (broadcast_frequency) (config_file)")
                sys.exit()
            #Theoretically, this should be coming from policies
            if int(sys.argv[3]) not in range(15,65535):
                print ("[mF2C/Discovery] Beacon interval should be between 15 and 65535" )
                sys.exit()
            def_gw_device = netifaces.gateways()['default'][netifaces.AF_INET][1]
            if (sys.argv[1] == def_gw_device):
                print ("[mF2C/Discovery] "+sys.argv[1]+" is used as the default route. Using it will cause you to lose your internet connection.")
                sys.exit()
                  
            encoding_error = Broadcaster.fill_beacon_fields(sys.argv[3], sys.argv[1],sys.argv[4])
            if not encoding_error:          
                msg = Broadcaster.start_broadcast()
                print("[mF2C/Discovery] "+msg)
            else:
                print("[mF2C/Discovery] Error filling beacon fields. Unexpected config value.")
                sys.exit()
        else:
            if sys.argv[2] == "s":
                s = Scanner()
                results = s.start_scan(sys.argv[1])
                if results[0]:
                    print("[mF2C/Discovery] Oops, the following error occured:")
                    print("[mF2C/Discovery] "+results[1])
                else:
                    found_leaders = s.parse_scan_results(results[2])  
            else:
                if sys.argv[2] == "j":
                    if len(sys.argv) != 4: # if arg#2 was 'j', then the following  argument (BSSID) should be set, we check if this is true
                        print ("[mF2C/Discovery] This program should run as:\nsudo python3 main.py interface_name function(b/s/j) (broadcast_frequency/bssid) (config_file)")
                        sys.exit()
                    else:
                        try:
                            JoinConfig.config(sys.argv[3])
                            JoinConfig.join(sys.argv[1])
                        
                        except (KeyboardInterrupt, SystemExit):
                            print("[mF2C/Discovery] Disassociating from leader")

                        

                    
                    

