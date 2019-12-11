import time
import psutil
import platform
import json
import cpuinfo
import subprocess
from os import getenv
import docker

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
        try:
            cpu_clock_speed = a['hz_advertised']
        except:
            cpu_clock_speed = "1.4 GHz"
        physical_cpu = psutil.cpu_count(logical=False)
        logical_cpu = psutil.cpu_count()
        mem = psutil.virtual_memory()
        RAM = mem[0]
        total_ram_size1 = ((RAM / 1024) / 1024)

        total_ram_size = float(total_ram_size1)

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
        total_available_storage1 = ((storage / 1024) / 1024)
        total_available_storage = float(total_available_storage1)

        agent_type = getenv('agentType')
        if agent_type == '1':
            at = 'cloud'
        elif agent_type == '2':
            at = 'normal'
        elif agent_type == '3':
            at = 'micro'
        else:
            at = 'empty'


        hwsw_stat = json.dumps({'os': os_info, 'arch':system_arch, 'cpuManufacturer': cpu_owner_info, 'physicalCores': physical_cpu,
                                'logicalCores': logical_cpu, 'cpuClockSpeed': cpu_clock_speed,
                                'memory': total_ram_size, 'storage': total_available_storage,
                                'agentType': at})

        return hwsw_stat

    def net_stat_info():
        global ethe_address_NIC, wifi_address_NIC, net_stat
        ddisIP = ''
        try:
            client = docker.from_env()
            running_containers = client.containers.list(filters={"status": "running"})
            running_discovery_containers = []
            for container in running_containers:
                container_im = container.attrs['Config']['Image']
                try:
                    if "discovery" in container_im:
                        running_discovery_containers.append(container)
                except:
                    running_discovery_containers = []

            if len(running_discovery_containers) == 1:
                disc_cont_id = running_discovery_containers[0]
                cmd = 'python get_ip_addr.py'
                try:
                    exit_code, output = disc_cont_id.exec_run(cmd, stderr=True, stdout=True, demux=True)
                    if exit_code == 0:
                        ip = output[0]  # output[0] is the stdout
                        ddisIP = bytes(ip).decode()
                        ddisIP = ddisIP[:-1]
                    else:
                        ddisIP = "None"
                except:
                    ddisIP = "None"
                if ddisIP != "" and ddisIP != "None" and ddisIP != "b'None\\n'":
                    net_stat = json.dumps({"networkingStandards": 'WiFi'})
                else:
                    try:
                        timeout = time.time() + 60 * 2
                        while True:
                            ddisIP = ''
                            try:
                                with open('/vpninfo/vpnclient.status', mode='r') as json_file:
                                    json_txt = json_file.readlines()[0]
                                    ljson = json.loads(json_txt)
                                    if ljson['status'] == 'connected':
                                        ddisIP = str(ljson['ip'])
                                        print(
                                            'VPN IP successfully parsed from JSON file at \'{}\'. Content: {} IP: {}'.format(
                                                '/vpninfo/vpnclient.status',
                                                str(ljson),
                                                ddisIP))
                                    else:
                                        print('VPN JSON status != \'connected\': Content: {}'.format(str(ljson)))
                            except OSError:
                                print('VPN file cannot be open or found at \'{}\'.'.format('/vpninfo/vpnclient.status'))
                            except (IndexError, KeyError):
                                print('VPN error on parsing the IP.')
                            except:
                                print('VPN generic error.')
                            if ddisIP != "" or time.time() > timeout:
                                break
                        net_stat = json.dumps({"networkingStandards": "Ethernet"})
                    except:
                        eta3 = 'Null'
                        net_stat = json.dumps({"networkingStandards": eta3})
            return net_stat
        except:
            eta3 = 'Null'
            net_stat = json.dumps({"networkingStandards": eta3})
            return net_stat


    def hwloccpuinfo():
        OS = platform.system()

        if OS == 'Linux':


            with open('/etc/hostname', mode = 'r') as file:
                txt = file.readlines()[0]
                host = str(txt)

            hwloc = subprocess.Popen("hwloc-ls --of xml", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cpuinfo = subprocess.Popen("cat /proc/cpuinfo", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            hwloc_xml = ""

            for line in hwloc.stdout.readlines():
                hwloc_xml += line.decode()

            lstring = hwloc_xml.split('IRILD039')
            try:
                hwloc_xml = lstring[0] + host.rstrip() + lstring[1]
            except:
                print('Error hostname')

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


    return jsonString_merged_static

#static_info()



