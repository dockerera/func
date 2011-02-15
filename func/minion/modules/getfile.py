#!/usr/bin/python
#Copyright (C) 2010 Louis-Frederic Coilliot
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Get a file, chunk by chunk. Minion side."""
import sys
import func_module
try:
    # py 2.4+
    import hashlib
except ImportError:
    # py 2.3 support for RHEL4
    import sha
    class hashlib:
        @staticmethod
        def new(algo):
            if algo == 'sha1':
                return sha.new()
            raise ValueError, "Bad checksum type"
try:
# py 2.4
    from base64 import b64encode
except ImportError:
# py 2.3 for RHEL4
    from base64 import encodestring as b64encode


class GetFile(func_module.FuncModule):
    """Get a file, chunk by chunk"""
    def chunkslen(self, filename):
        """Define the number of chunks of size=bufsize there is in the file"""
        bufsize = 60000
        try:
            fic = open(filename, "r")
        except IOError, err:
            sys.stderr.write("Unable to open file: %s: %s\n" % (filename, err))
            return(-1)
        chunkslen = 0
        while True:
            fic.seek(bufsize*chunkslen)
            data = fic.read(1024)
            if not data:
                break
            chunkslen += 1
        fic.close()
        return(chunkslen)

    def getchunk(self, chunknum, filename):
        """Get a chunk of the file, after a seek to the right position"""
        bufsize = 60000
        try:
            fic = open(filename, "r")
        except IOError, err:
            sys.stderr.write("Unable to open file: %s: %s\n" % (filename, err))
            checksum = -1
            return(checksum, '')
        fic.seek(bufsize*chunknum)
        chunk = b64encode(fic.read(bufsize))
        mysha = hashlib.new('sha1')
        mysha.update(chunk)
        checksum = mysha.hexdigest()
        fic.close()
        return(checksum, chunk)

