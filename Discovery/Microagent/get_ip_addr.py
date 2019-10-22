from JoinConfig import *
import os,netifaces

interface = os.environ['interface']
interfaces = netifaces.interfaces()
#check if the given interface exists
if interface not in interfaces:
    print (interface+" does not exist!")
else:
    print(JoinConfig.get_ip(interface))
