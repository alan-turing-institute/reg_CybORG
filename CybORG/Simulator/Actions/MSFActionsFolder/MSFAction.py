# Copyright DST Group. Licensed under the MIT license.
from ipaddress import IPv4Address, IPv4Network

from CybORG.Shared import CybORGLogger
from CybORG.Simulator.Actions.Action import Action
from CybORG.Simulator.Host import Host
from CybORG.Simulator.Interface import Interface
from CybORG.Simulator.MSFServerSession import MSFServerSession
from CybORG.Simulator.Session import Session
from CybORG.Simulator.State import State
from CybORG.Simulator.Subnet import Subnet


class MSFAction(Action, CybORGLogger):
    def __init__(self, session, agent):
        super().__init__()
        self.session = session
        self.agent = agent

    def get_local_source_interface(self, local_session: Session, remote_address: IPv4Address, state: State) -> (Session, Interface):
        # discovers the local session and interface from routing through existing sessions
        remote_subnet = state.get_subnet_containing_ip_address(remote_address)
        # if MSF server then attempt to use the routes generated by autoroute
        if type(local_session) is MSFServerSession:
            for session, interfaces in local_session.routes.items():
                for interface in interfaces:
                    # find if remote address is in the sessions subnet
                    if remote_address in interface.subnet:
                        return local_session.children[session], interface
                    # find if the remote address is in a routable subnet
                    if interface.name in remote_subnet.nacls:
                        return local_session, interface
        for interface in state.hosts[local_session.hostname].interfaces:
            # find if remote address is in the sessions subnet
            if remote_address in interface.subnet:
                return local_session, interface

            # find if the remote address is in a routable subnet
            if interface.name != 'lo' and state.subnets[interface.subnet].name in remote_subnet.nacls:
                return local_session, interface

        return None, None

    def test_nacl(self, port, target_subnet: Subnet, originating_subnet: Subnet) -> bool:
        # return true if target subnet can receive traffic from originating subnet over specified port
        if originating_subnet == target_subnet:
            #no nacl block inside subnet
            return True

        if originating_subnet.name not in target_subnet.nacls:
            return False
        if 'all' in [i for i in target_subnet.nacls[originating_subnet.name]['in']]:
            return True
        if port in [i['PortRange'] for i in target_subnet.nacls[originating_subnet.name]['in'] if
                    type(i['PortRange']) is int]:
            return True
        return False

    def __str__(self):
        return f"{self.__class__.__name__}: MSF Session: {self.session}"
