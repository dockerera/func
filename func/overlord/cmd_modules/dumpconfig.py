"""
Dump func-client/overlord config information

Copyright 2011, Red Hat, Inc
see AUTHORS

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""


import optparse
import os

from func.overlord import base_command
from certmaster import certs

class DumpConfig(base_command.BaseCommand):
    name = "dump_config"
    usage = "dump func-client/overlord config"
    summary = usage

    def do(self, args):
        self.server_spec = self.parentCommand.server_spec
        self.getOverlord()
        print 'config:'
        for l in str(self.overlord_obj.config).split('\n'):
            print '\t' + l
        print ''
        print 'key file:  %s' % self.overlord_obj.key
        cert = certs.retrieve_cert_from_file(self.overlord_obj.cert)
        print 'cert file: %s' % self.overlord_obj.cert
        print 'ca file: %s' % self.overlord_obj.ca
        print 'cert dn: %s' % cert.get_subject().CN
        print 'certificate hash: %s' % cert.subject_name_hash()
        print 'timeout: %s' % self.overlord_obj.timeout
        print 'forks: %s' % self.overlord_obj.nforks
        print 'cmd modules loaded:'
        for mn in sorted(self.overlord_obj.methods.keys()):
            print '\t' + mn
        print 'minion map:'
        print self.overlord_obj.minionmap
