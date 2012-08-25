"""
Copyright 2007, Red Hat, Inc
see AUTHORS

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import inspect
import os
import pwd
import socket
import string
import sys
import re
import fnmatch
import tempfile
import glob
from stat import *


from certmaster.config import read_config
from certmaster.commonconfig import MinionConfig
from commonconfig import FuncdConfig


REMOTE_ERROR = "REMOTE_ERROR"


def is_error(result):
    if type(result) != list:
        return False
    if len(result) == 0:
        return False
    if result[0] == REMOTE_ERROR:
        return True
    return False


def remove_weird_chars(dirty_word):
    """
    That method will be used to clean some
    glob adress expressions because async stuff
    depends on that part

    @param dirty_word : word to be cleaned
    """
    from copy import copy
    copy_word = copy(dirty_word)
    copy_word = copy_word.replace("-","_")
    return copy_word

def get_formated_jobid(**id_pack):
    import time
    import pprint

    glob = remove_weird_chars(id_pack['spec'])
    module = remove_weird_chars(id_pack['module'])
    method = remove_weird_chars(id_pack['method'])
    job_id = "".join([glob,"-",module,"-",method,"-",pprint.pformat(time.time())])
    return job_id

def is_public_valid_method(obj, attr, blacklist=[]):
    # Note: the order can be important here.  func modules that try to inspect
    # the list of available methods may run into inifinite recursion issues if
    # getattr() is called on them.  They can work around this by placing the
    # problematic code in a private method that's called from their public
    # method if we perform the check for a leading underscore before the check
    # that calls getattr()
    if attr[0] != '_' and attr not in blacklist and \
            inspect.ismethod(getattr(obj, attr)):
        return True
    return False

def get_hostname_by_route():
    """
    "localhost" is a lame hostname to use for a key, so try to get
    a more meaningful hostname. We do this by connecting to the certmaster
    and seeing what interface/ip it uses to make that connection, and looking
    up the hostname for that.
    """
    # FIXME: this code ignores http proxies (which granted, we don't
    #      support elsewhere either.

    minion_config_file = '/etc/func/minion.conf'
    minion_config = read_config(minion_config_file, FuncdConfig)

    # don't bother guessing a hostname if they specify it in the config file
    if minion_config.minion_name:
        return minion_config.minion_name.lower()

    # try to find the hostname attached to the ip of the interface that we use
    # to talk to the certmaster
    cm_config_file = '/etc/certmaster/minion.conf'
    cm_config = read_config(cm_config_file, MinionConfig)

    server = cm_config.certmaster
    port = cm_config.certmaster_port

    s = socket.socket()
    s.settimeout(5)
    s.connect_ex((server, port))
    (intf, port) = s.getsockname()
    s.close()

    try:
        return socket.gethostbyaddr(intf)[0]
    except:
        pass

    # try to find the hostname of the ip we're listening on
    if minion_config.listen_addr:
        try:
            return socket.gethostbyaddr(minion_config.listen_addr)[0]
        except:
            pass

    # in an ideal world, this would return exactly what we want: the most meaningful hostname
    # for a system, but that is often not that case
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip != "127.0.0.1" and ip != "::1":
            return hostname.lower()
    except:
        pass

    # all else has failed to get a good hostname, so just return
    # an ip address
    return intf

def find_files_by_hostname(hostglob, filepath, fileext=''):
    """look for files in the given filepath with the given extension that
        match our hostname, but case insensitively. This handles the
        craziness that is dns names that have mixed case :("""

    # this is a little like a case insensitive glob, except it's just one
    # layer deep - not multiple layers

    if fileext and fileext[0] != '.':
        fileext = '.' + fileext
    thisregex = fnmatch.translate('%s%s' % (hostglob, fileext))
    recomp = re.compile(thisregex, re.I) # case insensitive match
    files = []
    for potfile in os.listdir(filepath):
        if recomp.match(potfile):
            files.append(potfile)

    return [os.path.normpath(filepath + '/' + file) for file in files]


def get_all_host_aliases(hostname):
    try:
        (fqdn, aliases, ips) = socket.gethostbyname_ex(hostname)
    except socket.gaierror, e:
        return [hostname]
    else:
        return [fqdn] + aliases

def get_fresh_method_instance(function_ref):
    """
    That method is kind of workaround to not break the
    current api in order to add logging capabilities per
    method level. When methods are executed during xmlrpc
    calls we have a pool of references with module methods
    and overlord call them. If we want to pass those methods
    different logger instances in order to have log call per
    job_ids we shouldnt have the same method reference to be
    called,we need fresh ones so that is how we solve that
    kind of hacky ...
    """

    #CAUTION HACKY IF STATEMNETS AROUND :)
    # we dont want private methods and system
    #modules around ,we should change system
    #module though ....
    if function_ref.__name__.startswith("_"):
        return function_ref
    else:
        try:
            # check if the module want to be single
            assert not (hasattr(function_ref.im_self,"_single") and function_ref.im_self._single)
            fresh_instance = function_ref.im_self.__class__()
        except Exception,e:
            #something went wrong so we return the normal reference value
            return function_ref
        try:
            return getattr(fresh_instance,function_ref.__name__)
        except AttributeError:
            return getattr(fresh_instance,function_ref._name_)

def should_log(args):
    if args and type(args[len(args)-1]) == dict and args[len(args)-1].has_key('__logger__') and args[len(args)-1]['__logger__'] == True:
        return True
    return False

_re_compiled_glob_match = None
def re_glob(s):
    """ Tests if a string is a shell wildcard. """
    # TODO/FIXME maybe consider checking if it is a stringsType before going on - otherwise
    # returning None
    global _re_compiled_glob_match
    if _re_compiled_glob_match is None:
        _re_compiled_glob_match = re.compile('[*?]|\[.+\]').search
    return _re_compiled_glob_match(s)
    
def getCacheDir(tmpdir='/var/tmp', reuse=True, prefix='func-'):
    """return a path to a valid and safe cachedir - only used when not running
       as root or when --tempcache is set"""
    
    uid = os.geteuid()
    try:
        usertup = pwd.getpwuid(uid)
        username = usertup[0]
    except KeyError:
        return None # if it returns None then, well, it's bollocksed

    if reuse:
        # check for /var/tmp/func-username-* - 
        prefix = '%s%s-' % (prefix, username)
        dirpath = '%s/%s*' % (tmpdir, prefix)
        cachedirs = sorted(glob.glob(dirpath))
        for thisdir in cachedirs:
            stats = os.lstat(thisdir)
            if S_ISDIR(stats[0]) and S_IMODE(stats[0]) == 448 and stats[4] == uid:
                return thisdir

    # make the dir (tempfile.mkdtemp())
    cachedir = tempfile.mkdtemp(prefix=prefix, dir=tmpdir)
    return cachedir


#################### PROGRESS BAR ##################################
# The code below can be used for progress bar purposes as we will do
#it is a combination of http://code.activestate.com/recipes/168639/ and
#http://code.activestate.com/recipes/475116/ and recipes for usage
#you can look at places we use it !


class TerminalController:
    """
    A class that can be used to portably generate formatted output to
    a terminal.

    `TerminalController` defines a set of instance variables whose
    values are initialized to the control sequence necessary to
    perform a given action.  These can be simply included in normal
    output to the terminal:

        >>> term = TerminalController()
        >>> print 'This is '+term.GREEN+'green'+term.NORMAL

    Alternatively, the `render()` method can used, which replaces
    '${action}' with the string required to perform 'action':

        >>> term = TerminalController()
        >>> print term.render('This is ${GREEN}green${NORMAL}')

    If the terminal doesn't support a given action, then the value of
    the corresponding instance variable will be set to ''.  As a
    result, the above code will still work on terminals that do not
    support color, except that their output will not be colored.
    Also, this means that you can test whether the terminal supports a
    given action by simply testing the truth value of the
    corresponding instance variable:

        >>> term = TerminalController()
        >>> if term.CLEAR_SCREEN:
        ...     print 'This terminal supports clearning the screen.'

    Finally, if the width and height of the terminal are known, then
    they will be stored in the `COLS` and `LINES` attributes.
    """
    # Cursor movement:
    BOL = ''             #: Move the cursor to the beginning of the line
    UP = ''              #: Move the cursor up one line
    DOWN = ''            #: Move the cursor down one line
    LEFT = ''            #: Move the cursor left one char
    RIGHT = ''           #: Move the cursor right one char

    # Deletion:
    CLEAR_SCREEN = ''    #: Clear the screen and move to home position
    CLEAR_EOL = ''       #: Clear to the end of the line.
    CLEAR_BOL = ''       #: Clear to the beginning of the line.
    CLEAR_EOS = ''       #: Clear to the end of the screen

    # Output modes:
    BOLD = ''            #: Turn on bold mode
    BLINK = ''           #: Turn on blink mode
    DIM = ''             #: Turn on half-bright mode
    REVERSE = ''         #: Turn on reverse-video mode
    NORMAL = ''          #: Turn off all modes

    # Cursor display:
    HIDE_CURSOR = ''     #: Make the cursor invisible
    SHOW_CURSOR = ''     #: Make the cursor visible

    # Terminal size:
    COLS = None          #: Width of the terminal (None for unknown)
    LINES = None         #: Height of the terminal (None for unknown)

    # Foreground colors:
    BLACK = BLUE = GREEN = CYAN = RED = MAGENTA = YELLOW = WHITE = ''

    # Background colors:
    BG_BLACK = BG_BLUE = BG_GREEN = BG_CYAN = ''
    BG_RED = BG_MAGENTA = BG_YELLOW = BG_WHITE = ''

    _STRING_CAPABILITIES = """
    BOL=cr UP=cuu1 DOWN=cud1 LEFT=cub1 RIGHT=cuf1
    CLEAR_SCREEN=clear CLEAR_EOL=el CLEAR_BOL=el1 CLEAR_EOS=ed BOLD=bold
    BLINK=blink DIM=dim REVERSE=rev UNDERLINE=smul NORMAL=sgr0
    HIDE_CURSOR=cinvis SHOW_CURSOR=cnorm""".split()
    _COLORS = """BLACK BLUE GREEN CYAN RED MAGENTA YELLOW WHITE""".split()
    _ANSICOLORS = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE".split()

    def __init__(self, term_stream=sys.stdout):
        """
        Create a `TerminalController` and initialize its attributes
        with appropriate values for the current terminal.
        `term_stream` is the stream that will be used for terminal
        output; if this stream is not a tty, then the terminal is
        assumed to be a dumb terminal (i.e., have no capabilities).
        """
        # Curses isn't available on all platforms
        try: import curses
        except: return

        # If the stream isn't a tty, then assume it has no capabilities.
        if not term_stream.isatty(): return

        # Check the terminal type.  If we fail, then assume that the
        # terminal has no capabilities.
        try: curses.setupterm()
        except: return

        # Look up numeric capabilities.
        self.COLS = curses.tigetnum('cols')
        self.LINES = curses.tigetnum('lines')

        # Look up string capabilities.
        for capability in self._STRING_CAPABILITIES:
            (attrib, cap_name) = capability.split('=')
            setattr(self, attrib, self._tigetstr(cap_name) or '')

        # Colors
        set_fg = self._tigetstr('setf')
        if set_fg:
            for i,color in zip(range(len(self._COLORS)), self._COLORS):
                setattr(self, color, curses.tparm(set_fg, i) or '')
        set_fg_ansi = self._tigetstr('setaf')
        if set_fg_ansi:
            for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
                setattr(self, color, curses.tparm(set_fg_ansi, i) or '')
        set_bg = self._tigetstr('setb')
        if set_bg:
            for i,color in zip(range(len(self._COLORS)), self._COLORS):
                setattr(self, 'BG_'+color, curses.tparm(set_bg, i) or '')
        set_bg_ansi = self._tigetstr('setab')
        if set_bg_ansi:
            for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
                setattr(self, 'BG_'+color, curses.tparm(set_bg_ansi, i) or '')

    def _tigetstr(self, cap_name):
        # String capabilities can include "delays" of the form "$<2>".
        # For any modern terminal, we should be able to just ignore
        # these, so strip them out.
        import curses
        cap = curses.tigetstr(cap_name) or ''
        return re.sub(r'\$<\d+>[/*]?', '', cap)

    def render(self, template):
        """
        Replace each $-substitutions in the given template string with
        the corresponding terminal control string (if it's defined) or
        '' (if it's not).
        """
        return re.sub(r'\$\$|\${\w+}', self._render_sub, template)

    def _render_sub(self, match):
        s = match.group()
        if s == '$$': return s
        else: return getattr(self, s[2:-1])

#######################################################################
# Example use case: progress bar
#######################################################################

class ProgressBar:
    """
    A 3-line progress bar, which looks like::

                                Header
        20% [===========----------------------------------]
                           progress message

    The progress bar is colored, if the terminal supports color
    output; and adjusts to the width of the terminal.
    """
    BAR = '%3d%% ${WHITE}[${BLUE}%s%s${NORMAL}${WHITE}]${NORMAL}\n'
    HEADER = '${BOLD}${CYAN}%s${NORMAL}\n\n'

    def __init__(self, term, header,minValue = 0, maxValue = 10):
        self.term = term
        if not (self.term.CLEAR_EOL and self.term.UP and self.term.BOL):
            raise ValueError("Terminal isn't capable enough -- you "
                             "should use a simpler progress dispaly.")
        self.width = self.term.COLS or 75
        self.bar = term.render(self.BAR)
        self.header = self.term.render(self.HEADER % header.center(self.width))
        self.cleared = 1 #: true if we haven't drawn the bar yet.

        self.min = minValue
        self.max = maxValue
        self.span = maxValue - minValue
        self.amount = 0       # When amount == max, we are 100% done

        #initially it is 0
        self.update(0, '')

    def update(self, newAmount, message=''):
        if newAmount < self.min: newAmount = self.min
        if newAmount > self.max: newAmount = self.max
        self.amount = newAmount

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.amount - self.min)
        percentDone = (diffFromMin / float(self.span)) * 100.0
        percentDone = round(percentDone)
        percentDone = int(percentDone)

        if self.cleared:
            sys.stdout.write(self.header)
            self.cleared = 0
        n = int((self.width-10)*percentDone/100.0)
        sys.stdout.write(
            self.term.BOL + self.term.UP + self.term.CLEAR_EOL +
            (self.bar % (percentDone, '='*n, '-'*(self.width-10-n))) +
            self.term.CLEAR_EOL + message.center(self.width))

    def clear(self):
        if not self.cleared:
            sys.stdout.write(self.term.BOL + self.term.CLEAR_EOL +
                             self.term.UP + self.term.CLEAR_EOL +
                             self.term.UP + self.term.CLEAR_EOL)
            self.cleared = 1

if __name__ == "__main__":
    import time
    term = TerminalController()
    progress = ProgressBar(term, 'Progress Status',minValue=0,maxValue=5)
    filenames = ['this', 'that', 'other', 'foo', 'bar']

    for i, filename in zip(range(len(filenames)), filenames):
        progress.update(i+1)
        time.sleep(3)

    progress.update(5,"JOB_COMPLETED")
    #progress.clear()

#################### PROGRESS BAR ##################################
