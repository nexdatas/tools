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
# \file XMLConfiguratorTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import random
import struct
import binascii
# import time
# import threading
import PyTango
# import json
from nxstools import nxscreate

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


if sys.version_info > (3,):
    unicode = str
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class NXSCreateCompFSTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        try:
            # random seed
            self.seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            # random seed
            self.seed = long(time.time() * 256)  # use fractional seconds

        self._rnd = random.Random(self.seed)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self.__args = '{"host":"localhost", "db":"nxsconfig", ' \
                      '"read_default_file":"/etc/my.cnf", "use_unicode":true}'

        # home = expanduser("~")
        db = PyTango.Database()
        self.host = db.get_db_host().split(".")[0]
        self.port = db.get_db_port()
        self.directory = "."
        self.flags = ""

    # sets xmlconfiguration
    # \param xmlc configuration instance
    # \param xml xml configuration string
    def setXML(self, xmlc, xml):
        xmlc.XMLString = xml

    # gets xmlconfiguration
    # \param xmlc configuration instance
    # \returns xml configuration string
    def getXML(self, xmlc):
        return xmlc.XMLString

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    def dsexists(self, name):
        return os.path.isfile("%s/%s.ds.xml" % (self.directory, name))

    def cpexists(self, name):
        return os.path.isfile("%s/%s.xml" % (self.directory, name))

    def getds(self, name):
        fl = open("%s/%s.ds.xml" % (self.directory, name), 'r')
        xml = fl.read()
        fl.close()
        return xml

    def getcp(self, name):
        fl = open("%s/%s.xml" % (self.directory, name), 'r')
        xml = fl.read()
        fl.close()
        return xml

    def deleteds(self, name):
        os.remove("%s/%s.ds.xml" % (self.directory, name))

    def deletecp(self, name):
        os.remove("%s/%s.xml" % (self.directory, name))

    def runtest(self, argv):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        nxscreate.main()
        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er

    def runtestexcept(self, argv, exception):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        try:
            error = False
            nxscreate.main()
        except exception:
            error = True
        self.assertEqual(error, True)

        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er

    # Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error = False
            method(*args, **kwargs)
        except exception:
            error = True
        self.assertEqual(error, True)

    # sets selection configuration
    # \param selectionc configuration instance
    # \param selection selection configuration string
    def setSelection(self, selectionc, selection):
        selectionc.selection = selection

    # gets selectionconfiguration
    # \param selectionc configuration instance
    # \returns selection configuration string
    def getSelection(self, selectionc):
        return selectionc.selection

    def test_comp_simple(self):
        """ test nxsccreate comp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate comp starttimetest %s' % self.flags).split(),
                'starttimetest',
                '<?xml version="1.0" ?>\n'
                '<definition>\n'
                '  <group name="$var.entryname#\'scan\'$var.serialno" '
                'type="NXentry">\n'
                '    <group name="instrument" type="NXinstrument">\n'
                '      <group name="collection" type="NXcollection">\n'
                '        <field name="starttimetest" type="NX_FLOAT">\n'
                '          <strategy mode="STEP"/>\n'
                '          $datasources.starttimetest\n'
                '        </field>\n'
                '      </group>\n'
                '    </group>\n'
                '  </group>\n'
                '</definition>\n'
            ],
            [
                ('nxscreate comp endtimetest %s' % self.flags).split(),
                'endtimetest',
                '<?xml version="1.0" ?>\n'
                '<definition>\n'
                '  <group name="$var.entryname#\'scan\'$var.serialno" '
                'type="NXentry">\n'
                '    <group name="instrument" type="NXinstrument">\n'
                '      <group name="collection" type="NXcollection">\n'
                '        <field name="endtimetest" type="NX_FLOAT">\n'
                '          <strategy mode="STEP"/>\n'
                '          $datasources.endtimetest\n'
                '        </field>\n'
                '      </group>\n'
                '    </group>\n'
                '  </group>\n'
                '</definition>\n'
            ],
            [
                ('nxscreate comp wwwtest %s' % self.flags).split(),
                'wwwtest',
                '<?xml version="1.0" ?>\n'
                '<definition>\n'
                '  <group name="$var.entryname#\'scan\'$var.serialno" '
                'type="NXentry">\n'
                '    <group name="instrument" type="NXinstrument">\n'
                '      <group name="collection" type="NXcollection">\n'
                '        <field name="wwwtest" type="NX_FLOAT">\n'
                '          <strategy mode="STEP"/>\n'
                '          $datasources.wwwtest\n'
                '        </field>\n'
                '      </group>\n'
                '    </group>\n'
                '  </group>\n'
                '</definition>\n'
            ],
            [
                ('nxscreate comp abstest %s' % self.flags).split(),
                'abstest',
                '<?xml version="1.0" ?>\n'
                '<definition>\n'
                '  <group name="$var.entryname#\'scan\'$var.serialno" '
                'type="NXentry">\n'
                '    <group name="instrument" type="NXinstrument">\n'
                '      <group name="collection" type="NXcollection">\n'
                '        <field name="abstest" type="NX_FLOAT">\n'
                '          <strategy mode="STEP"/>\n'
                '          $datasources.abstest\n'
                '        </field>\n'
                '      </group>\n'
                '    </group>\n'
                '  </group>\n'
                '</definition>\n'
            ],
        ]

        totest = []
        try:
            for arg in args:
                if not self.cpexists(arg[1]):
                    totest.append(arg[1])

                    vl, er = self.runtest(arg[0])

                    self.assertEqual('', er)
                    self.assertTrue(vl)
                    xml = self.getcp(arg[1])
                    self.assertEqual(arg[2], xml)

                    self.deletecp(arg[1])
        finally:
            for cp in totest:
                if self.cpexists(cp):
                    self.deletecp(cp)

    def test_comp_first_last(self):
        """ test nxsccreate comp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate comp -v test_exp_mot  -l 3 %s'
                 % self.flags).split(),
                ['test_exp_mot01',
                 'test_exp_mot02',
                 'test_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot01" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot01\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate comp -v testmotor '
                 '-s  my_exp_mot  -l 3 %s'
                 % self.flags).split(),
                ['testmotor01',
                 'testmotor02',
                 'testmotor03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot01" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot01\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate comp -v testvm '
                 ' -s  test_exp_mot -f 2 -l 3 %s'
                 % self.flags).split(),
                ['testvm02',
                 'testvm03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        try:
            for arg in args:
                skip = False
                for cp in arg[1]:
                    if self.cpexists(cp):
                        skip = True
                if not skip:
                    for cp in arg[1]:
                        totest.append(cp)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, cp in enumerate(arg[1]):
                        xml = self.getcp(cp)
                        self.assertEqual(
                            arg[2][i], xml)

                    for cp in arg[1]:
                        self.deletecp(cp)
        finally:
            for cp in totest:
                if self.cpexists(cp):
                    self.deletecp(cp)

    def test_comp_first_last_fn(self):
        """ test nxsccreate comp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate comp --device-prefix test_exp_mot  --last 3 %s'
                 % self.flags).split(),
                ['test_exp_mot01',
                 'test_exp_mot02',
                 'test_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot01" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot01\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate comp --device-prefix testmotor '
                 '--datasource-prefix  my_exp_mot  --last 3 %s'
                 % self.flags).split(),
                ['testmotor01',
                 'testmotor02',
                 'testmotor03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot01" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot01\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate comp --device-prefix testvm '
                 ' --datasource-prefix  test_exp_mot --first 2 --last 3 %s'
                 % self.flags).split(),
                ['testvm02',
                 'testvm03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        try:
            for arg in args:
                skip = False
                for cp in arg[1]:
                    if self.cpexists(cp):
                        skip = True
                if not skip:
                    for cp in arg[1]:
                        totest.append(cp)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, cp in enumerate(arg[1]):
                        xml = self.getcp(cp)
                        self.assertEqual(
                            arg[2][i], xml)

                    for cp in arg[1]:
                        self.deletecp(cp)
        finally:
            for cp in totest:
                if self.cpexists(cp):
                    self.deletecp(cp)

    def test_comp_first_last_overwrite_false(self):
        """ test nxsccreate comp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate comp -v testmotor '
                 '-s  my_exp_mot  -l 3 %s'
                 % self.flags).split(),
                ['testmotor01',
                 'testmotor02',
                 'testmotor03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot01" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot01\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
                ('nxscreate comp -v testmotor '
                 '-s  myexpmot  -l 3 %s'
                 % self.flags).split(),
            ],
            [
                ('nxscreate comp -v testvm '
                 ' -s  test_exp_mot -f 2 -l 3 %s' % self.flags).split(),
                ['testvm02',
                 'testvm03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
                ('nxscreate comp -v testvm '
                 ' -s  tstexpmot -f 2 -l 3 %s' % self.flags).split(),
            ],
        ]

        totest = []
        try:
            for arg in args:
                skip = False
                for cp in arg[1]:
                    if self.cpexists(cp):
                        skip = True
                if not skip:
                    for cp in arg[1]:
                        totest.append(cp)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)
                    vl, er = self.runtestexcept(arg[3], Exception)

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, cp in enumerate(arg[1]):
                        xml = self.getcp(cp)
                        self.assertEqual(
                            arg[2][i], xml)

                    for cp in arg[1]:
                        self.deletecp(cp)
        finally:
            for cp in totest:
                if self.cpexists(cp):
                    self.deletecp(cp)

    def test_comp_first_last_overwrite_true(self):
        """ test nxsccreate comp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        args = [
            [
                ('nxscreate comp -v testmotor '
                 '-s  myexpmot  -l 3 %s'
                 % self.flags).split(),
                ['testmotor01',
                 'testmotor02',
                 'testmotor03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot01" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot01\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="my_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.my_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
                ('nxscreate comp -v testmotor '
                 '-s  my_exp_mot  -l 3 %s --overwrite '
                 % self.flags).split(),
            ],
            [
                ('nxscreate comp -v testvm '
                 ' -s  tstexpmot -f 2 -l 3 %s' % self.flags).split(),
                ['testvm02',
                 'testvm03'],
                [
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot02" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot02\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n<definition>\n'
                    '  <group name="$var.entryname#\'scan\'$var.serialno"'
                    ' type="NXentry">\n'
                    '    <group name="instrument" type="NXinstrument">\n'
                    '      <group name="collection" type="NXcollection">\n'
                    '        <field name="test_exp_mot03" type="NX_FLOAT">\n'
                    '          <strategy mode="STEP"/>\n'
                    '          $datasources.test_exp_mot03\n'
                    '        </field>\n'
                    '      </group>\n'
                    '    </group>\n'
                    '  </group>\n'
                    '</definition>\n',
                ],
                ('nxscreate comp -v testvm -o '
                 ' -s  test_exp_mot -f 2 -l 3 %s' % self.flags).split(),
            ],
        ]

        totest = []
        try:
            for arg in args:
                skip = False
                for cp in arg[1]:
                    if self.cpexists(cp):
                        skip = True
                if not skip:
                    for cp in arg[1]:
                        totest.append(cp)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)
                    vl, er = self.runtest(arg[3])

                    if er:
                        self.assertEqual(
                            "Info: NeXus hasn't been setup yet. \n\n", er)
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, cp in enumerate(arg[1]):
                        xml = self.getcp(cp)
                        self.assertEqual(
                            arg[2][i], xml)

                    for cp in arg[1]:
                        self.deletecp(cp)
        finally:
            for cp in totest:
                if self.cpexists(cp):
                    self.deletecp(cp)


if __name__ == '__main__':
    unittest.main()
