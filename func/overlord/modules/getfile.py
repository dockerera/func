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

"""Get a file on the minions, chunk by chunk. Overlord side."""
from func.overlord import overlord_module
import os

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
    # py 2.4+
    from base64 import b64decode
except ImportError:
    # py 2.3 support for RHEL4
    from base64 import decodestring as b64decode

class getfile(overlord_module.BaseModule):
    """Get a file on the minions"""
    def get(self, source, foldertarget):
        """Get a file on the minions, chunk by chunk. Save the files locally""" 
        chunkslendict = self.parent.run("getfile", "chunkslen", [ source ])
        # Exclude results for minions with a REMOTE_ERROR
        chunkslens = [ clen for clen in chunkslendict.values()\
                       if (type(clen) == type(int())) ]
        maxchunk = max(chunkslens)

        if maxchunk == -1:
            msg = 'Unable to open the file on the minion(s)' 
            status = 1
            return status, msg

        if not os.path.isdir(foldertarget):
            try:
                os.mkdir(foldertarget)
            except OSError:
                msg = 'Problem during the creation of the folder %s'\
                      % (foldertarget) 
                status = 1
                return status, msg

        if not os.access(foldertarget, os.W_OK):
            msg = 'The folder %s is not writeable' % (foldertarget) 
            status = 1
            return status, msg

        nullsha = hashlib.new('sha1').hexdigest()
        sourcebasename = os.path.basename(source)
        excluderrlist = [] 

        for chunknum in range(maxchunk):
            currentchunks = self.parent.run("getfile", "getchunk",
                                            [chunknum, source]).items()
            for minion, chunkparams in currentchunks:
                if minion in excluderrlist:
                    # previous error reported
                    continue 
                try:
                    checksum, chunk = chunkparams
                except ValueError:
                    # Probably a REMOTE_ERROR
                    excluderrlist.append(minion)
                    continue
                mysha = hashlib.new('sha1')
                mysha.update(chunk)
                if checksum == -1:
                    # On this minion there was no file to get
                    continue
                if mysha.hexdigest() == nullsha:
                    # On this minion there is no more chunk to get
                    continue 
                minionfolder = foldertarget+'/'+minion
                if mysha.hexdigest() == checksum:
                    if not os.path.isdir(minionfolder):
                        try:
                            os.mkdir(minionfolder)
                        except OSError:
                            excluderrlist.append(minion) 
                            continue
                    if chunknum == 0:
                        fic = open(minionfolder+'/'+sourcebasename, 'w')
                    else:
                        fic = open(minionfolder+'/'+sourcebasename, 'a')
                    fic.write(b64decode(chunk))
                    fic.close()
                else:
                    # Error - checksum failed during copy
                    # Delete the partial file
                    # Abort the copy for this minion
                    excluderrlist.append(minion)
                    os.remove(minionfolder+'/'+sourcebasename)
        return 0, foldertarget
