#!/usr/bin/env python
import re
import subprocess
import pprint
import json
import sys
from prettytable import PrettyTable

mf2c_oui = "ff:22:cc"

BSSRe = re.compile(r"^BSS\s[a-f0-9]+(?P<bss>.+)")

ieRe = re.compile(r"Vendor specific: OUI (?P<vsie_oui>.+), data: (?P<vsie_data>.+)")

service_code_name_dict = {"01":"Virtual Reality","02":"Smart Transportation","03":"Smart Health","04":"Environmental Data Processing"}

def decode_hex(s):
    return ''.join([chr(int(''.join(c), 16)) for c in zip(s[0::2], s[1::2])])


def mf2c_attr_decoder(attr_hex):  # Example Input: 01067a65696e6562
    type = attr_hex[0:2]

    length = attr_hex[2:4]
    value = attr_hex[4:]

    return [type, value]


def extract_attributes(payload):  # Example Input: 01067a65696e6562020102040101
    leader_attr_length = payload[2:4]
    i = int(leader_attr_length, 16)
    #print(i)
    j = 4 + 2 * i
    leader_ID_attr = payload[0:j]
    k = j + 6
    service_type_attr = payload[j:k]
    l = k + 6
    reward_attr = payload[k:l]
    # print([leader_ID_attr,service_type_attr,reward_attr])
    return [leader_ID_attr, service_type_attr, reward_attr]

#def service_code_to_name(service_code):
#    if service_code == "01":
#        name = "Virtual Reality"
#    else:
#        if service_code == "02":
#            name = "Smart Transportation"
#        else:
#            if service_code == "03":
#                name = "Smart Health"
#            else:
#                if service_code == "04":
#                    name == "Environmental Data Processing"

#    return name


def scan(interface='wlp3s0'):
    #    cmd = ["iw","dev", interface, "scan","-u","ssid","mf2c-leader" ]
    cmd = ["iw", "dev", interface, "scan", "-u", "passive"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Scan for mF2C beacons started...")
    points = proc.stdout.read().decode('utf-8')
    return points


def parse(content):
    scan_results = {}
    mf2cFound = False
    attr_dict = {"Leader ID(Trimmed)": "", "Service Type": "", "Reward": ""}
    lines = content.split('\n')
    for line in lines:

        line = line.strip()  # removes spaces
        #        print(line)
        BSS = BSSRe.search(line)

        if BSS is not None:
            # Example Of BSS.groupdict() : {'bss': ':27:eb:48:ac:94(on wlp3s0)'} OR {'bss': ':19:a9:a6:4d:60(on wlp3s0) -- associated'}
            BSSValue = BSS.groupdict()['bss']
            scan_results[BSSValue] = []
            continue

        result = ieRe.search(line)
        if result is not None:
            vsie = result.groupdict()
            # Example: {'vsie_data': '03 05', 'vsie_oui': '00:40:96'}
            scan_results[BSSValue].append(vsie)

            vsie_oui = vsie["vsie_oui"]
            if vsie_oui == mf2c_oui:
                mf2cFound = True
                mf2cPayload = vsie["vsie_data"]
                mf2cPayload = mf2cPayload.replace(" ", "")
                # Example: 01067a65696e6562
                # Payload after removing OUI & Length, 1st byte : type , 2nd byte: length of attribute , rest: attribute value
                attributes_list = extract_attributes(mf2cPayload)  # example: ['01067a65696e6562', '020102', '040101']
                for item in attributes_list:
                    type_value = mf2c_attr_decoder(item)
                    type = type_value[0]
                    value = type_value[1]
                    if type == "01":
                        attr_dict["Leader ID"] = value
                    else:
                        if type == "02":
                            attr_dict["Service Type"] = value
                        else:
                            if type == "04":
                                attr_dict["Reward"] = str(int(value, 16))

            continue

    if mf2cFound:
        message = "mF2C Beacon detected!!!"
        #       print (message,attr_dict)
    else:
        message = "No mF2C Beacons detected. Try again later."
    #        print (message)
    #    pp = pprint.PrettyPrinter(indent=2)
    #    pp.pprint(scan_results)
    return [message, attr_dict]


content = scan(interface='wlp3s0')
[message, attr_dict] = parse(content)
print(message)
if message == "mF2C Beacon detected!!!":
    x = PrettyTable(["#", "Leader ID(Trimmed)", "Service Type", "Reward"])
    x.add_row(["1", attr_dict["Leader ID"][:20], service_code_name_dict[attr_dict["Service Type"]], attr_dict["Reward"]+"€"])
    print(x)
