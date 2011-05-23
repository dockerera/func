#
# Copyright 2011
# Jan-Frode Myklebust <janfrode@tanso.net>
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

    version = "0.0.2"
    api_version = "0.0.1"
    description = "Information on active network ports and processes listening."

    def inventory(self):
        """
        Returns information on all network ports in LISTEN state and the processes listening.
        """
        flattened = ""
        for i in self.listenports():
            flattened = flattened + "\t".join(i) + "\n"
        return flattened

    def listenports(self):
        """
        Returns the adresses and ports a host is listening on.
        """

        cmd = sub_process.Popen(["netstat", "-nlp"],shell=False,stdout=sub_process.PIPE,close_fds=True)
        data = cmd.communicate()[0]

        ports = []
        tcpports = []
        udpports = []
        for line in data.splitlines():
              if line.split()[0]=="tcp":
		    pid = line.split()[6].split('/')[0]
		    cmd = self.cmdline(pid)
                    tcpports.append( (line.split()[3], "tcp", cmd) )
              elif line.split()[0]=="udp":
		    pid = line.split()[5].split('/')[0]
		    cmd = self.cmdline(pid)
                    udpports.append( (line.split()[3], "udp", cmd) )
        tcpports.sort()
        udpports.sort()
        ports.append( ('# addr:port', 'protocol', 'command [args]') )
        ports = ports + tcpports + udpports
        return ports

    def cmdline(self, pid):
        """
        Returns the commandline for a given pid as a string.
        """
        proccmdline = open("/proc/" + pid + "/cmdline").readline().split('\x00')
        return " ".join(proccmdline)
