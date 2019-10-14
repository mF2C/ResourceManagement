#!/usr/bin/env python3
from flask import Flask, jsonify,abort,request
from Broadcaster import *
from Watcher import *
from Scanner import *
from JoinConfig import *
from InformationElementAttribute  import *
import os, sys, threading
import netifaces

app = Flask(__name__)

@app.route('/api/v1/resource-management/discovery/', methods=['GET'])
def get_discovery_api():
        
    return jsonify({'message': "Discovery API"})

@app.route('/api/v1/resource-management/discovery/broadcast/', methods=['POST'])
def start_broadcast():
    if not request.json or not 'broadcast_frequency' in request.json or not "interface_name" in request.json or not 'config_file' or not 'leader_id' in request.json:
        abort(400)
    beacon_interval = request.json['broadcast_frequency']
    interface_name = request.json['interface_name']
    config_file = request.json['config_file']
    leader_id = request.json['leader_id']
    interfaces = netifaces.interfaces()
    #check if the given interface really exists
    if interface_name not in interfaces:
        return jsonify({'message': interface_name+" does not exist!"})
    else:

        #check if the provided beacon interval is within the expected range
        if int(beacon_interval) not in range(15,65535):
            return jsonify({'message': "Beacon interval should be between 15 and 65535!"})
        else:
            is_running = Broadcaster.check_active()
            #check if the broadcaster is already running in order not to run it twice
            if not is_running:
                encoding_error = Broadcaster.fill_beacon_fields(beacon_interval, interface_name,config_file,leader_id)
                if not encoding_error:   
                    msg = Broadcaster.start_broadcast()
                    return jsonify({'message': msg})
                else:
                    return jsonify({'message': "Error filling beacon fields. Unexpected config value!"})
            else:
                return jsonify({'message': "Broadcaster already running!"})

@app.route('/api/v1/resource-management/discovery/broadcast/', methods=['PUT'])
def stop_broadcast():
    msg = Broadcaster.stop_broadcast()
    return jsonify({'message': msg})

@app.route('/api/v1/resource-management/discovery/watch/')
def start_watching():
    is_running = Broadcaster.check_active()
    if is_running:
        watching = Watcher.check_watching_running("hostapd_cli")
        if watching:
            return jsonify({'message': "Already watching!"})
        else:
            t = threading.Thread(target=Watcher.on_topology_changed)
            t.start()
            return jsonify({'message': "Started watching!"})
    else:
        return jsonify({'message': "Broadcaster not running! Cannot start watching!"})

@app.route('/api/v1/resource-management/discovery/watch/',methods=['PUT'])
def stop_watching():
    msg = Watcher.stop()
    return jsonify({'message': msg})


@app.route('/api/v1/resource-management/discovery/scan/<interface_name>', methods=['GET'])
def get_found_leaders_list(interface_name):
    interfaces = netifaces.interfaces()
    #check if the given interface exists
    if interface_name not in interfaces:
        return jsonify({'message': interface_name+" does not exist!"})
    else:

        found_leaders=[]
        s = Scanner()
        results = s.start_scan(interface_name)
        #if no error occurred, parse and decode scan results
        if not results[0]:
            found_leaders = s.parse_scan_results(results[2])
        if_to_mac = netifaces.ifaddresses(interface_name)[netifaces.AF_LINK][0]["addr"]
        return jsonify({'error_message': results[1], 'found_leaders':found_leaders,"used_mac":if_to_mac})

@app.route('/api/v1/resource-management/discovery/join/', methods=['POST'])
def join_leader():
    if not request.json or not 'interface' in request.json or not "bssid" in request.json:
        abort(400)
    bssid = request.json['bssid']
    interface = request.json['interface']
    JoinConfig.config(bssid)
    msg=JoinConfig.join(interface)
    
    return jsonify({'message': msg})

@app.route('/api/v1/resource-management/discovery/join/', methods=['PUT'])
def unjoin_leader():
    JoinConfig.unjoin()
    return jsonify({'message': "Disassociated from leader!"})

@app.route('/api/v1/resource-management/discovery/watch_agent_side/')
def start_watching_agent_side():
    param = request.args.get('key')
    if param == "start":
        t = threading.Thread(target=Watcher.on_leader_connection_changed)
        t.start()
        return jsonify({'message': "Started watching connection to leader!"})
    else:
        disconnected_value = Watcher.DISCONNECTED
        return jsonify({'DISCONNECTED': disconnected_value})
    
@app.route('/api/v1/resource-management/discovery/my_ip/', methods=['GET'])
def get_my_ip():
    ip = JoinConfig.get_ip()
    if ip:
        return jsonify({'IP_address': ip})
    else:
        return jsonify({'IP_address': ''})

@app.route('/api/v1/resource-management/discovery/dhcp/', methods=['POST'])
def start_dhcp():
    if not request.json or not "interface_name" in request.json:
        abort(400)
    
    interface_name = request.json['interface_name']
    
    interfaces = netifaces.interfaces()
    #check if the given interface really exists
    if interface_name not in interfaces:
        return jsonify({'message': interface_name+" does not exist!"})
    else:
        Broadcaster.fill_dhcp_config(interface_name)
        msg = Broadcaster.start_dhcp()
        return jsonify({'message': msg})
    
@app.route('/api/v1/resource-management/discovery/dhcp/', methods=['PUT'])
def stop_dhcp():
    msg = Broadcaster.stop_dhcp()
    return jsonify({'message': msg})

if __name__ == '__main__':
    
    app.run(debug=True,host='0.0.0.0',port=46040)
    


