#!/usr/bin/python
#
# Copyright 2008, Stone-IT
# Jasper Capel <capel@stone-it.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA

import func_module
import os

class Vlan(func_module.FuncModule):
    version = "0.0.1"
    api_version = "0.0.1"
    description = "Func module for VLAN management"

    # A list of VLAN IDs that should be ignored.
    # You can use this if you have VLAN IDs which are reserved for internal
    # use, which should never be touched by func.
    ignorevlans = [ ]
    vconfig = "/sbin/vconfig"
    ip = "/sbin/ip"

    def list(self):
        # Returns a dictionary, elements look like this:
        # key: interface, value: [id1, id2, id3]

        retlist = {}

        f = open("/proc/net/vlan/config")

        # Read the config, throw the header lines away
        # Lines look like:
        # bond1.1003     | 1003  | bond1
        lines = f.readlines()[2:]

        for line in lines:
            elements = line.split("|")
            vlanid = int(elements[1].strip())
            interface = elements[2].strip()

            if interface not in retlist:
                # New list in dictionary
                retlist[interface] =  [ vlanid ]
            else:
                # Append to existing list in dictionary
                retlist[interface].append(vlanid)

        return retlist

    def add(self, interface, vlanid):
        vlanid = int(vlanid)
        # Adds a vlan with vlanid on interface
        if vlanid not in self.ignorevlans:
            exitcode = os.spawnv(os.P_WAIT, self.vconfig, [ self.vconfig, "add", interface, str(vlanid)] )
        else:
            exitcode = -1
        
        return exitcode

    def delete(self, interface, vlanid):
        # Deletes a vlan with vlanid from interface
        vintfname = interface + "." + str(vlanid)
        if int(vlanid) not in self.ignorevlans:
            exitcode = os.spawnv(os.P_WAIT, self.vconfig, [ self.vconfig, "rem", vintfname] )
        else:
            exitcode = -1

        return exitcode

    def up(self, interface, vlanid):
        # Marks a vlan interface as up
        vintfname = interface + "." + str(vlanid)
        if int(vlanid) not in self.ignorevlans:
            exitcode = os.spawnv(os.P_WAIT, self.ip, [ self.ip, "link", "set", vintfname, "up" ])
        else:
            exitcode = -1

        return exitcode

    def down(self, interface, vlanid):
        # Marks a vlan interface as down
        vintfname = interface + "." + str(vlanid)
        if int(vlanid) not in self.ignorevlans:
            exitcode = os.spawnv(os.P_WAIT, self.ip, [ self.ip, "link", "set", vintfname, "down" ])
        else:
            exitcode = -1

        return exitcode

    def makeitso(self, configuration):
        # Applies the supplied configuration to the system.
        # Configuration is a dictionary, elements should look like this:
        # key: interface, value: [id1, id2, id3]
        currentconfig = self.list()

        # First, remove all VLANs present in current configuration, that are
        # not present in new configuration.
        for interface, vlans in currentconfig.iteritems():
            if interface not in configuration:
                # Remove all the vlans from this interface
                for vlan in vlans:
                    self.delete(interface, vlan)

            else:
                for vlan in vlans:
                    if vlan not in configuration[interface]:
                        # VLAN not in new configuration, remove it.
                        self.delete(interface, vlan)

        # Second, add all VLANs present in new configuration, that are not
        # present in current configuration
        for interface, vlans in configuration.iteritems():
            if interface not in currentconfig:
                # Add all VLANs for this interface
                for vlan in vlans:
                    self.add(interface, vlan)

            else:
                for vlan in vlans:
                    if vlan not in currentconfig[interface]:
                        # VLAN not in current configuration, add it.
                        self.add(interface, vlan)

        # Todo: Compare the current configuration to the supplied configuration
        return self.list()
