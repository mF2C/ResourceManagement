from subprocess import call,Popen,PIPE
import time,sys
import json
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
            
            if "joined" in nextline[17:]:
                print (nextline[17:])
                mac_addr = nextline[:17]
                #Store through CIMI
                #Watcher.store(mac_addr)

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
        command = ["pkill", "hostapd_cli"]
        call(command)

        


            
            
    @staticmethod
    def on_leader_connection_changed():
        disconnected_var = False
        command = ['wpa_cli' ,'-a', 'onWpaCliChange.sh']
        process = Popen(command,stdout=PIPE, stderr=PIPE)
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline().decode()
            if nextline == '' and process.poll() is not None:
                break
            
            print ("Nextline: ",nextline)
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
        
        