from Vsie import *
from InformationElementAttribute import *
from subprocess import call,check_output,STDOUT,CalledProcessError,Popen,PIPE
import signal,sys,os
import configparser
import shlex

class Broadcaster(object): 
     
    @staticmethod
    def start_broadcast():  

        cmd = ['service','hostapd','start']

        pipes = Popen(cmd, stdout=PIPE, stderr=PIPE)
        std_out, std_err = pipes.communicate()

        if pipes.returncode != 0:
            # an error happened!
            msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            
        msg = std_out.decode('utf-8')
        if "failed" in msg:
            msg = "Broadcaster start failed!"
        else:
            msg = "Broadcaster started successfully!"
        return msg
        
    
    @staticmethod
    def stop_broadcast(): 
        #check if already stopped
        if not Broadcaster.check_active():
            return "Broadcaster is already stopped!"
        
        cmd = ['service','hostapd','stop']

        pipes = Popen(cmd, stdout=PIPE, stderr=PIPE)
        std_out, std_err = pipes.communicate()

        if pipes.returncode != 0:
            # an error happened!
            msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            
        msg = std_out.decode('utf-8')
        if "failed" in msg:
            msg = "Broadcaster stop failed!"
        else:
            msg = "Broadcaster successfully stopped!"
        return msg
        
    @staticmethod
    def check_active(): 
        #if the configuration file is not set, then hostapd is not working:
        if os.path.exists('/etc/hostapd/hostapd.conf') == False:
            return False
          
        command = ['service','hostapd','status']
        try:
            out = check_output(command).decode()
        except CalledProcessError as e:
            out = e.output.decode()
            
        if "is running" in out:
            is_running=True
        else:
            is_running=False
        return is_running

    @staticmethod
    def check_dnsmasq_active():   
        command = ['service','dnsmasq','status']
        try:
            out = check_output(command).decode()
        except CalledProcessError as e:
            out = e.output.decode()
            
        if ("pid file exists" in out) or ("(running)" in out):
            is_running=True
        else:
            is_running=False
        return is_running
    
       
    @staticmethod
    def fill_beacon_fields( broadcast_frequency, interface, config_file,leader_id): 
        config = configparser.ConfigParser() 
        config.read(config_file)
        attribute_list = []
        encoding_error = False
        attribute_list.append(InformationElementAttribute("01",leader_id))
        for section in config.sections():
            if config[section]['type'] not in InformationElementAttribute.TYPES_SWAPPED.keys():
                #if the type is unknown, there will be an error in encoding so this case is checked here
                encoding_error = True
            else:
                type_hex = InformationElementAttribute.TYPES_SWAPPED[config[section]['type']]

                if type_hex == "02":
                    if config[section]['value'] not in InformationElementAttribute.SERVICE_TYPE_DICT_SWAPPED.keys():
                        encoding_error = True
                    else:
                        value_hex = InformationElementAttribute.convert_value_to_hex(type_hex,config[section]['value'])
                else:
                    if type_hex == "04":
                        if config[section]['value'] not in InformationElementAttribute.URGENCY_DICT_SWAPPED.keys():
                            encoding_error = True
                        else:
                            value_hex = InformationElementAttribute.convert_value_to_hex(type_hex,config[section]['value'])
                    else:
                        if type_hex == "03":
                            try:
                                #int(config[section]['value'])
                                value_hex = InformationElementAttribute.convert_value_to_hex(type_hex,config[section]['value'])
                            except ValueError:
                                encoding_error = True                             
                                
                attribute_list.append(InformationElementAttribute(type_hex,value_hex))
        
        
        if not encoding_error:
            #create a vsie out of the different attributes
            vsie = Vsie(attribute_list)
         
            with open("/etc/hostapd/hostapd.conf", "w") as myfile:
               
              content = "ctrl_interface=/var/run/hostapd\n"+"ctrl_interface_group=0\n"+"interface=" + interface + "\n" + "driver=nl80211" + "\n" + "ssid=mf2c-leader" + "\n" + "beacon_int=" + str(broadcast_frequency) + "\n" + "hw_mode=g" + "\n" + "channel=6" + \
              "\n" + "macaddr_acl=0" + "\n" + "auth_algs=1" + "\n" + "ignore_broadcast_ssid=1" + "\n" + "vendor_elements=" + Vsie.create_mf2c_vsie_hex(vsie)
              myfile.write(content)
        return encoding_error
    
    @staticmethod
    def fill_dhcp_config(if_name): 
        with open("/etc/dnsmasq.conf", "w") as dns_file:
            content = "no-resolv\n"+"server=8.8.8.8\n"+"interface=lo,"+if_name+"\n"+"no-dhcp-interface=lo\n"+"dhcp-range=192.168.7.20,192.168.7.254,255.255.255.0,12h\n"+"dhcp-option=3\n"+"dhcp-option=6\n"+"ra-param=*,0,0"
            dns_file.write(content)
        
    @staticmethod
    def start_dhcp():  
        
        if Broadcaster.check_dnsmasq_active():
            return "Dnsmasq is already running!"
        
        cmd = ['service','dnsmasq','start']
        pipes = Popen(cmd, stdout=PIPE, stderr=PIPE)
        std_out, std_err = pipes.communicate()

        if pipes.returncode != 0:
            # an error happened!
            msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            
        msg = std_out.decode('utf-8')
        if "failed" in msg:
            msg = "Dnsmasq start failed!"
        else:
            msg = "Dnsmasq started successfully!"
        return msg
    
    
    @staticmethod
    def stop_dhcp():  
        
        if not Broadcaster.check_dnsmasq_active():
            return "Dnsmasq is already inactive!"
        
        cmd = ['pkill','dnsmasq']
        pipes = Popen(cmd, stdout=PIPE, stderr=PIPE)
        std_out, std_err = pipes.communicate()

        if pipes.returncode != 0:
            # an error happened!
            msg = "Unable to stop dnsmasq, Return Code: "+str(pipes.returncode)
            
        msg = std_out.decode('utf-8')
        if not Broadcaster.check_dnsmasq_active():
            msg = "Dnsmasq stopped successfully!"

        return msg

