import time
import psutil
import platform
import json
from os import getenv
import docker
import re
docker_client = docker.from_env()


class my_dict(dict):
    def __missing__(self, key):
        return 'Empty'


def dynamic_info():
    def hwsw_dyna_info():

        global power_plugged, power_remaining_status, power_remaining_time_info

        available_ram_size = float(psutil.virtual_memory()[1])
        RAM_size1 = float((available_ram_size / 1024.0) / 1024.0)
        RAM_size = float(RAM_size1)
        available_ram_size_in_percentage1   = float(100.0 - psutil.virtual_memory()[2])
        available_ram_size_in_percentage = float(available_ram_size_in_percentage1)

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
        Storage_size1 = float((available_storage_size_in_bytes / 1024.0) / 1024.0)
        Storage_size = float(Storage_size1)
        available_storage_size_in_percentage1 = float(100.0 - du[3])
        available_storage_size_in_percentage = float(available_storage_size_in_percentage1)

        cpu_status = psutil.cpu_percent()
        available_cpu_in_percentage1 = float(100.0 - cpu_status)
        available_cpu_in_percentage = float(available_cpu_in_percentage1)

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
        global ethernet_throughput_info, wifi_throughput_info, ethe_address_NIC, wifi_address_NIC, net_dyna, devicep1
        ddisIP =''
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
                    running_discovery_containers=[]

            if len(running_discovery_containers) == 1:
                disc_cont_id = running_discovery_containers[0]
                cmd = 'python get_ip_addr.py'
                output = ''
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
                wifi_ip1 = ddisIP
                patip = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
                test1 = patip.match(wifi_ip1)
                if test1:
                    try:
                        devicep1 = wifi_ip1
                    except:
                        devicep1 = ""
                else:
                    devicep1 = ""
                wifi_ip = devicep1
                print('\n\nwifi_ip:{}, ddisIP:{}, test1:{}, output:{}\n\n'.format(wifi_ip,ddisIP, test1, output))
                if wifi_ip != "" and wifi_ip != "None" and wifi_ip != "b'None\\n'":
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

                    net_dyna = json.dumps({'ethernetThroughputInfo': wifi_throughput_info, 'wifiThroughputInfo': ethernet_throughput_info,'ethernetAddress': 'Null', 'wifiAddress': ddisIP})

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

                            if ddisIP != '' or time.time() > timeout:
                                break
                            else:
                                print('\n\ntimeout: {} > {} = {}'.format(time.time(), timeout, time.time() > timeout))
                            time.sleep(1.)
                        wifi_ip1 = ddisIP
                        patip = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
                        test1 = patip.match(wifi_ip1)
                        if test1:
                            try:
                                devicep1 = wifi_ip1
                            except:
                                devicep1 = ""
                        else:
                            devicep1 = ""
                        wifi_ip = devicep1
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
                                               'wifiThroughputInfo': ethernet_throughput_info,
                                               'ethernetAddress': 'Null', 'wifiAddress': wifi_ip})

                    except:
                        ethe_address_NIC = 'Null'
                        wifi_address_NIC = 'Null'
                        ethernet_throughput_info = list('Null')
                        wifi_throughput_info = list('Null')
                        net_dyna = json.dumps({'ethernetThroughputInfo': ethernet_throughput_info,
                                               'wifiThroughputInfo': wifi_throughput_info,
                                               'ethernetAddress': ethe_address_NIC, 'wifiAddress': wifi_address_NIC})
            else:
                ethe_address_NIC = 'Null'
                wifi_address_NIC = 'Null'
                ethernet_throughput_info = list('Null')
                wifi_throughput_info = list('Null')
                net_dyna = json.dumps({'ethernetThroughputInfo': ethernet_throughput_info,
                                       'wifiThroughputInfo': wifi_throughput_info,
                                       'ethernetAddress': ethe_address_NIC, 'wifiAddress': wifi_address_NIC})
            return net_dyna
        except:
            ethe_address_NIC = 'Null'
            wifi_address_NIC = 'Null'
            ethernet_throughput_info = list('Null')
            wifi_throughput_info = list('Null')
            net_dyna = json.dumps({'ethernetThroughputInfo': ethernet_throughput_info, 'wifiThroughputInfo': wifi_throughput_info,'ethernetAddress': ethe_address_NIC, 'wifiAddress': wifi_address_NIC})

        return net_dyna

    c = hwsw_dyna_info()
    d = net_dyna_info()
    C = json.loads(c)
    D = json.loads(d)
    z = {**C, **D}
    jsonString_merged_dynamic = json.dumps(z)
    return jsonString_merged_dynamic

#dynamic_info()