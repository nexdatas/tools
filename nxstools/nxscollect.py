#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
## \package nexdatas nexdatas.tools
## \file nxscollect.py
# Command-line tool to merging NeXus files with other file-format images
#
""" Command-line tool to merging NeXus files with other file-format images"""

import sys
import os
import re
import shutil
import fabio
import signal
from optparse import OptionParser
from pni.io.nx.h5 import open_file, deflate_filter
from .filenamegenerator import FilenameGenerator


## collector class
class Collector(object):
    ## constructor
    def __init__(self, nexusfilename, compression=2,
                 skipmissing=False,
                 storeold=False):
        self.__nexusfilename = nexusfilename
        self.__compression = compression
        self.__skipmissing = skipmissing
        self.__storeold = storeold
        self.__tempfilename = None
        self.__filepattern = re.compile("[^:]+:\\d+:\\d+")
        self.__nxsfile = None
        self.__break = False

        self.__siginfo = dict(
            (signal.__dict__[sname], sname)
            for sname in ('SIGINT', 'SIGHUP', 'SIGALRM', 'SIGTERM'))

        for sig in self.__siginfo.keys():
            signal.signal(sig, self.signalhandler)

    def signalhandler(self, sig, _):
        if sig in self.__siginfo.keys():
            self.__break = True
            print ("terminated by %s" % self.__siginfo[sig])

    def createtmpfile(self):
        self.__tempfilename = self.__nexusfilename + ".__nxscollect_temp__"
        while os.path.exists(self.__tempfilename):
            self.__tempfilename += "_"
        shutil.copy2(self.__nexusfilename, self.__tempfilename)

    def storeoldfile(self):
        temp = self.__nexusfilename + ".__nxscollect_old__"
        while os.path.exists(temp):
            temp += "_"
        shutil.move(self.__nexusfilename, temp)

    def filegenerator(self, filestr):
        if self.__filepattern.match(filestr):
            return FilenameGenerator.from_slice(filestr)
        else:
            def files():
                return [filestr]
            return files

    def loadimage(self, filename):
        try:
            return fabio.open(filename)
        except IOError:
            print("Cannot open a file %s" % filename)
            if not self.__skipmissing:
                raise Exception("Cannot open a file %s" % filename)
            return None

    def getfield(self, node, fieldname, dtype, shape):
        if fieldname in node.names():
            return node[fieldname]
        else:
            cfilter = None
            if self.__compression:
                cfilter = deflate_filter()
                cfilter.rate = self.__compression
            return node.create_field(
                fieldname,
                dtype,
                shape=[0, shape[0], shape[1]],
                chunk=[1, shape[0], shape[1]],
                filter=cfilter)

    def collect(self, files, node, fieldname=None):
        fieldname = fieldname or "data"
        field = None
        ind = 0
        for filestr in files:
            if self.__break:
                break
            inputfiles = self.filegenerator(filestr)
            for fname in inputfiles():
                if self.__break:
                    break
                image = self.loadimage(fname)
                if image:
                    if field is None:
                        field = self.getfield(
                            node, fieldname,
                            image.data.dtype.__str__(),
                            image.data.shape)
                    if ind == field.shape[0]:
                        field.grow(0, 1)
                        print "+ append %s " % (fname)
                        field[-1, ...] = image.data[...]
                    ind += 1
                    self.__nxsfile.flush()

    def inspect(self, parent, collection=False):
        if hasattr(parent, "names"):
            if collection:
                if "postrun" in parent.names():
                    inputfiles = parent.open("postrun")
                    files = inputfiles[...]
                    if isinstance(files, (str, unicode)):
                        files = [files]
                    fieldname = "data"
                    print "COLLECT: %s/%s for %s" % (
                        parent.parent.path, fieldname, files)
                    self.collect(files, parent.parent, fieldname)
            try:
                names = parent.names()
            except Exception:
                names = []
            for name in names:
                coll = False
                child = parent.open(name)
                for at in child.attributes:
                    if at.name == "NX_class":
                        gtype = at[...]
                        if gtype == 'NXcollection':
                            coll = True
                self.inspect(child, coll)

    def merge(self):
        self.createtmpfile()
        try:
            self.__nxsfile = open_file(self.__tempfilename, readonly=False)
            root = self.__nxsfile.root()
            self.inspect(root)
            self.__nxsfile.close()
            if self.__storeold:
                self.storeoldfile()
            shutil.move(self.__tempfilename, self.__nexusfilename)
        except Exception as e:
            print str(e)
            os.remove(self.__tempfilename)


## creates command-line parameters parser
def createParser():
    ## usage example
    usage = "usage: nxscollect <command> <main_nexus_file> \n" \
            + " e.g.: nxscollect /tmp/gpfs/raw/scan_234.nxs \n\n" \
            + " "

    ## option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--compression", dest="compression",
                      action="store", type=int, default=2,
                      help="deflate compression ratio")
    parser.add_option("-s", "--skip_missing", action="store_true",
                      default=False, dest="skipmissing",
                      help="skip missing files")
    parser.add_option("-r", "--replace_nexus_file", action="store_true",
                      default=False, dest="replaceold",
                      help="if not the old file is save with "
                      ".__nxscollect__old__* extension")

    return parser


## the main function
def main():

    ## run options
    options = None
    parser = createParser()
    (options, nexusfiles) = parser.parse_args()

    if not nexusfiles or not nexusfiles[0]:
        parser.print_help()
        print ""
        sys.exit(0)

    ## configuration server
    for nxsfile in nexusfiles:
        collector = Collector(nxsfile,
                              options.compression,
                              options.skipmissing,
                              not options.replaceold)
        collector.merge()

if __name__ == "__main__":
    main()