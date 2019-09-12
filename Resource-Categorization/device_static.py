import time
import psutil
import platform
import json
import cpuinfo
import subprocess
from os import getenv
import docker
import requests

docker_client1 = docker.from_env()



class my_dict(dict):
    def __missing__(self, key):
        return 'Empty'

def static_info():

    def hwsw_info():
        os_info = platform.platform()

        system_arch = platform.machine()

        a = cpuinfo.get_cpu_info()
        cpu_owner_info = a['brand']
        cpu_clock_speed = a['hz_advertised']

        physical_cpu = psutil.cpu_count(logical=False)

        logical_cpu = psutil.cpu_count()

        mem = psutil.virtual_memory()
        RAM = mem[0]
        total_ram_size = ((RAM / 1024) / 1024)

        OS = platform.system()
        if OS == 'Linux':
            b = tuple(psutil.disk_usage('/'))
        elif OS == 'Windows':
            b = tuple(psutil.disk_usage('C:\\'))
        elif OS == 'ios':
            b = tuple(psutil.disk_usage('/'))
        else:
            b = tuple(psutil.disk_usage('Internal storage'))

        storage = float(b[0])
        total_available_storage = ((storage / 1024) / 1024)

        agent_type = getenv('agentType')
        if agent_type == '1':
            at = 'Cloud Agent'
        elif agent_type == '2':
            at = 'Fog Agent'
        elif agent_type == '3':
            at = 'Micro Agent'
        else:
            at = 'Something is wrong'


        hwsw_stat = json.dumps({'os': os_info, 'arch':system_arch, 'cpuManufacturer': cpu_owner_info, 'physicalCores': physical_cpu,
                      'logicalCores': logical_cpu, 'cpuClockSpeed': cpu_clock_speed,
                      'memory': total_ram_size, 'storage': total_available_storage,
                       'agentType': at})

        return hwsw_stat

    def net_stat_info():
         global ethe_address_NIC, wifi_address_NIC

         try:
            response_discovery = requests.get("http://discovery:46040/api/v1/resource-management/discovery/my_ip/", verify=False)
            res_dis = response_discovery.json()
            devdisIP = res_dis['IP_address']

            if devdisIP != '':
                 net_stat = json.dumps({"networkingStandards": 'WiFi'})

            else:
                time.sleep(45)
                try:
                    ifconfig_out = docker_client1.containers.run("alpine:latest", "ifconfig", network_mode='host', auto_remove=True).decode()
                    time.sleep (10)
                    ifconfig_list = str(ifconfig_out).split('\n\n')
                    ifaces = []

                    for item in ifconfig_list:
                        lines = item.split('\n')
                        name = lines[0].split(' ')[0]
                        if name.find('veth') == -1 and name != 'lo' and name.find('br') == -1 and name.find('docker') == -1 and len(name) > 0:
                            ifaces.append({'iface': name})

                    eta = ([(x['iface']) for x in ifaces])
                    eta2 = str(', '.join(eta))
                    eta3 = str(eta2)
                    eta4 = subprocess.Popen("ip addr show tun0", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                except:
                    eta3 = 'Null'

                net_stat = json.dumps({"networkingStandards": eta3})
         except:
             eta3 = 'Null'
             net_stat = json.dumps({"networkingStandards": eta3})


         return net_stat


    def hwloccpuinfo():
        OS = platform.system()

        if OS == 'Linux':

            hwloc = subprocess.Popen("hwloc-ls --of xml", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cpuinfo = subprocess.Popen("cat /proc/cpuinfo", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            hwloc_xml = ""

            for line in hwloc.stdout.readlines():
                hwloc_xml += line.decode()

            cpu_info = ""
            for line1 in cpuinfo.stdout.readlines():
                cpu_info += line1.decode()

            data = {
                'hwloc': hwloc_xml,
                'cpuinfo': cpu_info
                }
        else:
            hwloc_xml = "This information only provided for the Linux machine"
            cpu_info = "This information only provided for the Linux machine"

            data = {
                'hwloc': hwloc_xml,
                'cpuinfo': cpu_info
            }


        hwcpu = json.dumps(data)
        return hwcpu



    a=hwsw_info()
    b=net_stat_info()
    c= hwloccpuinfo()

    A = json.loads(a)
    B = json.loads(b)
    C = json.loads(c)

    merged_dict_stat = {**A, **B, **C}
    jsonString_merged_static = json.dumps(merged_dict_stat)
    #print(jsonString_merged_static)

    return jsonString_merged_static

#static_info()