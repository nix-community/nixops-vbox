# -*- coding: utf-8 -*-

# Automatic provisioning of Virtualbox Networks.

import os
import re
import ipaddress
import threading
from nixops.util import attr_property, logged_exec
from nixops.resources import ResourceDefinition, ResourceState
from nixopsvbox.backends.virtualbox import VirtualBoxDefinition, VirtualBoxState

class VirtualBoxNetworkDefinition(ResourceDefinition):
    """Definition of the VirtualBox Network"""

    @classmethod
    def get_type(cls):
        return "vbox-network"

    @classmethod
    def get_resource_type(cls):
        return "vboxNetworks"

    def __init__(self, xml):
        ResourceDefinition.__init__(self, xml)
        self.network_type = xml.find("attrs/attr[@name='type']/string").get("value")
        self.network_cidr = xml.find("attrs/attr[@name='cidrBlock']/string").get("value")

        self.static_ips = { x.find("attr[@name='machine']/string").get("value"):
                            x.find("attr[@name='address']/string").get("value") for x in xml.findall("attrs/attr[@name='staticIPs']/list/attrs") }

    def show_type(self):
        return "{0} [{1:8} {2}]".format(self.get_type(), self.network_type, self.network_cidr)

class VirtualBoxNetworkState(ResourceState):
    """State of the VirtualBox Network"""

    network_name  = attr_property("virtualbox.network_name", None)
    network_type  = attr_property("virtualbox.network_type", None)
    network_cidr  = attr_property("virtualbox.network_cidr", None)
    static_ips    = attr_property("virtualbox.static_ips", [], "json")

    _lock  = threading.Lock()

    @classmethod
    def get_type(cls):
        return "vbox-network"

    def __init__(self, depl, name, id):
        ResourceState.__init__(self, depl, name, id)
        VirtualBoxNetwork.logger = self.logger

    def show_type(self):
        s = super(VirtualBoxNetworkState, self).show_type()
        if self.state == self.UP: s = "{0} [{1}]".format(s, self.network_type)
        return s

    @property
    def resource_id(self):
        return self.network_name

    @property
    def public_ipv4(self):
        return self.network_cidr if self.state == self.UP else None;

    nix_name = "vboxNetworks"

    @property
    def full_name(self):
        return "VirtualBox network '{}'".format(self.name)

    def create(self, defn, check, allow_reboot, allow_recreate):
        assert isinstance(defn, VirtualBoxNetworkDefinition)

        if check: self.check()

        if self.state != self.UP:
            self.log("creating {}...".format(self.full_name))
            with self._lock:
                self.network_type = defn.network_type
                self.network_cidr = defn.network_cidr
                self.static_ips   = defn.static_ips
                self.network_name = VirtualBoxNetworks[defn.network_type].create(self, defn).name
                self.state = self.UP
            return

        self.log("updating {}...".format(self.full_name))
        if self._can_update(defn, allow_reboot, allow_recreate):
            with self._lock:
                self.network_cidr = defn.network_cidr
                self.static_ips   = defn.static_ips
                self.network_name = VirtualBoxNetworks[defn.network_type](self.network_name).update(self, defn).name
                self.state = self.UP
            return

    def _can_update(self, defn, allow_reboot, allow_recreate):
        if self.network_type != defn.network_type:
            self.warn("change of the network type from {0} to {1} is not supported; skipping".format(self.network_type, defn.network_type))
            return False

        if self.network_cidr != defn.network_cidr and not allow_reboot:
            self.warn("change of the network CIDR from {0} to {1} requires reboot; skipping".format(self.network_cidr, defn.network_cidr))
            return False

        if any(defn.static_ips.get(machine) != address for machine, address in self.static_ips.iteritems()) and not allow_reboot:
            self.warn("change of existing bindings for static IPs requires reboot; skipping")
            return False

        return True

    def destroy(self, wipe=False):
        if self.state != self.UP: return True
        if not self.depl.logger.confirm("are you sure you want to destroy {}?".format(self.full_name)):
            return False

        self.log("destroying {}...".format(self.full_name))

        with self._lock:
            VirtualBoxNetworks[self.network_type](self.network_name).destroy()

        return True


    # def _is_attached(self):
    #     for m in self.depl.resources.values if isintance(m, VirtualBoxState):
    #         if m.

    #     if isinstance(mstate, VirtualBoxState) and isinstance(mdefn, VirtualBoxDefinition):
    #         k    = "{_name}:{network_type}".format(**self.__dict__)
    #         nics = mstate.parse_nic_spec(mdefn)
    #         if nics.has(k)

    def _check(self):
        if self.network_type and self.network_name in VirtualBoxNetworks[self.network_type].findall():
            return super(VirtualBoxNetworkState, self)._check()

        if self.network_name:
            self.warn("'{0}' seems to have been destroyed unexpectedly. To fix the issue, please re-run ‘nixops deploy‘ with ‘--allow-reboot‘ option".format(self.network_name))

        with self.depl._db:
            self.network_name = None
            self.state = self.MISSING

        return False

