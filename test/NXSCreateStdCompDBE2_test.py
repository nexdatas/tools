#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2018 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
# \package test nexdatas
# \file XMLConfigurator_test.py
# unittests for field Tags running Tango Server
#
import unittest
import sys


try:
    import NXSCreateStdCompDBR_test
except Exception:
    from . import NXSCreateStdCompDBR_test


if sys.version_info > (3,):
    unicode = str
    long = int


# test fixture
class NXSCreateStdCompDBE2Test(
        NXSCreateStdCompDBR_test.NXSCreateStdCompDBRTest):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        NXSCreateStdCompDBR_test.NXSCreateStdCompDBRTest.__init__(
            self, methodName)

        self.flags = " --database --server testp09/testmcs/testr228 " \
                     "--external aatestp09/testmcs2/testr228 "
        self.device = 'aatestp09/testmcs2/testr228'


if __name__ == '__main__':
    unittest.main()
