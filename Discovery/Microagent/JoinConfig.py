import subprocess
import signal,sys,time
import configparser,netifaces
class JoinConfig(object): 
     
    @staticmethod
    def config(bssid):

        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as myfile:
            content = "ctrl_interface=/var/run/wpa_supplicant"+"\n"+"network={"+"\n"+"    key_mgmt=NONE"+"\n"+"    scan_ssid=1"+"\n"+"    bssid="+bssid+"\n"+"    ssid=\"mf2c-leader\""+"\n}"
            myfile.write(content)        
  
    @staticmethod         
    def unjoin():
        subprocess.call(['wpa_cli','terminate'])     
                   
    @staticmethod
    def join(interface):
        error_occured = False
        has_joined=JoinConfig.check(interface)
        if has_joined:
            msg = "Already associated with leader!"
        else:
            
            interface_arg = "-i"+interface

            return_code = subprocess.call(['wpa_supplicant', interface_arg, '-Dnl80211', '-c/etc/wpa_supplicant/wpa_supplicant.conf' ,'-B'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

            if return_code != 0:
            # an error happened!
                msg = "Association failed! Reason: "+str(return_code)
            else:
                #Making sure agent is truly associated to leader and that it is not just a wpa_supplicant false positive
                stop_cond = False
                while stop_cond == False:
                    association_true = JoinConfig.check(interface)
                    if association_true:
                        stop_cond = True
                    time.sleep(1)
                    
                if association_true:
                    msg = "Successfully associated with leader!"
                else:
                    msg= "Association to leader failed. "+interface+" is probably used by the host!"
            
        return msg

    @staticmethod
    def check(interface):   
        command = ['wpa_cli','-i',interface,'status' , '>> log_file.txt 2>&1']
        try:
            #out = subprocess.check_output(command).decode()
            rt_code = subprocess.call(command)
            
        except:
            out = "error"
        
        with open("log_file.txt") as f:
            log_content = f.readlines()
            
        if ("ssid=mf2c-leader" in log_content):
            has_joined=True
        else:
            has_joined=False
        return has_joined
    
    @staticmethod
    def get_ip(interface):
        stop_condition = False
        ip = ''
        while stop_condition == False:
            try:
                ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
            except Exception as e:
                excep = e
            
            if ip != '' and "169.254" not in ip:
                stop_condition = True
            
            time.sleep(1)
        
        return ip
        