class VirtualBoxNetwork(object):
    """Wrapper for VBoxManage CLI network operations"""

    logger = None

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def update(self, state, defn):
        pass

    @classmethod
    def _findall_dhcped(cls):
        return re.findall(r"NetworkName: *(NatNetwork\d+|HostInterfaceNetworking-vboxnet\d+) *", logged_exec([
            "VBoxManage", "list", "dhcpservers"
        ], cls.logger, capture_stdout=True))

    def setup_dhcp_server(self, state, defn):
        subnet = ipaddress.ip_network(unicode(defn.network_cidr), strict=False)

        logged_exec([
            "VBoxManage" , "dhcpserver", "modify" if self._name in self._findall_dhcped() else "add",
            "--netname"  , self._name,
            "--netmask"  , str(subnet.netmask),
            "--ip"       , str(subnet[2]),
            "--lowerip"  , str(subnet[3]),
            "--upperip"  , str(subnet[-2]),
            "--enable"
        ], self.logger)

        for machine, address in defn.static_ips.iteritems():
            mstate = state.depl.resources.get(machine)
            mdefn  = state.depl.definitions.get(machine)
            if isinstance(mstate, VirtualBoxState) and isinstance(mdefn, VirtualBoxDefinition):
                k    = "{name}:{network_type}".format(**defn.__dict__)
                nics = mstate.parse_nic_spec(mdefn)

                if nics.get(k):

                    def set_static_ip(): logged_exec([
                        "VBoxManage", "dhcpserver", "modify",
                        "--netname" , self._name,
                        "--vm"      , mstate.vm_id,
                        "--nic"     , str(nics[k]["num"]),
                        "--fixed-address", address
                    ], self.logger)

                    set_static_ip() if mstate.vm_id else mstate.add_hook("after_createvm", set_static_ip)

                else:
                    state.warn("cannot assign a static IP '{0}' to non-attached machine '{1}'".format(address, machine))
            else:
                state.warn("cannot assign a static IP '{0}' to non-existent machine '{1}'".format(address, machine))

        return subnet

    def destroy(self):
        logged_exec(["VBoxManage", "dhcpserver", "remove", "--netname", self._name], self.logger, check=False)

class VirtualBoxHostNetwork(VirtualBoxNetwork):

    def __init__(self, name):
        super(VirtualBoxHostNetwork, self).__init__("HostInterfaceNetworking-{}".format(name))
        self._if_name = name

    @classmethod
    def create(cls, state, defn):

        name = re.match(r"^.*'(vboxnet\d+)'.*$", logged_exec([
            "VBoxManage", "hostonlyif", "create"
        ], cls.logger, capture_stdout=True)).group(1)

        return cls(name).update(state, defn)

    @classmethod
    def findall(cls):
        return re.findall(r"Name: *(vboxnet\d+) *", logged_exec([
            "VBoxManage", "list", "hostonlyifs"
        ], cls.logger, capture_stdout=True))

    @property
    def name(self):
        return self._if_name

    def update(self, state, defn):
        subnet = self.setup_dhcp_server(state, defn)
        logged_exec(["VBoxManage", "hostonlyif", "ipconfig", self._if_name, "--ip", str(subnet[1]), "--netmask", str(subnet.netmask)], self.logger)
        return self

    def destroy(self):
        super(VirtualBoxHostNetwork, self).destroy()
        logged_exec(["VBoxManage", "hostonlyif", "remove", self._if_name], self.logger, check=False)

class VirtualBoxNatNetwork(VirtualBoxNetwork):
    _pattern = "NatNetwork{}"

    def __init__(self, name):
        super(VirtualBoxNatNetwork, self).__init__(name);

    @classmethod
    def create(cls, state, defn):
        def new_name():
            exists = cls.findall()
            return cls._pattern.format(int(exists[-1][len(cls._pattern.format("")):])+1 if exists else 1)

        name = new_name()
        logged_exec([
            "VBoxManage", "natnetwork", "add", "--netname", name, "--network", defn.network_cidr
        ], cls.logger)

        return cls(name).update(state, defn)

    @classmethod
    def findall(cls):
        return re.findall(r"Name: *("+cls._pattern.format("")+r"\d+) *", logged_exec([
            "VBoxManage", "natnetwork", "list", cls._pattern.format("*")
        ], cls.logger, capture_stdout=True))

    def update(self, state, defn):
        logged_exec(["VBoxManage", "natnetwork", "modify", "--netname", self._name, "--network", defn.network_cidr, "--enable", "--dhcp", "on"], self.logger)
        self.setup_dhcp_server(state, defn)
        #logged_exec(["VBoxManage", "natnetwork", "start" , "--netname", self._name], self.logger, check=False)
        return self

    def destroy(self):
        super(VirtualBoxNatNetwork, self).destroy()
        logged_exec(["VBoxManage", "natnetwork", "remove", "--netname", self._name], self.logger, check=False)

VirtualBoxNetworks = {
    "hostonly" : VirtualBoxHostNetwork,
    "natnet"   : VirtualBoxNatNetwork,
}
