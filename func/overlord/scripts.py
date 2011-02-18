# python modules for doing normal/standard things with func command scripts
# parsing/checking for errors
# returning hosts
# returning results
# standard option parser for --forks, --outputpath, --timeout,  --hosts-from-file, --


from optparse import OptionParser
import sys


def base_func_parser(opthosts=True, outputpath=True, forkdef=40, timeoutdef=300):
    parser = OptionParser()
    if opthosts:
        parser.add_option('--host', default=[], action='append',
                   help="hosts to act on, defaults to ALL")
        parser.add_option('--hosts-from-file', default=None, dest="hostfile",
                   help="read list of hosts from this file, if '-' read from stdin")

    parser.add_option('--timeout', default=timeoutdef, type='int',
               help='set the wait timeout for func commands')
    parser.add_option('--forks', default=forkdef, type='int',
               help='set the number of forks to start up')
    parser.add_option('-d', '--delegate', default=None, action="store_true",
               help="use delegation to make function call")
    parser.add_option('--no-delegate', default=None, dest="delegate", action="store_false",
               help="disable delegation when making function call")
    if outputpath:
        parser.add_option('--outputpath', default='/var/lib/func/data/', dest="outputpath",
                   help="basepath to store results/errors output.")
    return parser

def handle_base_func_options(parser, opts):
    if hasattr(opts, 'hostfile') and opts.hostfile:
        hosts = []
        if opts.hostfile == '-':
            hosts = sys.stdin.readlines()
        else:
            hosts = open(opts.hostfile, 'r').readlines()

        for hn in hosts:
            hn = hn.strip()
            if hn.startswith('#'):
                continue
            hn = hn.replace('\n', '')
            opts.host.append(hn)

    return opts


def errorprint(msg):
    print >> sys.stderr, msg
