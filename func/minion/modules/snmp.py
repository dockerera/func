# Copyright 2007, Red Hat, Inc
# James Bowes <jbowes@redhat.com>
# Seth Vidal modified command.py to be snmp.py
#
# This software may be freely redistributed under the terms of the GNU
# general public license.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

"""
Arbitrary command execution module for func.
"""

import func_module
#Needed for compatibility with Python < 2.4
try:
    import subprocess
except ImportError:
    from func.minion import sub_process as subprocess

base_snmp_command = '/usr/bin/snmpget -v2c -Ov -OQ'


class Snmp(func_module.FuncModule):

    version = "0.0.2"
    api_version = "0.0.1"
    description = "SNMP related calls through FUNC."

    def get(self, oid, rocommunity, hostname='localhost'):
        """
        Runs an snmpget on a specific oid returns the output of the call.
        """
        command = '%s -c %s %s %s' % (base_snmp_command, rocommunity,
                                      hostname, oid)

        cmdref = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=False,
                                  close_fds=True)

        data = cmdref.communicate()

        return (cmdref.returncode, data[0], data[1])

    def register_method_args(self):
        """
        Implementing the argument getter
        """

        return {
                'get': {
                    'args': {
                        'oid': {
                            'type': 'string',
                            'optional': False,
                            'description': 'The OID'
                            },
                        'rocommunity': {
                            'type': 'string',
                            'optional': False,
                            'description': "The read only community string"
                            },
                        'hostname': {
                            'type': 'string',
                            'optional': True,
                            'default': 'localhost',
                            'description': "The host name to be applied on"
                            }
                        },
                    'description': ("Runs an snmpget on a specific oid "
                                    "returns the output of the call")
                    }
                }
    #def walk(self, oid, rocommunity):

    #def table(self, oid, rocommunity):
