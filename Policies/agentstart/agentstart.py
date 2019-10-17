#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE
    Agent Start - Start an Agent 101

    # TODO: LOG integration in triggers
    # TODO: Reelection Integration
"""

import threading
import requests
import socket
from time import sleep

from common.logs import LOG
from common.common import CPARAMS, URLS
from common.CIMI import CIMIcalls as CIMI, AgentResource
from common.vpn import VPN_mF2C as VPN

from requests.exceptions import ConnectTimeout as timeout
from requests.exceptions import ReadTimeout as timeout2

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class AgentStart:
    TAG = '\033[36m' + '[FCJP]: ' + '\033[0m'
    ETAG = '\033[31m' + '[FCJP] ERROR: ' + '\033[0m'
    MAX_MISSING_SCANS = 10      # TODO: ENV Policies Param
    MAX_VPN_FAILURES = 20
    WAIT_TIME_CIMI = 2.
    WAIT_TIME_VPN = 5.
    ALE_ENABLED = False

    def __init__(self, addr_dis=None, addr_id=None, addr_cat=None, addr_pol=None, addr_CAUcl=None, addr_dcly=None):
        self._connected = False
        self.isStarted = False
        self.isSwitched = False
        self.imLeader = False
        self.imCloud = False
        self.th_proc = threading.Thread()
        self._cimi_agent_resource_id = None
        self._cimi_agent_resource = None

        self.MACaddr = None
        self.detectedLeaderID = None
        self.bssid = None
        self.deviceID = None
        self.IDkey = None
        self.isAuthenticated = None
        self.secureConnection = None
        self.deviceIP = None
        self.leaderIP = None
        self.vpnIP = None
        self.cloudIP = CPARAMS.CLOUD_AGENT_IP       # Default: None

        self.categorization_started = None
        self.arearesilience_started = None
        self.categorization_switched = None
        self.discovery_switched = None
        self.dataclay_started = None

        self.discovery_failed = None
        self.discovery_leader_failed = None
        self.categorization_failed = None
        self.categorization_leader_failed = None
        self.identification_failed = None
        self.cauclient_failed = None
        self.policies_failed = None

        self.URL_DISCOVERY = URLS.build_url_address(URLS.URL_DISCOVERY, portaddr=addr_dis)
        if CPARAMS.WIFI_DEV_FLAG != '':
            self.URL_DISCOVERY += '{}'.format(CPARAMS.WIFI_DEV_FLAG)
        # self.URL_DISCOVERY_MAC = urls.build_url_address(urls.URL_DISCOVERY_MAC, portaddr=addr_dis)
        self.URL_DISCOVERY_JOIN = URLS.build_url_address(URLS.URL_DISCOVERY_JOIN, portaddr=addr_dis)
        self.URL_DISCOVERY_DHCP = URLS.build_url_address(URLS.URL_DISCOVERY_DHCP, portaddr=addr_dis)
        self.URL_DISCOVERY_MYIP = URLS.build_url_address(URLS.URL_DISCOVERY_MYIP, portaddr=addr_dis)
        self.URL_DISCOVERY_SWITCH_LEADER = URLS.build_url_address(URLS.URL_DISCOVERY_SWITCH_LEADER, portaddr=addr_dis)
        self.URL_IDENTIFICATION = URLS.build_url_address(URLS.URL_IDENTIFICATION, portaddr=addr_id)
        self.URL_CATEGORIZATION_SWITCH_LEADER = URLS.build_url_address(URLS.URL_CATEGORIZATION_SWITCH_LEADER,
                                                                       portaddr=addr_cat)
        self.URL_CATEGORIZATION = URLS.build_url_address(URLS.URL_CATEGORIZATION, portaddr=addr_cat)
        self.URL_CAU_CLIENT = URLS.build_url_address(URLS.URL_CAU_CLIENT, portaddr=addr_CAUcl)
        self.URL_POLICIES = URLS.build_url_address(URLS.URL_POLICIES, portaddr=addr_pol)
        self.URL_DISCOVERY_WATCH = URLS.build_url_address(URLS.URL_DISCOVERY_WATCH, portaddr=addr_dis)

    def start(self, imLeader, imCloud):
        if self.isStarted:
            print(self.TAG, 'Procedure is already started...')
            return False
        else:
            self.imLeader = imLeader
            self.imCloud = imCloud
            self._connected = True
            self.th_proc = threading.Thread(name='th_fcjp', target=self.__agent_startup_flow, daemon=True)
            self.th_proc.start()
            self.isStarted = True
            return True

    def switch(self, imLeader):
        if not self.isStarted:
            LOG.error('Agent is not started!')
            return False

        if self.th_proc.is_alive():
            LOG.debug(self.TAG + 'Stopping thread {} to switch...'.format(self.th_proc.name))
            self._connected = False
            self.th_proc.join()
        LOG.debug('Thread successfully stopped.')
        self._connected = True

        if self.imLeader != imLeader:
            LOG.warning('imLeader state is not consequent!')    # TODO: Action required

        if self.imLeader:
            # Switch to Agent
            LOG.info(self.TAG + 'Switch to Agent')
            self.imLeader = False
            self.th_proc = threading.Thread(name='fcjp_agent', target=self.__agent_switch_flow, daemon=True)
        else:
            # Switch to Leader
            LOG.info(self.TAG + 'Switch to Leader')
            # TODO: Create a thread if we don't want blocking feature (AR wait until leader is set - slow)
            self.imLeader = True
            self.th_proc = threading.Thread(name='fcjp_leader', target=self.__leader_switch_flow, daemon=True)
        self.th_proc.start()
        return True

    def stop(self):     # TODO: Clean stop
        self._connected = False

    def __agent_startup_flow(self):
        while self._connected:
            # 0. Init
            self.detectedLeaderID, self.MACaddr = None, None

            # 0.1 Check CIMI is UP
            CIMIon = False
            while self._connected and not CIMIon:
                CIMIon = CIMI.checkCIMIstarted()
                if not CIMIon:
                    LOG.debug(self.TAG + 'CIMI is not ready... Retry in {}s'.format(self.WAIT_TIME_CIMI))
                    sleep(self.WAIT_TIME_CIMI)
            LOG.info(self.TAG + 'CIMI is ready!')

            # 1. Identification
            if self._connected:
                self.identification_failed = True   # Reset variable to avoid false positives
                LOG.debug(self.TAG + 'Sending trigger to Identification...')
                try:
                    self.__trigger_requestID()
                    self.identification_failed = False
                except Exception:
                    LOG.exception(self.TAG + 'Identification trigger failed!')
                    self.identification_failed = True
                LOG.info(self.TAG + 'Identification Trigger Done.')
            else:
                return
            if not CPARAMS.DEBUG_FLAG and self.identification_failed:
                LOG.critical(self.TAG + 'Identification failed, interrupting agent start.')
                return

            # 2.1. Check if im Cloud Agent
            if self.imCloud:
                # start cloud flow
                self.__cloud_flow()
                return

            # 2.2. Check if im a Leader - PLE
            if self.imLeader:
                # switch to leader
                self.__leader_switch_flow()
                return

            # remain as agent
            # 3. Scan for Leaders
            count = 0
            self.discovery_failed = True
            while self._connected and count < self.MAX_MISSING_SCANS and self.detectedLeaderID is None and self.MACaddr is None:    # TODO: new protocol required
                LOG.debug(self.TAG + 'Sending SCAN trigger to Discovery...')
                try:
                    self.__trigger_startScan()
                    self.discovery_failed = False
                except Exception:
                    LOG.debug(self.TAG + 'Discovery failed on attepmt {}.'.format(count))
                    self.discovery_failed = True

                if self.detectedLeaderID is not None and self.MACaddr is not None and self.bssid is not None:
                    LOG.info(self.TAG + 'Discovery Scan Trigger Done.')
                count += 1
            LOG.info(self.TAG + 'Discovery trigger finished in #{} attempts and ok={}'.format(count,
                                                                                          self.detectedLeaderID is not None and self.MACaddr is not None and self.bssid is not None))
            if not self._connected:
                return
            if not CPARAMS.DEBUG_FLAG and self.discovery_failed:
                LOG.critical(self.TAG + 'Discovery failed, interrupting agent start.')
                return

            # 4.1. If no leader detected, switch to leader IF policy and capable - ALE
            if not self.discovery_failed and self.detectedLeaderID is None and self.MACaddr is None and self.bssid is None and self.ALE_ENABLED:
                self.__leader_switch_flow()     # TODO: imCapable?
                return

            # 4.2 If detected, join to the Leader
            if not self.discovery_failed and self.bssid is not None and self._connected:
                LOG.debug(self.TAG + 'Sending JOIN trigger to discovery...')
                try:
                    r = self.__trigger_joinDiscovery()
                    self.discovery_failed = not r
                    if not self.discovery_failed:
                        self.leaderIP = CPARAMS.LEADER_DISCOVERY_IP
                except Exception:
                    LOG.exception(self.TAG + 'Discovery JOIN trigger failed.')
                    self.discovery_failed = True
                LOG.debug(self.TAG + 'Discovery JOIN trigger Done.')

            # 4.3 If not detected or failed, static configuration if setup
            if self.discovery_failed or (self.detectedLeaderID is None and self.MACaddr is None and self.bssid is None):
                LOG.debug(self.TAG + 'Discovery failed or leader was not detected. Fetching deviceIP and leaderIP from env variables.')
                self.deviceIP = CPARAMS.DEVICE_IP_FLAG
                self.leaderIP = CPARAMS.LEADER_IP_FLAG

            # 5. CAU client
            if self._connected:
                self.cauclient_failed = True
                LOG.debug(self.TAG + 'Sending trigger to CAU client...')
                try:
                    r = self.__trigger_triggerCAUclient()
                    self.cauclient_failed = not r
                except Exception:
                    LOG.exception(self.TAG + 'CAUclient failed.')
                    self.cauclient_failed = True
                LOG.info(self.TAG + 'CAU client Trigger Done.')
            else:
                return
            if not CPARAMS.DEBUG_FLAG and self.cauclient_failed:
                LOG.critical(self.TAG + 'CAU-Client failed, interrupting agent start.')
                return

            # 5.1. VPN get IP
            attempt = 0
            while self._connected and self.vpnIP is None and attempt < self.MAX_VPN_FAILURES:
                vpn_ip = VPN.getIPfromFile()
                self.vpnIP = vpn_ip if vpn_ip != '' else None
                if self.vpnIP is None:
                    LOG.debug(self.TAG + 'VPN IP cannot be obtained... Retry in {}s'.format(self.WAIT_TIME_VPN))
                    sleep(self.WAIT_TIME_VPN)
                    attempt += 1
            if self.vpnIP is None:
                LOG.warning(self.TAG + 'VPN IP cannot be obtained.')
                if not CPARAMS.DEBUG_FLAG:
                    LOG.critical(self.TAG + 'Policies module cannot continue its activity without VPN IP')
                    exit(4)
            else:
                LOG.info(self.TAG + 'VPN IP: [{}]'.format(self.vpnIP))

            # 5.2 If not static configuration and no leader detected, VPN configuration
            if self.deviceIP is None and self.leaderIP is None:
                LOG.debug(
                    self.TAG + 'Static configuration for deviceIP and leaderIP not found. Using VPN values')
                self.deviceIP = self.vpnIP
                self.leaderIP = self.cloudIP

            LOG.info(self.TAG + 'deviceIP={}, leaderIP={}'.format(self.deviceIP, self.leaderIP))

            # 6. Categorization
            if self._connected and not self.categorization_started:
                self.categorization_failed = True
                LOG.debug(self.TAG + 'Sending start trigger to Categorization...')
                try:
                    self.__trigger_startCategorization()
                    self.categorization_failed = False
                    self.categorization_started = True
                except Exception:
                    LOG.exception(self.TAG + 'Categorization failed')
                    self.categorization_failed = True
                LOG.info(self.TAG + 'Categorization Start Trigger Done.')
            elif not self._connected:
                return
            if not CPARAMS.DEBUG_FLAG and self.categorization_failed:
                LOG.critical(self.TAG + 'Categorization failed, interrupting agent start.')
                return

            # 7. Area Resilience
            if self._connected and not self.arearesilience_started:
                self.policies_failed = True
                LOG.debug(self.TAG + 'Sending start trigger to Policies...')
                try:
                    success = self.__trigger_startLeaderProtectionPolicies()
                    self.policies_failed = not success
                    self.arearesilience_started = success
                except Exception:
                    LOG.exception(self.TAG + 'Policies Area Resilience failed!')
                LOG.info(self.TAG + 'Policies Area Resilience Start Trigger Done.')
            elif not self._connected:
                return
            if not CPARAMS.DEBUG_FLAG and self.policies_failed:
                LOG.critical(self.TAG + 'Policies Area Resilience failed, interrupting agent start.')
                return

            # Print summary
            self.__print_summary()

            # Create/Modify Agent Resource
            self.deviceIP = '' if self.deviceIP is None else self.deviceIP
            self._cimi_agent_resource = AgentResource(self.deviceID, self.deviceIP, self.isAuthenticated,
                                                      self.secureConnection, self.imLeader)
            LOG.debug(self.TAG + 'CIMI Agent Resource payload: {}'.format(self._cimi_agent_resource.getCIMIdicc()))
            if self._cimi_agent_resource_id is None:
                # Create agent resource
                self._cimi_agent_resource_id = CIMI.createAgentResource(self._cimi_agent_resource.getCIMIdicc())
                sleep(.1)
                self._cimi_agent_resource = AgentResource(self.deviceID, self.deviceIP, self.isAuthenticated,
                                                          self.secureConnection, self.imLeader, leaderIP=self.leaderIP)
                LOG.debug(self.TAG + 'CIMI Agent Resource payload: {}'.format(self._cimi_agent_resource.getCIMIdicc()))
                status = CIMI.modify_resource(self._cimi_agent_resource_id, self._cimi_agent_resource.getCIMIdicc())
                if self._cimi_agent_resource_id == '':
                    LOG.warning(self.TAG + 'Agent resource creation failed.')
                    if not CPARAMS.DEBUG_FLAG:
                        LOG.error('Stopping Policies module due to resource creation failure.')
                        exit(4)
            else:
                # Agent resource already exists
                status = CIMI.modify_resource(self._cimi_agent_resource_id, self._cimi_agent_resource.getCIMIdicc())
                sleep(.1)
                self._cimi_agent_resource = AgentResource(self.deviceID, self.deviceIP, self.isAuthenticated,
                                                          self.secureConnection, self.imLeader, leaderIP=self.leaderIP)
                LOG.debug(self.TAG + 'CIMI Agent Resource payload: {}'.format(self._cimi_agent_resource.getCIMIdicc()))
                status = CIMI.modify_resource(self._cimi_agent_resource_id, self._cimi_agent_resource.getCIMIdicc())

            # 8. Watch Leader
            if self._connected and not self.discovery_failed:
                LOG.debug(self.TAG + 'Start Discovery Leader Watch...')
                try:
                    self.__trigger_startDiscoveryWatch()
                except Exception:
                    LOG.exception(self.TAG + 'Watch Discovery Start Fail.')
                LOG.info(self.TAG + 'Watch Discovery Start Trigger Done.')
            elif self.discovery_failed:
                LOG.warning(self.TAG + 'Discovery Watch cancelled due Discovery Trigger failed')
            else:
                return

            alive = True
            while self._connected and not self.discovery_failed and alive:
                # 6 Check if discovery connection is alive
                LOG.debug(self.TAG + 'Discovery Alive Start Trigger.')
                try:
                    alive = not self.__trigger_aliveDiscovery() # not disconnected
                except Exception:
                    LOG.exception(self.TAG + 'Discovery Alive failed')
                    alive = False
                if self._connected:
                    sleep(CPARAMS.TIME_WAIT_ALIVE)
                LOG.info(self.TAG + 'Discovery Alive Start Trigger Done.')
            if not self._connected:
                return

            if CPARAMS.DEBUG_FLAG and self.discovery_failed:
                LOG.debug(self.TAG + 'No rescan available. Stoping activity')
                return

    def __leader_switch_flow(self):
        """
        Agent become leader
        :return:
        """
        # 1. Start sending beacons
        if self._connected:
            self.discovery_leader_failed = True
            LOG.debug(self.TAG + 'Sending Broadcast trigger to discovery...')
            try:
                r = self.__trigger_switch_discovery()
                self.detectedLeaderID = self.deviceID
                self.discovery_leader_failed = not r
            except Exception as ex:
                LOG.exception(self.TAG + 'Discovery broadcast trigger failed!')
                self.detectedLeaderID = self.deviceID
            LOG.info(self.TAG + 'Discovery Broadcast Trigger Done.')
        else:
            return
        if not CPARAMS.DEBUG_FLAG and self.discovery_leader_failed:
            LOG.critical(self.TAG + 'Discovery broadcast failed, interrupting leader switch.')
            return
        self.discovery_failed = self.discovery_leader_failed

        # 2. Start CAU-client
        if self._connected:
            self.cauclient_failed = True
            LOG.debug(self.TAG + 'Sending trigger to CAU client...')
            try:
                r = self.__trigger_triggerCAUclient()
                self.cauclient_failed = not r
            except Exception:
                LOG.exception(self.TAG + 'CAUclient failed.')
                self.cauclient_failed = True
            LOG.info(self.TAG + 'CAU client Trigger Done.')
        else:
            return
        if not CPARAMS.DEBUG_FLAG and self.cauclient_failed:
            LOG.critical(self.TAG + 'CAU-Client failed, interrupting agent start.')
            return

        # 3. VPN get IP
        attempt = 0
        while self._connected and self.vpnIP is None and attempt < self.MAX_VPN_FAILURES:
            vpn_ip = VPN.getIPfromFile()
            self.vpnIP = vpn_ip if vpn_ip != '' else None
            if self.vpnIP is None:
                LOG.debug(self.TAG + 'VPN IP cannot be obtained... Retry in {}s'.format(self.WAIT_TIME_VPN))
                sleep(self.WAIT_TIME_VPN)
                attempt += 1
        if self.vpnIP is None:
            LOG.warning(self.TAG + 'VPN IP cannot be obtained.')
            if not CPARAMS.DEBUG_FLAG:
                LOG.critical(self.TAG + 'Policies module cannot continue its activity without VPN IP')
                exit(4)
        else:
            LOG.info(self.TAG + 'VPN IP: [{}]'.format(self.vpnIP))

        # 4. Switch leader categorization (or start if not started)
        if self.categorization_started:
            self.categorization_leader_failed = True
            # Switch!
            LOG.debug(self.TAG + 'Sending switch trigger to Categorization...')
            try:
                self.__trigger_switch_categorization()
                self.categorization_leader_failed = False
            except Exception:
                LOG.exception(self.TAG + 'Categorization switch to leader failed')
            LOG.info(self.TAG + 'Categorization Switch Trigger Done.')

        else:
            # Start as leader!
            LOG.debug(self.TAG + 'Sending start trigger to Categorization...')
            try:
                self.__trigger_startCategorization()
                self.categorization_leader_failed = False
                self.categorization_started = True
            except Exception:
                LOG.exception(self.TAG + 'Categorization failed')
            LOG.info(self.TAG + 'Categorization Start Trigger Done.')

        if not CPARAMS.DEBUG_FLAG and self.categorization_leader_failed:
            LOG.critical(self.TAG + 'Categorization failed, interrupting leader switch.')
            return
        self.categorization_failed = self.categorization_leader_failed

        # 5. Start Area Resilience (if not started)
        if not self.arearesilience_started:
            self.policies_failed = True
            LOG.debug(self.TAG + 'Sending start trigger to Policies...')
            try:
                self.__trigger_startLeaderProtectionPolicies()
                self.policies_failed = False
                self.arearesilience_started = True
            except Exception:
                LOG.exception(self.TAG + 'Policies Area Resilience failed!')
            LOG.info(self.TAG + 'Policies Area Resilience Start Trigger Done.')

        if not CPARAMS.DEBUG_FLAG and self.policies_failed:
            LOG.critical(self.TAG + 'Policies Area Resilience failed, interrupting agent start.')
            return

        # 8. Watch Leader
        if self._connected and not self.discovery_failed:
            LOG.debug(self.TAG + 'Start Discovery Leader Watch...')
            try:
                self.__trigger_startDiscoveryWatch()
            except Exception:
                LOG.exception(self.TAG + 'Watch Discovery Start Fail.')
            LOG.info(self.TAG + 'Watch Discovery Start Trigger Done.')
        elif self.discovery_failed:
            LOG.warning(self.TAG + 'Discovery Watch cancelled due Discovery Trigger failed')

        # Print summary
        self.__print_summary()

        # Create/Modify Agent Resource
        # IF static IP configuration setup
        self.deviceIP = CPARAMS.DEVICE_IP_FLAG
        self.leaderIP = CPARAMS.LEADER_IP_FLAG
        if self.deviceIP is None or self.leaderIP is None:
            LOG.debug(self.TAG + 'No static configuration was detected. Applying VPN values')
            self.deviceIP = self.vpnIP
            self.leaderIP = self.cloudIP

        LOG.info(self.TAG + 'deviceIP={}, leaderIP={}'.format(self.deviceIP, self.leaderIP))

        self._cimi_agent_resource = AgentResource(self.deviceID, self.deviceIP, True,
                                                  True, self.imLeader, leaderIP=self.leaderIP)
        # deprecated: real values of Auth and Conn (as now are None in the Leader)
        if self._cimi_agent_resource_id is None:
            # Create agent resource
            self._cimi_agent_resource_id = CIMI.createAgentResource(self._cimi_agent_resource.getCIMIdicc())
        else:
            # Agent resource already exists
            status = CIMI.modify_resource(self._cimi_agent_resource_id, self._cimi_agent_resource.getCIMIdicc())

        # 6. Finish
        return

    def __cloud_flow(self):
        LOG.info(self.TAG + 'Cloud flow started.')

        # 0. Cloud Agent is Leader by definition
        self.imLeader = self.imCloud

        # 1. Discovery
        LOG.debug(self.TAG + 'Discovery trigger ignored in Cloud flow.')
        self.discovery_failed = False
        self.discovery_leader_failed = False
        self.detectedLeaderID = self.deviceID

        # 2. Start CAU-client
        if self._connected:
            self.cauclient_failed = True
            LOG.debug(self.TAG + 'Sending trigger to CAU client...')
            try:
                r = self.__trigger_triggerCAUclient()
                self.cauclient_failed = not r
            except Exception:
                LOG.exception(self.TAG + 'CAUclient failed.')
                self.cauclient_failed = True
            LOG.info(self.TAG + 'CAU client Trigger Done.')
        else:
            return
        if not CPARAMS.DEBUG_FLAG and self.cauclient_failed:
            LOG.critical(self.TAG + 'CAU-Client failed, interrupting agent start.')
            return

        # 3. VPN get IP
        attempt = 0
        while self._connected and self.vpnIP is None and attempt < self.MAX_VPN_FAILURES:
            vpn_ip = VPN.getIPfromFile()
            self.vpnIP = vpn_ip if vpn_ip != '' else None
            if self.vpnIP is None:
                LOG.debug(self.TAG + 'VPN IP cannot be obtained... Retry in {}s'.format(self.WAIT_TIME_VPN))
                sleep(self.WAIT_TIME_VPN)
                attempt += 1
        if self.vpnIP is None:
            LOG.warning(self.TAG + 'VPN IP cannot be obtained.')
            if not CPARAMS.DEBUG_FLAG:
                LOG.critical(self.TAG + 'Policies module cannot continue its activity without VPN IP')
                exit(4)
        else:
            LOG.info(self.TAG + 'VPN IP: [{}]'.format(self.vpnIP))

        # 4. Switch leader categorization (or start if not started)
        if self.categorization_started:
            self.categorization_leader_failed = True
            # Switch!
            LOG.debug(self.TAG + 'Sending switch trigger to Categorization...')
            try:
                self.__trigger_switch_categorization()
                self.categorization_leader_failed = False
            except Exception:
                LOG.exception(self.TAG + 'Categorization switch to leader failed')
            LOG.info(self.TAG + 'Categorization Switch Trigger Done.')

        # 5. Area Resilience
        LOG.debug(self.TAG + 'Area Resilience trigger ignored in Cloud flow.')
        self.policies_failed = False

        # Print summary
        self.__print_summary()

        # Create Agent Resource
        self.deviceIP = self.cloudIP
        self.leaderIP = None
        self._cimi_agent_resource = AgentResource(self.deviceID, self.deviceIP, True,
                                                  True, self.imLeader)
        LOG.debug(self.TAG + 'CIMI Agent Resource payload: {}'.format(self._cimi_agent_resource.getCIMIdicc()))
        if self._cimi_agent_resource_id is None:
            # Create agent resource
            self._cimi_agent_resource_id = CIMI.createAgentResource(self._cimi_agent_resource.getCIMIdicc())
            if self._cimi_agent_resource_id == '':
                LOG.warning(self.TAG + 'Agent resource creation failed.')
                if not CPARAMS.DEBUG_FLAG:
                    LOG.error('Stopping Policies module due to resource creation failure.')
                    exit(4)
        else:
            # Agent resource already exists
            status = CIMI.modify_resource(self._cimi_agent_resource_id, self._cimi_agent_resource.getCIMIdicc())


    def __agent_switch_flow(self):
        """
        Leader become agent
        :return:
        """
        # 1. Stop Beacons   # TODO
        # 2. Switch Agent Categorization to normal OR stop # TODO
        # 3. Start agent startup flow
        self.__agent_startup_flow()
        return

    def summary(self):
        data = {
            'MACaddr': self.MACaddr,
            'detectedLeaderID': self.detectedLeaderID,
            'bssid': self.bssid,
            'deviceID': self.deviceID,
            'IDkey': self.IDkey,
            'authenticated': self.isAuthenticated,
            'secureConnection': self.secureConnection,
            'categorization_started': self.categorization_started,
            'lpp_started': self.arearesilience_started,
            'categorization_switched': self.categorization_switched,
            'discovery_switched': self.discovery_switched,
            'isLeader': self.imLeader,
            'isCloud': self.imCloud,
            'leaderIP': self.leaderIP,
            'deviceIP': self.deviceIP,
            'vpnIP': self.vpnIP,
            'cloudIP': self.cloudIP
        }
        return data

    def __print_summary(self):
        s = "\n######################## FCJP ##########################\n"
        summary = self.summary()
        for item in summary.keys():
            s += '\t[\"{}\"] : {}\n'.format(item,summary.get(item))
        s += "########################################################\n"
        LOG.info(s)

    def __trigger_startScan(self):
        r = requests.get(self.URL_DISCOVERY)
        rjson = r.json()
        if 'found_leaders' in rjson and 'used_mac' in rjson and len(rjson['found_leaders']) > 0:
            self.detectedLeaderID, self.MACaddr, self.bssid = rjson['found_leaders'][0]['Leader ID'], rjson['used_mac'], rjson['found_leaders'][0]['Bssid']
        else:
            LOG.error(self.TAG + 'Discovery is not detecting a Leader \'{}\''.format(rjson))
            self.detectedLeaderID, self.MACaddr, self.bssid = None, None, None
        # r = requests.get(self.URL_DISCOVERY_MAC)
        # rjson = r.json()
        # self.MACaddr = rjson['MACaddr']

    def __trigger_joinDiscovery(self):
        payload = {
            'interface': CPARAMS.WIFI_DEV_FLAG,
            'bssid': self.bssid
        }
        try:
            r = requests.post(self.URL_DISCOVERY_JOIN, json=payload, timeout=20.)
        except (timeout, timeout2):
            LOG.error(self.TAG + 'JOIN trigger timeout.')
            return False
        rjson = r.json()
        if r.status_code != 200:
            LOG.warning(self.TAG + 'JOIN operation failed. Reply from discovery: {}'.format(rjson['message']))
            return False
        else:
            LOG.debug(self.TAG + 'Sending MYIP trigger to Discovery...')
            try:
                r2 = requests.get(self.URL_DISCOVERY_MYIP, timeout=20.)
            except (timeout, timeout2):
                LOG.error(self.TAG + 'MYIP trigger timeout.')
                return False
            rjson2 = r2.json()
            if r2.status_code != 200:
                LOG.warning(self.TAG + 'MYIP operation failed. Reply from discovery: {}'.format(rjson2))
                return False
            LOG.debug(self.TAG + 'MYIP trigger success. Reply form Discovery: {}'.format(rjson2['IP_address']))
            self.deviceIP = rjson2['IP_address']
            return True


    def __trigger_requestID(self):
        r = requests.get(self.URL_IDENTIFICATION)
        rjson = r.json()
        LOG.debug(self.TAG + 'Identification requestID reply: {}'.format(rjson))
        self.deviceID, self.IDkey = rjson['deviceID'], rjson['IDKey']

    def __trigger_triggerCAUclient(self):
        # payload = {
        #     'MACaddr': self.MACaddr,
        #     'detectedLeaderID': self.detectedLeaderID,
        #     'deviceID': self.deviceID,
        #     'IDkey': self.IDkey
        # }
        # TODO: Define socket timeout
        s_caucl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_caucl.connect(CPARAMS.CAU_CLIENT_ADDR)
        s_caucl.send('detectedLeaderID={},deviceID={}\n'.format(self.detectedLeaderID, self.deviceID).encode())
        reply = s_caucl.recv(4092).decode()
        LOG.debug(self.TAG + 'CAU_client reply: {}'.format(reply))
        s_caucl.close()

        if 'OK' in reply:
            self.isAuthenticated = True
            self.secureConnection = True
            return True
        else:
            LOG.warning(self.TAG + 'CAU_client reply \'{}\' evaluated as error'.format(reply))
            self.isAuthenticated = False
            self.secureConnection = False
            return False

        # r = requests.post(self.URL_CAU_CLIENT, json=payload)
        # rjson = r.json()
        # if 'error' in rjson:
        #     self.isAuthenticated = False
        #     self.secureConnection = False
        # else:
        #     self.isAuthenticated = rjson['authenticated']
        #     self.secureConnection = rjson['secureConnection']

    def __trigger_startCategorization(self):
        payload = {
            'detectedLeaderID': self.detectedLeaderID,
            'deviceID': self.deviceID,
            'isLeader': self.imLeader
        }
        r = requests.post(self.URL_CATEGORIZATION, json=payload)
        rjson = r.json()
        if 'error' in rjson:
            self.categorization_started = False
        else: # TODO: check started exists
            self.categorization_started = rjson['started']

    def __trigger_startLeaderProtectionPolicies(self):
        r = requests.get(self.URL_POLICIES)
        rjson = r.json()
        if r.status_code == 200:
            return rjson['started']
        else:
            return False

    def __trigger_switch_categorization(self):
        payload = {
            'deviceID': self.deviceID
        }
        r = requests.get(self.URL_CATEGORIZATION_SWITCH_LEADER, json=payload)
        rjson = r.json()
        self.categorization_switched = rjson['started']

    def __trigger_switch_discovery(self):
        payload = {
            'broadcast_frequency': 100,
            'interface_name': CPARAMS.WIFI_DEV_FLAG,
            'config_file': CPARAMS.WIFI_CONFIG_FILE,
            'leader_id': self.deviceID
        }
        r = requests.post(self.URL_DISCOVERY_SWITCH_LEADER, json=payload)
        rjson = r.json()
        LOG.debug(self.TAG + 'Discovery broadcast start trigger received code: {} with msg: {}'.format(r.status_code, rjson['message']))
        self.discovery_switched = rjson['message']
        if r.status_code != 200:
            LOG.warning(self.TAG + 'Discovery broadcast failed with code {}. DHCP trigger is not performed.'.format(r.status_code))
        else:
            payload2 = {
                'interface_name': CPARAMS.WIFI_DEV_FLAG
            }
            r2 = requests.post(self.URL_DISCOVERY_DHCP, json=payload2)
            rjson2 = r2.json()
            self.discovery_switched += '|| DHCP: ' + rjson2['message']
            if r2.status_code == 200:
                LOG.debug(self.TAG + 'Discovery DHCP trigger successfully done with message: {}.'.format(rjson2['message']))
                return True
            else:
                LOG.warning(self.TAG + 'Discovery DHCP trigger failed with code {}'.format(r2.status_code))
        return False

    def __trigger_aliveDiscovery(self):
        payload = {
            'key': 'get'
        }
        r = requests.get(self.URL_DISCOVERY_WATCH, json=payload)
        rjson = r.json()
        print(self.TAG, 'Discovery: Disconnected Leader = {}'.format(rjson['DISCONNECTED']))
        return rjson['DISCONNECTED']

    def __trigger_startDiscoveryWatch(self):
        payload = {
            'key': 'start'
        }
        r = requests.get(self.URL_DISCOVERY_WATCH, json=payload)
        rjson = r.json()
        print(self.TAG, 'Discovery: {}'.format(rjson))