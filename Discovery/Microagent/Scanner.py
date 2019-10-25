import subprocess
import re
from Vsie import *
from InformationElementAttribute import *


class Scanner(object): 
    
    def __init__(self) :
        # self.mf2c_oui_found = mf2c_oui_found
        pass
      
    def start_scan(self, interface): 
        error_occured = False
        err_msg = "None"
        #the -u flag is compulsory, since it allows displaying unknown IEs
        #ap-force allows scanning while being an access point at the same time. Not all wireless cards support this
        #passive specifies that the scan is passive
        call_return_1 = subprocess.call(["ip","link","set","dev",interface, "down"])
        call_return_2 = subprocess.call(["ip","link","set","dev",interface, "up"])

        cmd = ["iw", "dev", interface, "scan", "-u", "ap-force", "passive"]
        results=[]
        pipes = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_out, std_err = pipes.communicate()

        if pipes.returncode != 0:
            # an error happened!
            error_occured = True
            err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
        
        results = std_out.decode('utf-8')

        return [error_occured, err_msg, results]
 
    @staticmethod
    def is_mf2c_oui_found(line): 

        ieRe = re.compile(r"Vendor specific: OUI ff:22:cc, data: (?P<vsie_data>.+)")

        return ieRe.search(line) 
    
    @staticmethod
    def get_f2c_ie(item):  
        ieRe = re.compile(r"Vendor specific: OUI ff:22:cc, data: (?P<vsie_data>.+)")
        lines = item.split('\n')
        ie_value =""
        for i in range(len(lines)):
            ie = ieRe.search(lines[i])
            if ie is not None:
                ie_value = ie.groupdict()
        return ie_value
    
    @staticmethod
    def get_mac(item):    
        mac_line = item.split('\n')[0]
        mac_value = mac_line[4:21]
        return mac_value
    
    @staticmethod
    def return_list_of_results(content):
        BSSRe = re.compile(r"^BSS\s[a-f0-9]+(?P<bss>.+)")
    
        single_result_list = []
        single_result = content[0].strip()+'\n'
        content = content[1:]
        for x in range(len(content)):
            line = content[x].strip()+'\n'  # removes spaces
            BSS = BSSRe.search(line)
            
            if BSS is not None or x == len(content)-1:
                single_result_list.append(single_result)
                single_result = line
            else:
                single_result+=line
        return single_result_list
    
    def parse_scan_results(self, scan_results): #for each scan result, we check if it contains mF2C OUI. 
        #if so, the subsequent vendor content is decoded and a new leader is added to the leaders_list
        
        lines = scan_results.split('\n')
        scan_result_list = Scanner.return_list_of_results(lines)
        leaders_list = [] 
        for scan_item in scan_result_list:
            #check if it contains mf2c_ie
            f2c_ie = Scanner.get_f2c_ie(scan_item)
            if f2c_ie != "":
                leader_dict = {"vsie_data":"", "Bssid":"","Leader ID":"Not found","Service type":"Not found","Reward":"Not found","Urgency level":"Not found"}      
                leader_dict["vsie_data"] = f2c_ie["vsie_data"]
                attribute_list = Vsie.get_vendor_specific_content(f2c_ie["vsie_data"])
                for item in attribute_list:
                    key = InformationElementAttribute.get_attribute_dict(item)["type"]
                    value = InformationElementAttribute.get_attribute_dict(item)["value"]
                    leader_dict[key] = value
                leader_dict["Bssid"] =Scanner.get_mac(scan_item)
                #prevents having duplicate leaders since iw may return the same "leader" twice once 
                #from the beacon and the other from the probe response 
                if not any (d.get("Bssid",None)== Scanner.get_mac(scan_item) for d in leaders_list):
                    leaders_list.append(leader_dict)
            else:
                continue
        
        #if len(leaders_list) == 0:
            #print("No mF2C beacons found in this scan!")

        return leaders_list
    

