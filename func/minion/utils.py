#!/usr/bin/python

"""
Copyright 2007, Red Hat, Inc
see AUTHORS

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import os
import socket
import string
import sys
import time
import traceback
import xmlrpclib

import codes
from func import certs
from func.config import read_config
from func.commonconfig import FuncdConfig

# "localhost" is a lame hostname to use for a key, so try to get
# a more meaningful hostname. We do this by connecting to the certmaster
# and seeing what interface/ip it uses to make that connection, and looking
# up the hostname for that. 
def get_hostname():

    # FIXME: this code ignores http proxies (which granted, we don't
    #      support elsewhere either. It also hardcodes the port number
    #      for the certmaster for now
    hostname = None
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    if ip != "127.0.0.1":
        return hostname


    config_file = '/etc/func/minion.conf'
    config = read_config(config_file, FuncdConfig)

    server = config.certmaster
    port = 51235

    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((server, port))
        (intf, port) = s.getsockname()
        hostname = socket.gethostbyaddr(intf)[0]
        s.close()
    except:
        s.close()
        raise

    return hostname
    


def create_minion_keys():
    config_file = '/etc/func/minion.conf'
    config = read_config(config_file, FuncdConfig)
    cert_dir = config.cert_dir
    master_uri = 'http://%s:51235/' % config.certmaster
    hn = get_hostname()

    if hn is None:
        raise codes.FuncException("Could not determine a hostname other than localhost")

    key_file = '%s/%s.pem' % (cert_dir, hn)
    csr_file = '%s/%s.csr' % (cert_dir, hn)
    cert_file = '%s/%s.cert' % (cert_dir, hn)
    ca_cert_file = '%s/ca.cert' % cert_dir


    if os.path.exists(cert_file) and os.path.exists(ca_cert_file):
        return

    keypair = None
    try:
        if not os.path.exists(cert_dir):
            os.makedirs(cert_dir)
        if not os.path.exists(key_file):
            keypair = certs.make_keypair(dest=key_file)
        if not os.path.exists(csr_file):
            if not keypair:
                keypair = certs.retrieve_key_from_file(key_file)
            csr = certs.make_csr(keypair, dest=csr_file)
    except Exception, e: # need a little more specificity here
        raise codes.FuncException, "Could not create local keypair or csr for minion funcd session"

    result = False
    while not result:
        try:
            result, cert_string, ca_cert_string = submit_csr_to_master(csr_file, master_uri)
        except socket.gaierror, e:
            raise codes.FuncException, "Could not locate certmaster at: http://certmaster:51235/"

        # logging here would be nice
        if not result:
            time.sleep(10)


    if result:
        cert_fo = open(cert_file, 'w')
        cert_fo.write(cert_string)
        cert_fo.close()

        ca_cert_fo = open(ca_cert_file, 'w')
        ca_cert_fo.write(ca_cert_string)
        ca_cert_fo.close()

def submit_csr_to_master(csr_file, master_uri):
    """"
    gets us our cert back from the certmaster.wait_for_cert() method
    takes csr_file as path location and master_uri
    returns Bool, str(cert), str(ca_cert)
    """

    fo = open(csr_file)
    csr = fo.read()
    s = xmlrpclib.ServerProxy(master_uri)

    return s.wait_for_cert(csr)


# this is kind of handy, so keep it around for now
# but we really need to fix out server side logging and error
# reporting so we don't need it
def trace_me():
    x = traceback.extract_stack()
    bar = string.join(traceback.format_list(x))
    return bar


def daemonize(pidfile=None):
    """
    Daemonize this process with the UNIX double-fork trick.
    Writes the new PID to the provided file name if not None.
    """

    print pidfile
    pid = os.fork()
    if pid > 0:
        sys.exit(0)
    os.setsid()
    os.umask(0)
    pid = os.fork()


    if pid > 0:
        if pidfile is not None:
            open(pidfile, "w").write(str(pid))
        sys.exit(0)