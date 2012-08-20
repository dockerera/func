"""
getfile command line
Based on "copyfile command line" by RedHat, Inc
Modifications are Copyright Marcus Lauer (ml1100@nyu.edu) and released under the GNU Public License

Copyright for the GPL code used in this project can be found below.
---
copyfile command line

Copyright 2007, Red Hat, Inc
see AUTHORS

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""


import optparse
import os
import pprint
import stat
import xmlrpclib

from func.overlord import base_command
from func.overlord import client


class CopyFile(base_command.BaseCommand):
    name = "getfile"
    usage = "\n  getfile -l localdir -r remotesource\n    remotesource = file to download from the specified minions\n    localdir = directory in which to put the downloaded files"
    summary = "get a file from minions"

    def addOptions(self):
        self.parser.add_option("-l", "--localdir", dest="localdir",
                               action="store")
        self.parser.add_option("-r", "--remotesource", dest="remotesource",
                                action="store")

    def handleOptions(self, options):
        pass

    def do(self, args):
        if not self.options.localdir or not self.options.remotesource:
            self.outputUsage()
            return

        self.server_spec = self.parentCommand.server_spec
        self.getOverlord()

        return self.overlord_obj.local.getfile.get(self.options.remotesource, self.options.localdir)
