#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE
    CIMI API calls
"""

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'

from common.common import CPARAMS
from common.logs import LOG

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)     # https://stackoverflow.com/a/28002687


class CIMIcalls:

    CIMI_URL = CPARAMS.CIMI_URL
    CIMI_HEADERS = CPARAMS.CIMI_HEADER

    CIMI_API_ENTRY = '/cloud-entry-point'
    CIMI_AGENT_RESOURCE = '/agent'
    CIMI_DEVICE_DYNAMIC = 'device-dynamic'
    CIMI_DEVICE = 'device'

    @staticmethod
    def checkCIMIstarted():
        """
        Check if CIMI is up.
        :return: True if CIMI is started, False otherwise.
        """
        URL = CIMIcalls.CIMI_URL + CIMIcalls.CIMI_API_ENTRY
        try:
            r = requests.get(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            LOG.debug('CIMI [{}] status_code {}, content {}'.format(URL, r.status_code,r.text))
            return True
        except Exception as ex:
            LOG.debug('CIMI [{}] failed. Exception: {}'.format(URL, ex))
            return False


    @staticmethod
    def getAgentResource():
        """
        Get Agent resource in CIMI
        :return: Dicc of the Agent Resource if found or empty dicc otherwise
        """
        URL = CIMIcalls.CIMI_URL + CIMIcalls.CIMI_AGENT_RESOURCE
        try:
            r = requests.get(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            rjson = r.json()
            LOG.debug('CIMI agent [{}] status_code {} count {}'.format(URL, r.status_code, rjson.get('count')))
            if len(rjson.get('agents')) > 0:
                LOG.debug('Agent resource found!')
                return rjson.get('agents')[0], rjson.get('agents')[0].get('id')
            else:
                LOG.debug('Agent resource not found!')
                return {}, ''
        except:
            LOG.exception('CIMI agent [{}] failed'.format(URL))
            return {}, ''

    @staticmethod
    def getAllAgentResources():
        URL = CIMIcalls.CIMI_URL + CIMIcalls.CIMI_AGENT_RESOURCE
        try:
            r = requests.get(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            rjson = r.json()
            LOG.debug('CIMI agent [{}] status_code {} count {}'.format(URL, r.status_code, rjson.get('count')))
            if len(rjson.get('agents')) > 0:
                LOG.debug('Agent resource found!')
                return rjson.get('agents')
            else:
                LOG.debug('Agent resource not found!')
                return []
        except:
            LOG.exception('CIMI agent [{}] failed'.format(URL))
            return []

    @staticmethod
    def createAgentResource(agentResource):
        """
        Create a new Agent Resource in CIMI
        :param agentResource: Agent resource dicc formated
        :return: Agent resource ID
        """
        URL = CIMIcalls.CIMI_URL + CIMIcalls.CIMI_AGENT_RESOURCE
        payload = agentResource
        try:
            r = requests.post(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False, json=payload)
            rjson = r.json()
            LOG.debug('CIMI create agent [{}] status_code {} resource-id {}'.format(URL, r.status_code, rjson.get('resource-id')))
            LOG.debug('CIMI reply: {}'.format(r.text))
            if r.status_code == 409:
                LOG.error('CIMI create agent already exists! resource-id {}'.format(rjson.get('resource-id')))
            elif r.status_code not in [200, 201]:
                LOG.error('CIMI create Agent error dettected! Payload Sent: {}'.format(payload))
            return str(rjson.get('resource-id'))
        except:
            LOG.exception('CIMI agent [{}] failed'.format(URL))
            return ''

    @staticmethod
    def get_topology():
        resource, CIMIid = CIMIcalls.getAgentResource()
        topology = []
        device_id = 0
        if 'childrenIPs' in resource:
            for childrenIP in resource['childrenIPs']:
                topology.append((str(device_id), str(childrenIP)))
        LOG.debug('{} devices found in childrenIPs Agent Resource.'.format(len(topology)))
        return topology

    @staticmethod
    def get_deviceID_from_IP(deviceIP):
        device_static_id = ''

        scode, dev_dyn_reply = CIMIcalls.get_resource(CIMIcalls.CIMI_DEVICE_DYNAMIC)
        if scode != 200:
            LOG.debug('Unable to query device-dynamic resource. IP cannot be found.')
            return ''

        try:
            if 'deviceDynamics' in dev_dyn_reply:
                device_dynamic_collection = dev_dyn_reply['deviceDynamics']
                for item in device_dynamic_collection:
                    if 'wifiAddress' in item and 'device' in item:
                        if item['wifiAddress'] == deviceIP:
                            device_static_id = item['device']['href']
                            LOG.debug('IP {} found! Device CIMI resource: {}'.format(deviceIP,device_static_id))
                            break
            else:
                LOG.error('deviceDynamics not found in {} resource'.format(CIMIcalls.CIMI_DEVICE_DYNAMIC))
                return ''

            if device_static_id != '':
                scode2, dev_sta_reply = CIMIcalls.get_resource(device_static_id)
                if scode2 != 200:
                    LOG.error('Unable to query device from device-dynamic. href:{}'.format(device_static_id))
                    return ''
                if 'deviceID' in dev_sta_reply:
                    LOG.debug('IP corresponds to deviceID: {}'.format(dev_sta_reply['deviceID']))
                    return dev_sta_reply['deviceID']
                else:
                    LOG.error('deviceID not found in resource {}'.format(device_static_id))
                    return ''
            else:
                LOG.debug('IP {} not found in {} collection.'.format(deviceIP, CIMIcalls.CIMI_DEVICE_DYNAMIC))
                return ''
        except:
            LOG.exception('Exception raised getting deviceID from IP')
            return ''


    # ### Common Methods ### #
    @staticmethod
    def get_resource(resource_id):
        """
        Get resource by ID if exists
        :param resource_id: CIMI resource id
        :return: status_code and resource if successful, None otherwise
        """
        URL = CIMIcalls.CIMI_URL + '/' + resource_id
        try:
            r = requests.get(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            rjson = r.json()
            LOG.debug('CIMI GET resource [{}] status_code {}'.format(URL, r.status_code))
            return r.status_code, rjson
        except:
            LOG.exception('CIMI GET resource [{}] failed.'.format(URL))
            return None, None

    @staticmethod
    def modify_resource(resource_id, payload):
        """
        Modify resource by ID in CIMI
        :param resource_id: CIMI resource id
        :param payload: new content of the resource
        :return: status_code if successful, None otherwise
        """
        URL = CIMIcalls.CIMI_URL + '/' + resource_id
        # URL = CIMIcalls.CIMI_URL + '/' + 'agent'
        try:
            r = requests.put(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False, json=payload)
            # rjson = r.json()
            LOG.debug('CIMI EDIT resource [{}] status_code {} content {} payload {}'.format(URL, r.status_code, r.content, payload))
            return r.status_code
        except:
            LOG.exception('CIMI EDIT resource [{}] failed.'.format(URL))
            return None

    @staticmethod
    def delete_resource(resource_id):
        """
        Delete resource by ID in CIMI
        :param resource_id: CIMI resource ID
        :return: status_code if successful, None otherwise
        """
        URL = CIMIcalls.CIMI_URL + '/' + resource_id
        try:
            r = requests.delete(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            # rjson = r.json()
            LOG.debug('CIMI DELETE resource [{}] status_code {}'.format(URL, r.status_code))
            return r.status_code
        except:
            LOG.exception('CIMI DELETE resource [{}] failed.'.format(URL))
            return None


class AgentResource:

    def __init__(self, deviceID, deviceIP, auth, conn, isLeader, leaderID=None, leaderIP=None, backupIP=None):
        self.deviceID = deviceID
        self.deviceIP = deviceIP
        self.authenticated = auth
        self.connected = conn
        self.isLeader = isLeader

        self.leaderID = leaderID
        self.leaderIP = leaderIP
        self.backupIP = backupIP
        self.childrenIPs = []

    def getCIMIdicc(self):
        p = {
            'device_id' : self.deviceID,
            'device_ip' : self.deviceIP,
            'authenticated' : self.authenticated,
            'connected' : self.connected,
            'isLeader' : self.isLeader
        }

        if self.leaderID is not None:
            p.update({'leader_id' : self.leaderID})
        if self.leaderIP is not None:
            p.update({'leader_ip' : self.leaderIP})
        if self.backupIP is not None:
            p.update({'backup_ip' : self.backupIP})

        return p