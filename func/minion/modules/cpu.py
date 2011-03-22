
#
# Copyright 2011
# Tomas Edwardsson <tommi@tommi.org>
#
# This software may be freely redistributed under the terms of the GNU
# general public license.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import func_module
from timemodule import sleep
from func.minion.codes import FuncException

SAMPLE_TIMER = 5
MAX_SAMPLE_TIMER = 18

class CpuModule(func_module.FuncModule):
    version = "0.0.1"
    api_version = "0.0.1"
    description = "Gathering CPU related information"

    def jiffies(self):

        # Which fields we are parsing from /proc stat
        fields = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest']

        # Returning struct
        res = {}

        # Open the /proc/stat
        try:
            stat_fd = open("/proc/stat", "r")
        except Exception, e:
            raise FuncException("Unable to open /proc/stat: %s" % (e))

        # Run through the contents of /proc/stat
        for statline in stat_fd.readlines():
            # We don't care about non CPU stuff
            if statline[0:3] != 'cpu':
                break
            statline = (statline.split())

            # split cpu name and its stats
            cpu, stat = statline[0], statline[1:]

            # Total jiffies for this cpu
            total = 0

            # Create the dictionary
            res[cpu] = {}

            # Run through stats, matching with named fields
            for i in xrange(1, (len(stat))):
                try:
                    res[cpu][fields[i]] = int(stat[i])
                except IndexError:
                    break
                total += int(stat[i])

            # Record total jiffies
            res[cpu]['total'] = total

        return res

    def usage(self, sampletime=SAMPLE_TIMER):
        """
        Returns percentage CPU utilization in an given
        timeperiod.
        """
        if int(sampletime) > MAX_SAMPLE_TIMER:
            raise FuncException("sampletime maximum is %s" % MAX_SAMPLE_TIMER)

        # Get CPU statistics
        prestat = self.jiffies()

        # Wait for some activity
        sleep(int(sampletime))

        # Re fetch CPU statistics
        poststat = self.jiffies()

        # Dict to store results
        results = {}

        # Run through each CPU entry
        for cpu in prestat.keys():
            total = poststat[cpu]['total'] - prestat[cpu]['total']
            results[cpu] = {}
            for k in prestat[cpu].keys():
                if k == 'total': continue
                # Calculate the percentage
                results[cpu][k] = float(poststat[cpu][k] - prestat[cpu][k]) / float(total) * 100
        return results

    def register_method_args(self):
        """
        Register the CPU method arguments
        """
        return{
            'usage':{
                'args':{
                    'sampletime':{
                        'type': 'int',
                        'default': SAMPLE_TIMER,
                        'optional':True,
                        'description':'How long to sample CPU usage',
                    },
                },
                'description':'Gather CPU data over period and return percent averages',
            },
            'jiffies':{
                'args':{},
                'description':'Fetch the CPU jiffies from /proc/stat',
            },
        }
