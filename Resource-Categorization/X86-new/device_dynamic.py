import psutil
import platform
import json
from os import getenv
import docker


docker_client = docker.from_env()


class my_dict(dict):
    def __missing__(self, key):
        return 'Empty'

def dynamic_info():
    def hwsw_dyna_info():

        global power_plugged, power_remaining_status, power_remaining_time_info

        available_ram_size = float(psutil.virtual_memory()[1])
        RAM_size = ((available_ram_size / 1024) / 1024)
        available_ram_size_in_percentage = 100 - psutil.virtual_memory()[2]

        OS = platform.system()
        if OS == 'Linux':
            du = tuple(psutil.disk_usage('/'))
        elif OS == 'Windows':
            du = tuple(psutil.disk_usage('C:\\'))
        elif OS == 'ios':
            du = tuple(psutil.disk_usage('/'))
        else:
            du = tuple(psutil.disk_usage('Internal storage'))

        available_storage_size_in_bytes = float(du[2])
        Storage_size = ((available_storage_size_in_bytes / 1024) / 1024)
        available_storage_size_in_percentage = 100 - du[3]

        cpu_status = psutil.cpu_percent()
        available_cpu_in_percentage = 100 - cpu_status

        os = platform.system()
        if os == 'Linux':
            try:
                power_plugged = psutil.sensors_battery()[2]
                power_remaining_status = str(psutil.sensors_battery()[0])
                power_remaining_time_info = str(psutil.sensors_battery()[1])
            except:
                power_plugged = True
                power_remaining_status = "Unlimited"
                power_remaining_time_info = "Unlimited"

        elif os == 'Windows':
            try:
                power_plugged = psutil.sensors_battery()[2]
                power_remaining_status = str(psutil.sensors_battery()[0])
                power_remaining_time_info = str(psutil.sensors_battery()[1])
            except:
                power_plugged = True
                power_remaining_status = "Unlimited"
                power_remaining_time_info = "Unlimited"



        target_device = getenv('targetDeviceActuator')
        if target_device == 'N':
            tgdv = 'The agent has not connected with any actuator'
        elif target_device == 'A--N':
            tgdv = 'The agent has not connected with the unanmed actuator'
        elif target_device == 'A-AFST':
            tgdv = 'It has Ambulance, Firetruck, Sirene, Traffic light'
        elif target_device == 'A-AFS':
            tgdv = 'It has Ambulance, Firetruck, Sirene'
        elif target_device == 'A-AST':
            tgdv = 'It has Ambulance, Sirene, Traffic light'
        elif target_device == 'A-AFT':
            tgdv = 'It has Ambulance, Firetruck, Traffic light'
        elif target_device == 'A-AF':
            tgdv = 'It has Ambulance, Firetruck'
        elif target_device == 'A-AS':
            tgdv = 'It has Ambulance, Sirene'
        elif target_device == 'A-AT':
            tgdv = 'It has Ambulance, Traffic light'
        elif target_device == 'A-A':
            tgdv = 'It has Ambulance'
        elif target_device == 'A-F':
            tgdv = 'It has Firetruck'
        elif target_device == 'A-FS':
            tgdv = 'It has Firetruck, Sirene'
        elif target_device == 'A-FT':
            tgdv = 'It has Firetruck, Traffic light'
        elif target_device == 'A-FST':
            tgdv = 'It has Firetruck, Sirene, Traffic light'
        elif target_device == 'A-S':
            tgdv = 'It has Sirene'
        elif target_device == 'A-ST':
            tgdv = 'It has Sirene, Traffic light'
        elif target_device == 'A-T':
            tgdv = 'It has Traffic light'
        else:
            tgdv = 'Please check your actuator connection'


        hwsw_dyna = json.dumps({'ramFree': RAM_size,
                                'ramFreePercent': available_ram_size_in_percentage,
                                'storageFree': Storage_size,
                                'storageFreePercent': available_storage_size_in_percentage, 'cpuFreePercent': available_cpu_in_percentage,
                                'powerRemainingStatus': power_remaining_status,
                                'powerRemainingStatusSeconds': power_remaining_time_info, 'powerPlugged': power_plugged, 'actuatorInfo':tgdv })

        return hwsw_dyna

### Network information collection
    def net_dyna_info():
        global ethernet_throughput_info, wifi_throughput_info, ethe_address_NIC, wifi_address_NIC, net_dyna

        OS = platform.system()
        if OS == 'Linux':
            net_if_add = psutil.net_if_addrs()
            net_if_add = my_dict(net_if_add)
            net_io = psutil.net_io_counters(pernic=True)
            net_io = my_dict(net_io)
            x = []
            keys = net_io.keys()
            sub = 'enp'
            sub1 = 'wl'
            a = ''
            b = ''
            for key in keys:
                x.append(key)
                a = (next((s for s in x if sub in s), None))
                b = (next((s for s in x if sub1 in s), None))
            if 'eth0' in x and 'wlan0' in x:
                wifi_throughput_info1 = list(net_io['wlan0'])
                ethernet_throughput_info1 = list(net_io['eth0'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif a in x and 'wlan0' in x:
                wifi_throughput_info1 = list(net_io['wlan0'])
                ethernet_throughput_info1 = list(net_io[a])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif 'eth0' in x and b in x:
                wifi_throughput_info1 = list(net_io[b])
                ethernet_throughput_info1 = list(net_io['eth0'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif a in x and b in x:
                wifi_throughput_info1 = list(net_io[b])
                ethernet_throughput_info1 = list(net_io[a])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif 'eth0' in x:
                wifi_throughput_info1 = list(net_io['Null'])
                ethernet_throughput_info1 = list(net_io['eth0'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif a in x:
                wifi_throughput_info1 = list(net_io['Null'])
                ethernet_throughput_info1 = list(net_io[a])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif 'wlan0' in x:
                wifi_throughput_info1 = list(net_io['wlan0'])
                ethernet_throughput_info1 = list(net_io['Null'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif b in x:
                wifi_throughput_info1 = list(net_io[b])
                ethernet_throughput_info1 = list(net_io['Null'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]
        else:
            net_if_add = psutil.net_if_addrs()
            net_io = psutil.net_io_counters(pernic=True)
            x = []
            for key in net_io:
                x.append(key)
            if 'Ethernet' and 'Wi-Fi' in x:
                wifi_throughput_info1 = list(net_io['Wi-Fi'])
                ethernet_throughput_info1 = list(net_io['Ethernet'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif 'Ethernet' in x:
                wifi_throughput_info1 = list(net_io['Null'])
                ethernet_throughput_info1 = list(net_io['Ethernet'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

            elif 'Wi-Fi' in x:
                wifi_throughput_info1 = list(net_io['Wi-Fi'])
                ethernet_throughput_info1 = list(net_io['Null'])
                wifi_throughput_info = [str(item) for item in wifi_throughput_info1]
                ethernet_throughput_info = [str(item) for item in ethernet_throughput_info1]

        net_dyna = json.dumps({'ethernetThroughputInfo': wifi_throughput_info,
                               'wifiThroughputInfo': ethernet_throughput_info, 'ethernetAddress': "None"})
        return net_dyna


    c = hwsw_dyna_info()
    d = net_dyna_info()
    C = json.loads(c)
    D = json.loads(d)
    z = {**C, **D}
    jsonString_merged_dynamic = json.dumps(z)
    return jsonString_merged_dynamic
