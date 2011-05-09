#
# Copyright 2011
# Jan-Frode Myklebust <janfrode@tanso.net> -- 2011
#
# This software may be freely redistributed under the terms of the GNU
# general public license.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import func_module
import sub_process

class PortinfoModule(func_module.FuncModule):

    version = "0.0.1"
    api_version = "0.0.1"
    description = "Informations on active network ports."

    def inventory(self):
        """
        Returns information on all network ports in LISTEN state.
        """
        return "\n".join(self.listenports()) + "\n"

    def listenports(self):
        """
        Returns the adresses and ports a host is listening on.
        """

        cmd = sub_process.Popen(["netstat", "-nl"],shell=False,stdout=sub_process.PIPE,close_fds=True)
        data = cmd.communicate()[0]

        ports = []
        tcpports = []
        udpports = []
        for line in data.splitlines():
              if line.split()[0]=="tcp":
                    tcpports.append(line.split()[3] + "/tcp")
              elif line.split()[0]=="udp":
                    udpports.append(line.split()[3] + "/udp")
        tcpports.sort()
        udpports.sort()
        ports = tcpports + udpports
        return ports
