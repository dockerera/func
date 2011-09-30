# Copyright 2007, Red Hat, Inc
# James Bowes <jbowes@redhat.com>
# Seth Vidal modified command.py to be nagios-check.py
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

from certmaster.config import BaseConfig, Option
import func_module
try:
    import subprocess
#Needed for compatibility with Python < 2.4
except ImportError:
    from func.minion import sub_process as subprocess

class NagiosCheck(func_module.FuncModule):

    version = "0.0.2"
    api_version = "0.0.1"
    description = "Runs Nagios checks."

    class Config(BaseConfig):
        nagios_path = Option('/usr/lib/nagios/plugins')

    def run(self, check_command):
        """
        Runs a Nagios check gathering the return code, stdout, and stderr 
        as a tuple.
        """
        command = '%s/%s' % (self.options.nagios_path, check_command)

        cmdref = subprocess.Popen(command.split(),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, 
                                   shell=False, close_fds=True)
        
        data = cmdref.communicate()
        return (cmdref.returncode, data[0], data[1])

    def register_method_args(self):
        """
        Implementing argument getter part
        """

        return{
                'run':{
                    'args':{
                        'check_command':{
                            'type':'string',
                            'optional':False,
                            'description':"The command to be checked"
                            }
                        },
                    'description':"Runs a nagios check returning the return code"
                    }
                }
