from subprocess import call,Popen,PIPE
import time,sys,psutil
import json,requests

class Watcher(object):
     
    DISCONNECTED = False     
    
    @staticmethod
    def on_topology_changed():
        #-a allows hostapd_cli to run in daemon mode executing the action file based on events from hostapd
        command = ['hostapd_cli' ,'-a', 'onHostapdChange.sh']
        #subprocess.call(command)
        process = Popen(command,stdout=PIPE, stderr=PIPE)
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline().decode()
            if nextline == '' and process.poll() is not None:
                break
                
            if "left" in nextline[17:]:
                mac_addr = nextline[:17]
                
                Watcher.update(mac_addr)

            #Just print to stdout as well
            sys.stdout.write("At "+str(time.time())+" "+nextline)
            sys.stdout.flush()
    
        output = process.communicate()[0]
        exitCode = process.returncode
    
        if (exitCode != 0):
            print("Exitcode: "+str(exitCode))
        else:
            print(output)
            
    @staticmethod
    def stop():
        watching = Watcher.check_watching_running("hostapd_cli")
        if not watching:
            return "Watcher already inactive!"
        
        cmd = ['pkill','hostapd_cli']
        pipes = Popen(cmd, stdout=PIPE, stderr=PIPE)
        std_out, std_err = pipes.communicate()

        if pipes.returncode != 0:
            # an error happened!
            msg = "Unable to stop watching, Return Code: "+str(pipes.returncode)
            
        msg = std_out.decode('utf-8')
        if not Watcher.check_watching_running("hostapd_cli"):
            msg = "Watcher stopped successfully!"

        return msg
            
    @staticmethod
    def on_leader_connection_changed():
        command = ['wpa_cli' ,'-a', 'onWpaCliChange.sh']
        process = Popen(command,stdout=PIPE, stderr=PIPE)
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline().decode()
            if nextline == '' and process.poll() is not None:
                break
            
            if "DISCONNECTED" in nextline:
                Watcher.DISCONNECTED = True
            elif "CONNECTED" in nextline:
                Watcher.DISCONNECTED = False

            #Just print to stdout as well
            sys.stdout.write("At "+str(time.time())+" "+nextline)
            sys.stdout.flush()
    
        output = process.communicate()[0]
        exitCode = process.returncode
    
        if (exitCode != 0):
            print("Exitcode: "+str(exitCode))
        else:
            print(output)
    
    @staticmethod    
    def update(mac_addr):
        
        CIMI_URL = 'http://localhost'
        CIMI_API = 'http://localhost/api'
        CIMI_HEADERS = {'Content-Type': 'application/json','slipstream-authn-info': 'internal ADMIN'}
    
        url_device = CIMI_URL+'/api/device-dynamic'
        
        #check if device exists using cimi filtering
        params = {'$filter':'wifiAddress="'+mac_addr+'"'}
        
        try:
            r_device_get = requests.get(url_device,params=params,headers=CIMI_HEADERS,verify=False)
            exists = r_device_get.json()['count']
            
            
            if exists == 0:
            
                print ("Unable to update device with MAC address ", mac_addr," . This device does not exist.")
                
            else:
                
                device_id = r_device_get.json()["deviceDynamics"][0]["id"]
                
                data = {'status':'disconnected'}
            
                try:
                    r_device_put = requests.put(CIMI_API+"/"+device_id, headers=CIMI_HEADERS,json=data,verify=False)
                    print (r_device_put.json())
                    
                except requests.exceptions.RequestException as e:
                    print("An exception occurred while trying to connect to CIMI!")
            
        except requests.exceptions.RequestException as e:
            print("An exception occurred while trying to connect to CIMI!")
            
    @staticmethod       
    def check_watching_running(processName):

        #Iterate over the all the running process
        for proc in psutil.process_iter():
            try:
                # Check if process name contains the given name string.
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
        
        
        

            

        