from JoinConfig import *
import os,netifaces

interface = os.environ['interface']
interfaces = netifaces.interfaces()
#check if the given interface exists
if interface not in interfaces:
    print ("None")
else:
    print(JoinConfig.get_ip(interface))
