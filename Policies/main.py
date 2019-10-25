#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE


    Sub-Modules:
        - Agent Start [AS]
        - Leader Protection [LP]
            - Area Resilience [AR]
            - Leader Reelection [LR]

"""

from common.logs import LOG
from common.common import CPARAMS, URLS
from common.CIMI import CIMIcalls as CIMI
from logging import DEBUG, INFO

from leaderprotection.arearesilience import AreaResilience
from agentstart.agentstart import AgentStart
from leaderprotection.leaderreelection import LeaderReelection

from flask import Flask, request
from flask_restplus import Api, Resource, fields
from threading import Thread
from time import sleep, time
import requests
import subprocess

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__version__ = '2.0.11'
__author__ = 'Universitat Politècnica de Catalunya'

# ### Global Variables ### #
arearesilience = AreaResilience()
agentstart = AgentStart()
startup_time = time()

# ### main.py code ### #
# Set Logger
if CPARAMS.DEBUG_FLAG:
    LOG.setLevel(DEBUG)
else:
    LOG.setLevel(INFO)

LOG.info('Policies Module. Version {} Status {}'.format(__version__,__status__))

# Print env variables
LOG.debug('Environment Variables: {}'.format(CPARAMS.get_all()))


# Prepare Server
app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app, version=__version__, title='Policies Module API', description='Resource Manager - Agent Controller')

pl = api.namespace('api/v2/resource-management/policies', description='Policies Module Operations')
rm = api.namespace('rm', description='Resource Manager Operations')

reelection_model = api.model('Reelection_msg', {
    'deviceID': fields.String(required=True, description='The deviceID of the device that is promoted as new leader.')
})

keepalive_model = api.model('Keepalive Message', {
    'deviceID': fields.String(required=True, description='The deviceID of the device that is sending the message.'),
    'deviceIP': fields.String(required=False, description='The IP of the device that is dettected by the Leader Discovery module.')
})

keepalive_reply_model = api.model('Keepalive Reply Message', {
    'deviceID': fields.String(required=True, description='The deviceID of the device that is replying the message.'),
    'backupPriority': fields.Integer(required=True, description='Order of the backup in the area.')
})

leader_info_model = api.model('Leader Info Message', {
    'imLeader': fields.Boolean(required=True, description='If the actual role is Leader'),
    'imBackup': fields.Boolean(required=True, description='If the actual role is Backup'),  # TODO: Check with Roman.
    'imCloud' : fields.Boolean(required=True, description='If the actual role is Cloud Agent')
})

components_info_model = api.model('Resource Manager Components Information', {
    "started": fields.Boolean(description='The agent is started'),
    "running": fields.Boolean(description='The agent is currently running'),
    "modules": fields.List(fields.String, description='List of modules that are triggered on starting'),
    "discovery": fields.Boolean(description='Discovery module is started'),
    "identification": fields.Boolean(description='Identification module is started'),
    "cau_client": fields.Boolean(description='CAUClient module is started'),
    "categorization": fields.Boolean(description='Categorization module is started'),
    "policies": fields.Boolean(description='Policies module is started'),
    "discovery_description": fields.String(description='Discovery module description / parameters received'),
    "identification_description": fields.String(description='Identification module description / parameters received'),
    "categorization_description": fields.String(description='Categorization module description / parameters received'),
    "policies_description": fields.String(description='Policies module description / parameters received'),
    "cau_client_description": fields.String(description='CAUClient module description / parameters received')
})

health_model = api.model('Policies Healthcheck', {
    "health": fields.Boolean(description='True if the component is considered to work properly (GREEN and YELLOW status).'),
    "startup": fields.Boolean(description="True if the module has finished the agent startup flow."),
    "startup_time": fields.Float(description="Time considered as startup (ORANGE status when failure)"),
    "status": fields.String(description="Status code of the component. GREEN: all OK, YELLOW: failure detected but working, ORANGE: Failed but starting, RED: critical failure."),
    "API": fields.Boolean(description="True if API working"),
    "discovery": fields.Boolean(description="True if Discovery not failed on trigger"),
    "identification": fields.Boolean(description="True if Identification not failed on trigger"),
    "cau-client": fields.Boolean(description="True if CAU-client not failed on trigger"),
    "res-cat": fields.Boolean(description="True if Res. Categorization not failed on trigger"),
    "area-resilience": fields.Boolean(description="True if sub-module Area Resilience started"),
    "vpn-client": fields.Boolean(description="True if VPN is stablished and got IP"),
    "deviceIP": fields.Boolean(description="True if deviceIP not empty"),
    "leaderIP": fields.Boolean(description="True if leaderIP not empty or isCloud = True"),
    "cloudIP": fields.Boolean(description="True if cloudIP not empty"),
    "deviceID": fields.Boolean(description="True if deviceID not empty"),
    "backupElected": fields.Boolean(description="True if (activeBackups > 0 and isLeader=True) or isCloud=True"),
    "leaderfound": fields.Boolean(description="True if leader found by discovery or (isCloud = True || isLeader = True)"),
    "JOIN-MYIP": fields.Boolean(description="True if joined and IP from discovery obtained or (isCloud = True || isLeader = True)"),
    "wifi-iface": fields.Boolean(description="True if wifi iface not empty or (isCloud = True)")
})


# API Endpoints
# #### Resource Manager #### #
@rm.route('/components')
class ResourceManagerStatus(Resource):
    """Resource Manager components status"""
    @rm.doc('get_components')
    @rm.marshal_with(components_info_model)
    @rm.response(200, 'Components Information')
    def get(self):
        """Get resource manager module start status"""
        payload = {
            'started': agentstart.isStarted,
            'running': agentstart._connected,  # TODO: Private variable exposed here (soft)
            'modules': ['discovery', 'identification', 'cau_client', 'categorization', 'policies'],
            'discovery': not agentstart.discovery_failed if agentstart.discovery_failed is not None else False,
            'identification': not agentstart.identification_failed if agentstart.identification_failed is not None else False,
            'cau_client': not agentstart.cauclient_failed if agentstart.cauclient_failed is not None else False,
            'categorization': not agentstart.categorization_failed if agentstart.categorization_failed is not None else False,
            'policies': not agentstart.policies_failed if agentstart.policies_failed is not None else False
        }
        payload.update({'discovery_description': 'detectedLeaderID: \"{}\", MACaddr: \"{}\"'.format(
            agentstart.detectedLeaderID, agentstart.MACaddr) if payload.get(
            'discovery') else 'Discovery not started or error on trigger.'})
        payload.update({'identification_description': 'IDKey: \"{}\", deviceID: \"{}\"'.format(agentstart.IDkey,
                                                                                               agentstart.deviceID) if payload.get(
            'identification') else 'Identification not started or error on trigger.'})
        payload.update(
            {'categorization_description': 'Started: {}'.format(agentstart.categorization_started) if payload.get(
                'categorization') else 'RCategorization not started or error on trigger.'})
        payload.update({'policies_description': 'LPP: {}'.format(agentstart.arearesilience_started) if payload.get(
            'policies') else 'Policies (LPP) not started or error on trigger.'})
        payload.update(
            {'cau_client_description': 'authenticated: {}, secureConnection: {}'.format(agentstart.isAuthenticated,
                                                                                        agentstart.secureConnection) if payload.get(
                'cau_client') else 'CAU_client not started or error on trigger.'})
        return payload, 200


# Healthcheck
@pl.route('/{}'.format(URLS.END_POLICIES_HEALTHCHECK))
class policiesHealthcheck(Resource):
    """Policies Healthcheck"""
    @pl.doc('get-healthcheck')
    @pl.marshal_with(health_model, code=200)
    @pl.response(200, description="Health OK GREEN or YELLOW")
    @pl.response(400, description="Health NOK ORANGE or RED")
    def get(self):
        """Policies Healthcheck"""
        payload = {
            'health': False,        # Needs change
            'startup': agentstart.isCompleted,
            'startup_time': CPARAMS.STARTUP_TIME_HEALTH,
            'status': 'BLACK',      # Needs change
            'API': True,
            'discovery': not agentstart.discovery_failed if agentstart.discovery_failed is not None else False,
            'identification': not agentstart.identification_failed if agentstart.identification_failed is not None else False,
            'cau-client': not agentstart.cauclient_failed if agentstart.cauclient_failed is not None else False,
            'res-cat': not agentstart.categorization_failed if agentstart.categorization_failed is not None else False,
            'area-resilience': not agentstart.policies_failed if agentstart.policies_failed is not None else False,
            'vpn-client': True if agentstart.vpnIP is not None and agentstart.vpnIP != '' else False,
            'deviceIP': True if agentstart.deviceIP is not None and agentstart.deviceIP != '' else False,
            'leaderIP': True if (agentstart.leaderIP is not None and agentstart.leaderIP != '') or CPARAMS.CLOUD_FLAG else False,
            'cloudIP': True if (agentstart.cloudIP is not None and agentstart.cloudIP != '') or CPARAMS.CLOUD_FLAG else False,
            'deviceID': True if agentstart.deviceID is not None and agentstart.deviceID != '' else False,
            'backupElected': True if arearesilience.getAmountActiveBackups() > 0 or not agentstart.imLeader or agentstart.imCloud else False,
            'leaderfound': True if (agentstart.bssid is not None and agentstart.bssid != '') or agentstart.imLeader or agentstart.imCloud else False,
            'JOIN-MYIP': True if (agentstart.discovery_joined is not None and agentstart.discovery_joined) or agentstart.imCloud or agentstart.imLeader else False,
            'wifi-iface': True if CPARAMS.WIFI_DEV_FLAG != '' or CPARAMS.CLOUD_FLAG else False
        }
        components = payload['identification'] and payload['discovery'] and payload['cau-client'] and payload['res-cat'] and payload['area-resilience'] and payload['vpn-client']
        components_no_discovery = payload['identification'] and payload['cau-client'] and payload['res-cat'] and payload['area-resilience'] and payload['vpn-client']
        ips = payload['deviceIP'] and payload['leaderIP'] and payload['cloudIP']
        discovery_fail_ip_ok = not payload['discovery'] and payload['deviceIP'] and payload['leaderIP']
        discovery_ok_leader_notfound_vpn_ok = payload['discovery'] and not payload['leaderfound'] and payload['vpn-client'] and payload['deviceIP'] and payload['leaderIP']

        # GREEN STATUS EVALUATION
        if not components_no_discovery or not ips or not payload['deviceID']:
            if time() - startup_time < payload['startup_time']:
                payload['status'] = 'ORANGE'
            else:
                payload['status'] = 'RED'
            payload['health'] = False
        elif discovery_fail_ip_ok or discovery_ok_leader_notfound_vpn_ok or not payload['backupElected'] or not payload['startup']:
            if time() - startup_time < payload['startup_time']:
                payload['status'] = 'ORANGE'
                payload['health'] = False
            else:
                payload['status'] = 'YELLOW'
                payload['health'] = True
        elif components and ips and payload['backupElected'] and payload['deviceID'] and payload['startup']:
            payload['status'] = 'GREEN'
            payload['health'] = True
        else:
            payload['status'] = 'YELLOW'
            payload['health'] = True
        LOG.info('Policies Health={} Status={} Started={} Components={} IPs={} ID={}'.format(payload['health'],payload['status'],payload['startup'],components, ips, payload['deviceID']))
        status_code = 200 if payload['health'] else 400
        return payload, status_code


# #### Policies Module #### #
@pl.route(URLS.END_START_FLOW)      # Start Agent
class startAgent(Resource):
    """Start Agent"""
    @pl.doc('get_startAgent')
    @pl.response(200, 'Started')
    @pl.response(403, 'Already Started')
    def get(self):
        """Start Agent"""
        started = agentstart.start(CPARAMS.LEADER_FLAG, CPARAMS.CLOUD_FLAG)
        if started:
            return {'started': started}, 200
        else:
            return {'started': True}, 403


@pl.route(URLS.END_POLICIES)        # Area Resilience
class startAR(Resource):
    """Start Area Resilience"""
    @pl.doc('get_startAR')
    @pl.response(200, 'Started')
    @pl.response(403, 'Already Started')
    def get(self):
        """Start Agent Resilience"""
        started = arearesilience.start(agentstart.deviceID, agentstart.deviceIP)
        if started:
            return {'started': started}, 200
        else:
            return {'started': True}, 403


# noinspection PyUnresolvedReferences
@pl.route('/roleChange/<string:role>')      # TODO: Parametrized Endpoint
@pl.param('role', 'The requested role to change.')
class role_change(Resource):
    """Promotion/Demotion of the agent role."""
    @pl.doc('get_change')
    @pl.response(200, 'Successful')
    @pl.response(403, 'Not Successful')
    @pl.response(404, 'Role not found')
    def get(self, role):
        global arearesilience
        """Promotion/Demotion of the agent role."""
        imLeader = arearesilience.imLeader()
        imBackup = arearesilience.imBackup()
        if role.lower() == 'leader':
            # Do you want to be a leader?
            if imLeader:
                # If a leader is promoted to leader, it becomes a super-leader?
                LOG.debug('Role change: Leader -> Leader')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403
            elif imBackup:
                # Hi, I'm backup-kun - It's my time to shine!!
                LOG.debug('Role change: Backup -> Leader')
                ret = agentstart.switch(imLeader=True)
                if ret:
                    LOG.info('Successful promotion to Leader')
                else:
                    LOG.warning('Unsuccessful promotion from Backup to Leader')
                return {'imLeader': True, 'imBackup': False}, 200
            else:
                # Nor leader, nor Backup, just a normal agent
                # For reelection, first you must be a backup!
                LOG.debug('Role change: Agent -> Leader')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403

        elif role.lower() == 'backup':
            # Always have a B plan
            if imLeader:
                # Why in the hell a Leader'll become a backup?
                LOG.debug('Role change: Leader -> Backup')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403
            elif imBackup:
                # Emm... no pls.
                LOG.debug('Role change: Backup -> Backup')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403
            else:
                # Can you watch my shoulder?
                LOG.debug('Role change: Agent -> Backup')
                leaderIP = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                LOG.debug('Leader at {} is selecting me as Backup'.format(leaderIP))
                ret = arearesilience.promotedToBackup(leaderIP=agentstart.leaderIP)    # TODO: get leaderIP from CIMI
                if ret:
                    LOG.info('Successful promotion to Backup')
                    return {'imLeader': imLeader, 'imBackup': True}, 200
                else:
                    LOG.warning('Unsuccessful promotion from Agent to Backup')
                    return {'imLeader': arearesilience.imLeader(), 'imBackup': arearesilience.imBackup()}, 403

        elif role.lower() == 'agent':
            # Bigger will be the fall....
            if imLeader:
                # You are shuch an incompetent, you're FIRED!
                # Leader demotion
                LOG.debug('Role change: Leader -> Agent')
                arearesilience.stop()
                agentstart.switch(imLeader=False)
                CPARAMS.LEADER_FLAG = False
                arearesilience = AreaResilience(cimi)
                arearesilience.start(agentstart.deviceID)
                return {'imLeader': False, 'imBackup': False}, 200
            elif imBackup:
                # Maybe we are gona call you latter.... or not
                # Backup demotion
                LOG.debug('Role change: Backup -> Agent')
                arearesilience.stop()
                arearesilience = AreaResilience(cimi)
                arearesilience.start(agentstart.deviceID)
                return {'imLeader': False, 'imBackup': False}, 200
            else:
                # You're so tiny that I don't even care.
                LOG.debug('Role change: Agent -> Agent')
                return {'imLeader': False, 'imBackup': False}, 403

        else:
            # keikaku doori... Weird syntax maybe?
            return {'imLeader': imLeader, 'imBackup': imBackup}, 404


@pl.route('/reelection')
class reelection(Resource):
    """Reelection of the Leader"""
    @pl.doc('post_reelection')
    @pl.expect(reelection_model)
    # @pl.marshal_with(reelection_model, code=200)  # Only for return if we want to follow the same schema
    @pl.response(200, 'Reelection Successful')
    @pl.response(401, 'The Agent is not authorized to trigger the reelection')
    @pl.response(403, 'Reelection failed')
    @pl.response(404, 'Device not found or IP not available')
    def post(self):
        """Reelection of the Leader"""
        found = False
        deviceIP = ''
        deviceID = api.payload['deviceID']
        for device in cimi('topology', default=[]):     # TODO: use real topology
            if device.get('deviceID') == deviceID:
                found = True
                deviceIP = device.get('deviceIP')
                break

        if not found:
            LOG.error('Device {} not found in the topology'.format(deviceID))
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 404
        if not arearesilience.imLeader():
            LOG.error('Device is not a Leader, cannot perform a reelection in a non-leader device.')
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 401

        correct = LeaderReelection.reelection(arearesilience, deviceID, deviceIP)
        if correct:
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 200
        else:
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 403


@pl.route('/keepalive')
class keepalive(Resource):
    """Keepalive entrypoint"""
    @pl.doc('post_keepalive')
    @pl.expect(keepalive_model)
    @pl.marshal_with(keepalive_reply_model, code=200)
    @pl.response(200, 'Leader alive')
    @pl.response(403, 'Agent not authorized (Not recognized as backup)')
    @pl.response(405, 'Device is not a Leader')
    def post(self):
        """Keepalive entrypoint for Leader"""
        if not arearesilience.imLeader():
            # It's not like I don't want you to send me messages or anything, b-baka!
            return {'deviceID': agentstart.deviceID, 'backupPriority': arearesilience.PRIORITY_ON_FAILURE}, 405

        deviceIP = '' if 'deviceIP' not in api.payload else api.payload['deviceIP']
        correct, priority = arearesilience.receive_keepalive(api.payload['deviceID'], deviceIP)
        LOG.debug('Device {} has sent a keepalive. Result correct: {}, Priority: {}, deviceIP: {}'.format(api.payload['deviceID'],correct,priority,deviceIP))
        if correct:
            # Authorized
            return {'deviceID': agentstart.deviceID, 'backupPriority': priority}, 200
        else:
            # Not Authorized
            return {'deviceID': agentstart.deviceID, 'backupPriority': priority}, 403


@pl.route('/leaderinfo')
class leaderInfo(Resource):     # TODO: Provisional, remove when possible
    """Leader and Backup information"""
    @pl.doc('get_leaderinfo')
    @pl.marshal_with(leader_info_model, code=200)
    @pl.response(200, 'Leader and Backup Information')
    def get(self):
        """Leader and Backup information"""
        return {
            'imLeader': arearesilience.imLeader(),
            'imBackup': arearesilience.imBackup(),
            'imCloud' : agentstart.imCloud
        }, 200


# And da Main Program
def cimi(key, default=None):
    value = default
    if key == 'leader':
        value = CPARAMS.LEADER_FLAG
    elif key == 'topology':
        value = []
        # 1. Try to get the real topology
        cimi_topology = CIMI.get_topology()
        if len(cimi_topology) > 0:
            used_topology = cimi_topology
            # used_topology = list()
            # for item in cimi_topology:        # TODO: Dataclay doesnt sync device static information to the leader
            #     qdeviceID = CIMI.get_deviceID_from_IP(item[1])
            #     if qdeviceID != '':
            #         used_topology.append((qdeviceID, item[1]))
        else:
            used_topology = CPARAMS.TOPOLOGY_FLAG

        try:
            for item in used_topology:
                i = {
                    'deviceID': item[0],
                    'deviceIP': item[1]
                }
                value.append(i)
        except:
            LOG.exception('Topology Environment variable format is not correct.')
            value = []

    return value


def initialization():
    global arearesilience, agentstart
    # 0. Waitting time
    LOG.info('INIT: Wait {:.2f}s to start'.format(CPARAMS.TIME_WAIT_INIT))
    sleep(CPARAMS.TIME_WAIT_INIT)
    LOG.debug('INIT: Wake Me up Before You Go-Go ♫')

    # 1. Area Resilience Module Creation
    LOG.debug('Area Resilience submodule creation')
    arearesilience = AreaResilience(cimi)
    LOG.debug('Area Resilience created')

    # 2. Leader Reelection Module Creation (None)

    # 3.1 Discovery IP adquisition
    result = subprocess.run(['/bin/ip', 'route'], stdout=subprocess.PIPE)
    route_ip = bytes(result.stdout).decode()
    route_ip_l = route_ip.split('\n')
    server_ip = ''
    if len(route_ip_l) > 0:
        for line in route_ip_l:
            if 'default' in line:
                server_ip = line.split(' ')[2]
                break
    if server_ip == '':
        LOG.error('Discovery IP cannot be received. Stopping.')
        exit(4)

    # 3. Agent Start Module Creation
    LOG.debug('Agent Start submodule creation')
    if CPARAMS.MF2C_FLAG:
        agentstart = AgentStart(addr_pol=('127.0.0.1', '46050'),
                                addr_dis=('{}'.format(server_ip), '46040'),
                                addr_cat=('resource-categorization', '46070'),
                                addr_id=('identification', '46060'))
    else:
        agentstart = AgentStart(addr_pol=('127.0.0.1', '46050'))
    agentstart.deviceID = CPARAMS.DEVICEID_FLAG     # TODO: remove this
    if CPARAMS.LEADER_IP_FLAG is not None and len(CPARAMS.LEADER_IP_FLAG) != 0:
        agentstart.leaderIP = CPARAMS.LEADER_IP_FLAG
    LOG.debug('Agent Start created')

    return


def main():
    LOG.info('API documentation page at: http://{}:{}/'.format('localhost', CPARAMS.POLICIES_PORT))
    app.run(debug=False, host='0.0.0.0', port=CPARAMS.POLICIES_PORT)


def debug():
    sleep(10)
    LOG.info('Device registration procedure...')
    attempt = 0
    successful = False
    while attempt < CPARAMS.REGISTRATION_MAX_RETRY and not successful:
        try:
            r = requests.post(URLS.build_url_address(URLS.URL_IDENTIFICATION_START, portaddr=('identification', '46060')))
            rjson = r.json()
            LOG.debug('Identification request result: {}'.format(rjson))
            if rjson['status'] == '412' and CPARAMS.CLOUD_FLAG:
                # We need to wait until user and password is registered
                LOG.warning('Cloud user not registered yet... Retry in 10s.')
            elif rjson['status'] in ('200', '201'):
                LOG.info('Successful registration of the device.')
                successful = True
            elif CPARAMS.DEBUG_FLAG:
                LOG.warning('Status code received different from 200 or 201. Debug mode skips this failure.')
                successful = True
            else:
                LOG.warning('Error on registration trigger. Retry in 10s...')
                successful = False
        except ValueError:
            LOG.debug('ValueError raised on Identification: {}'.format(r.text))
        except:
            LOG.warning('Early start of Identification not successful.')
        finally:
            if not successful:
                sleep(10)
            attempt += 1
        if not CPARAMS.DEBUG_FLAG and not successful:
            LOG.critical('Critical Error: Registration of the device not successful. Stopping module')
            exit(4)
    sleep(5)

    LOG.info('Starting Agent Flow...')
    r = requests.get(URLS.build_url_address(URLS.URL_START_FLOW, portaddr=('127.0.0.1', CPARAMS.POLICIES_PORT)))
    # r = requests.get(URLS.build_url_address(URLS.URL_POLICIES, portaddr=('127.0.0.1', CPARAMS.POLICIES_PORT)))
    LOG.debug('Agent Flow request result: {}'.format(r.json()))
    LOG.debug('Stopping thread activity.')
    return


if __name__ == '__main__':
    initialization()
    if CPARAMS.DEBUG_FLAG or CPARAMS.MF2C_FLAG:
        t = Thread(target=debug, name='debug_init', daemon=True)
        t.start()
    main()
    exit(0)
