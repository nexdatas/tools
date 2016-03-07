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
                 storeold=False,
                 testmode=False):
        self.__nexusfilename = nexusfilename
        self.__compression = compression
        self.__skipmissing = skipmissing
        self.__testmode = testmode
        self.__storeold = storeold
        self.__tempfilename = None
        self.__filepattern = re.compile("[^:]+:\\d+:\\d+")
        self.__nxsfile = None
        self.__break = False
        self.__fullfilename = None

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

    def absolutefilename(self, filename, masterfile):
        if not os.path.isabs(filename):
            nexusfilepath = os.path.join('/', *os.path.abspath(
                masterfile).split('/')[:-1])
            filename = os.path.abspath(os.path.join(nexusfilepath, filename))
        return filename

    def findfile(self, filename, nname=None):
        tmpfname = self.absolutefilename(filename, self.__nexusfilename)
        if os.path.exists(tmpfname):
            # print "F1"
            return tmpfname
        tmpfname = self.absolutefilename(filename, self.__fullfilename)
        if os.path.exists(tmpfname):
            # print "F2"
            return tmpfname
        if nname is not None and '.nxs' == self.__fullfilename[-4:]:
            tmpfname = '%s/%s/%s' % (
                self.__fullfilename[:-4], nname,
                filename.split("/")[-1])
            if os.path.exists(tmpfname):
                # print "F3"
                return tmpfname
        # print "F4"

        return filename

    def loadimage(self, filename):
        try:
            return fabio.open(filename)
        except Exception:
            print("Cannot open a file %s" % filename)
            if not self.__skipmissing:
                raise Exception("Cannot open a file %s" % filename)
            return None

    def addattr(self, node, attrs):
        attrs = attrs or {}
        for name, (value, dtype, shape) in attrs.items():
            if not self.__testmode:
                node.attributes.create(
                    name, dtype, shape, overwrite=True)[...] = value
            print " + add attribute: %s = %s" % (name, value)

    def getfield(self, node, fieldname, dtype, shape, fieldattrs,
                 fieldcompression):
        field = None
        if fieldname in node.names():
            return node[fieldname]
        else:
            if not self.__testmode:
                cfilter = None
                if fieldcompression:
                    cfilter = deflate_filter()
                    cfilter.rate = fieldcompression
                    field = node.create_field(
                        fieldname,
                        dtype,
                        shape=[0, shape[0], shape[1]],
                        chunk=[1, shape[0], shape[1]],
                        filter=cfilter)
            self.addattr(field, fieldattrs)
            return field

    def collect(self, files, node, fieldname=None, fieldattrs=None,
                fieldcompression=None):
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
                fname = self.findfile(fname, node.name)
                image = self.loadimage(fname)
                if image:
                    if field is None:
                        field = self.getfield(
                            node, fieldname,
                            image.data.dtype.__str__(),
                            image.data.shape,
                            fieldattrs, fieldcompression)
                    if self.__testmode or ind == field.shape[0]:
                        if not self.__testmode:
                            field.grow(0, 1)
                            field[-1, ...] = image.data[...]
                        print " * append %s " % (fname)
                    ind += 1
                    if not self.__testmode:
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
                    fieldattrs = {}
                    fieldcompression = None
                    for at in inputfiles.attributes:
                        if at.name == "fieldname":
                            fieldname = at[...]
                        elif at.name == "fieldcompression":
                            fieldcompression = int(at[...])
                        elif at.name.startswith("fieldattr_"):
                            atname = at.name[10:]
                            if atname:
                                fieldattrs[atname] = (
                                    at[...], at.dtype, at.shape
                                )

                    print "populate: %s/%s with %s" % (
                        parent.parent.path, fieldname, files)
                    if fieldcompression is None:
                        fieldcompression = self.__compression
                    self.collect(files, parent.parent, fieldname, fieldattrs,
                                 fieldcompression)
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
            self.__nxsfile = open_file(
                self.__tempfilename, readonly=self.__testmode)
            root = self.__nxsfile.root()
            try:
                self.__fullfilename = root.attributes['file_name'][...]
                # print self.__fullfilename
            except:
                pass
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
    usage = "usage: nxscollect -x <command> <main_nexus_file> \n" \
            + " e.g.: nxscollect -x /tmp/gpfs/raw/scan_234.nxs \n\n" \
            + " "

    ## option parser
    parser = OptionParser(usage=usage)
    parser.add_option("-x", "--execute", action="store_true",
                      default=False, dest="execute",
                      help="setup servers action")
    parser.add_option("-t", "--test", action="store_true",
                      default=False, dest="test",
                      help="setup servers action")
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

    if not options.execute and not options.test:
        parser.print_help()
        print ""
        sys.exit(0)

    ## configuration server
    for nxsfile in nexusfiles:
        collector = Collector(nxsfile,
                              options.compression,
                              options.skipmissing,
                              not options.replaceold,
                              options.test)
        collector.merge()

if __name__ == "__main__":
    main()
