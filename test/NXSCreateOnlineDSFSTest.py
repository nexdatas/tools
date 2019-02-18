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
import nxstools
from nxstools import nxscreate
from nxstools import nxsdevicetools

try:
    import nxsextrasp00
except ImportError:
    from . import nxsextrasp00

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    import TestServerSetUp
except ImportError:
    from . import TestServerSetUp


if sys.version_info > (3,):
    unicode = str
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class NXSCreateOnlineDSFSTest(unittest.TestCase):

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
        self.flags = "-d . "

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

    def test_onlineds_stepping_motor(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
 <name>my_exp_mot01</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/exp.01</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>1</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>my_exp_mot02</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/exp.02</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>2</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>my_exp_mot03</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/exp.03</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>3</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
</hw>
"""

        args = [
            [
                ('nxscreate onlineds %s %s'
                 % (fname, self.flags)).split(),
                ['my_exp_mot01',
                 'my_exp_mot02',
                 'my_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot01" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.01" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot02" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.02" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot03" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.03" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            os.remove(fname)
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_stepping_motor_noclientlike(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
 <name>my_oh1_mot01</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/oh1.01</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_oh1</controller>
 <channel>1</channel>
 <rootdevicename>p09/motor/oh1</rootdevicename>
</device>
<device>
 <name>my_oh1_mot02</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/oh1.02</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_oh1</controller>
 <channel>2</channel>
 <rootdevicename>p09/motor/oh1</rootdevicename>
</device>
<device>
 <name>my_oh1_mot03</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/motor/oh1.03</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_oh1</controller>
 <channel>3</channel>
 <rootdevicename>p09/motor/oh1</rootdevicename>
</device>
</hw>
"""

        args = [
            [
                ('nxscreate onlineds -t %s %s'
                 % (fname, self.flags)).split(),
                ['my_oh1_mot01',
                 'my_oh1_mot02',
                 'my_oh1_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_oh1_mot01" type="TANGO">\n'
                    '    <device hostname="haso000"'
                    ' member="attribute" name="p09/motor/oh1.01" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_oh1_mot02" type="TANGO">\n'
                    '    <device hostname="haso000"'
                    ' member="attribute" name="p09/motor/oh1.02" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_oh1_mot03" type="TANGO">\n'
                    '    <device hostname="haso000"'
                    ' member="attribute" name="p09/motor/oh1.03" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate onlineds --noclientlike %s %s'
                 % (fname, self.flags)).split(),
                ['my_oh1_mot01',
                 'my_oh1_mot02',
                 'my_oh1_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_oh1_mot01" type="TANGO">\n'
                    '    <device hostname="haso000"'
                    ' member="attribute" name="p09/motor/oh1.01" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_oh1_mot02" type="TANGO">\n'
                    '    <device hostname="haso000"'
                    ' member="attribute" name="p09/motor/oh1.02" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_oh1_mot03" type="TANGO">\n'
                    '    <device hostname="haso000"'
                    ' member="attribute" name="p09/motor/oh1.03" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            os.remove(fname)
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_stepping_motor_lower(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
 <name>my_exp_mot01</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/Motor/exp.01</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>1</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>my_exp_Mot02</name>
 <type>Stepping_motor</type>
 <module>oms58</module>
 <device>P09/motor/exp.02</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>2</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>My_exp_mot03</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>P09/motor/exp.03</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>3</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
</hw>
"""

        args = [
            [
                ('nxscreate onlineds %s %s'
                 % (fname, self.flags)).split(),
                ['my_exp_mot01',
                 'my_exp_mot02',
                 'my_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot01" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.01" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot02" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.02" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot03" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/exp.03" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            os.remove(fname)
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_stepping_motor_nolower(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
 <name>my_exp_mot01</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>p09/Motor/exp.01</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>1</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>my_exp_Mot02</name>
 <type>Stepping_motor</type>
 <module>oms58</module>
 <device>P09/motor/exp.02</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>2</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
<device>
 <name>My_exp_mot03</name>
 <type>stepping_motor</type>
 <module>oms58</module>
 <device>P09/motor/exp.03</device>
 <control>tango</control>
 <hostname>haso000:10000</hostname>
 <controller>oms58_exp</controller>
 <channel>3</channel>
 <rootdevicename>p09/motor/exp</rootdevicename>
</device>
</hw>
"""

        args = [
            [
                ('nxscreate onlineds %s %s -n '
                 % (fname, self.flags)).split(),
                ['my_exp_mot01',
                 'my_exp_Mot02',
                 'My_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot01" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/Motor/exp.01" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_Mot02" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="P09/motor/exp.02" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="My_exp_mot03" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="P09/motor/exp.03" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
            [
                ('nxscreate onlineds %s %s --nolower '
                 % (fname, self.flags)).split(),
                ['my_exp_mot01',
                 'my_exp_Mot02',
                 'My_exp_mot03'],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_mot01" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/Motor/exp.01" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_exp_Mot02" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="P09/motor/exp.02" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="My_exp_mot03" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="P09/motor/exp.03" '
                    'port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            os.remove(fname)
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_motors(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
    <name>my_abs</name>
    <type>step_motor</type>
    <module>absbox</module>
    <device>p09/absorbercontroller/mag.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my2_abs</name>
    <type>motor</type>
    <module>absbox</module>
    <device>p09/absorbercontroller/mag.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_tango_motor</name>
    <type>motor</type>
    <module>motor_tango</module>
    <device>p09/motor/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_kohzu</name>
    <type>motor</type>
    <module>kohzu</module>
    <device>p09/kohzu/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_smchydra</name>
    <type>motor</type>
    <module>smchydra</module>
    <device>p09/smchydra/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_lom</name>
    <type>motor</type>
    <module>lom</module>
    <device>p09/lom/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_oms58</name>
    <type>motor</type>
    <module>oms58</module>
    <device>p09/oms58/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_e6c</name>
    <type>motor</type>
    <module>e6c</module>
    <device>p09/e6c/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_omsmaxv</name>
    <type>motor</type>
    <module>omsmaxv</module>
    <device>p09/omsmaxv/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_spk</name>
    <type>motor</type>
    <module>spk</module>
    <device>p09/spk/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_pie710</name>
    <type>motor</type>
    <module>pie710</module>
    <device>p09/pie710/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_pie712</name>
    <type>motor</type>
    <module>pie712</module>
    <device>p09/pie712/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_e6c_p09_eh2</name>
    <type>motor</type>
    <module>e6c_p09_eh2</module>
    <device>p09/e6c_p09_eh2/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_smaract</name>
    <type>motor</type>
    <module>smaract</module>
    <device>p09/smaract/mot.01</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
</hw>
"""

        args = [
            [
                ('nxscreate onlineds %s %s'
                 % (fname, self.flags)).split(),
                [
                    'my_abs',
                    'my2_abs',
                    'my_tango_motor',
                    'my_kohzu',
                    'my_smchydra',
                    'my_lom',
                    'my_oms58',
                    'my_e6c',
                    'my_omsmaxv',
                    'my_spk',
                    'my_pie710',
                    'my_pie712',
                    'my_e6c_p09_eh2',
                    'my_smaract',
                ],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_abs" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/absorbercontroller/mag.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my2_abs" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/absorbercontroller/mag.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_tango_motor" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/motor/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_kohzu" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/kohzu/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_smchydra" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/smchydra/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_lom" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/lom/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_oms58" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/oms58/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_e6c" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/e6c/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_omsmaxv" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/omsmaxv/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_spk" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/spk/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_pie710" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/pie710/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_pie712" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/pie712/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_e6c_p09_eh2" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/e6c_p09_eh2/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_smaract" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="p09/smaract/mot.01"'
                    ' port="10000"/>\n    <record name="Position"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            os.remove(fname)
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_attributes(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
    <name>my_test_counter_tango</name>
    <type>type_tango</type>
    <module>counter_tango</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_v260</name>
    <type>type_tango</type>
    <module>v260</module>
    <device>mytest/v260/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>

<device>
    <name>my_test_dgg2</name>
    <type>type_tango</type>
    <module>dgg2</module>
    <device>mytest/dgg2/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_mca_8701</name>
    <type>type_tango</type>
    <module>mca_8701</module>
    <device>mytest/mca_8701/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_mca_sis3302new</name>
    <type>type_tango</type>
    <module>mca_sis3302new</module>
    <device>mytest/mca_sis3302new/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_mca_sis3302</name>
    <type>type_tango</type>
    <module>mca_sis3302</module>
    <device>mytest/mca_sis3302/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_sis3610</name>
    <type>type_tango</type>
    <module>sis3610</module>
    <device>mytest/sis3610/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_vdot32in</name>
    <type>type_tango</type>
    <module>vdot32in</module>
    <device>mytest/vdot32in/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_sis3820</name>
    <type>type_tango</type>
    <module>sis3820</module>
    <device>mytest/sis3820/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_tip551</name>
    <type>type_tango</type>
    <module>tip551</module>
    <device>mytest/tip551/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_tip850dac</name>
    <type>type_tango</type>
    <module>tip850dac</module>
    <device>mytest/tip850dac/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_tip830</name>
    <type>type_tango</type>
    <module>tip830</module>
    <device>mytest/tip830/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_tip850adc</name>
    <type>type_tango</type>
    <module>tip850adc</module>
    <device>mytest/tip850adc/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_vfcadc</name>
    <type>type_tango</type>
    <module>vfcadc</module>
    <device>mytest/vfcadc/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
</hw>
"""

        args = [
            [
                ('nxscreate onlineds %s %s'
                 % (fname, self.flags)).split(),
                [
                    'my_test_counter_tango',
                    'my_test_v260',
                    'my_test_dgg2',
                    'my_test_mca_8701',
                    'my_test_mca_sis3302new',
                    'my_test_mca_sis3302',
                    'my_test_sis3610',
                    'my_test_vdot32in',
                    'my_test_sis3820',
                    'my_test_tip551',
                    'my_test_tip850dac',
                    'my_test_tip830',
                    'my_test_tip850adc',
                    'my_test_vfcadc',
                ],
                [
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_counter_tango"'
                    ' type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/vcexecutor/ct"'
                    ' port="10000"/>\n    <record name="Counts"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_v260" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/v260/ct"'
                    ' port="10000"/>\n    <record name="Counts"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_dgg2" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/dgg2/ct"'
                    ' port="10000"/>\n    <record name="SampleTime"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_mca_8701" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/mca_8701/ct"'
                    ' port="10000"/>\n    <record name="Data"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_mca_sis3302new"'
                    ' type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/mca_sis3302new/ct"'
                    ' port="10000"/>\n    <record name="Data"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_mca_sis3302" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/mca_sis3302/ct"'
                    ' port="10000"/>\n    <record name="Data"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_sis3610" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/sis3610/ct"'
                    ' port="10000"/>\n    <record name="Value"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_vdot32in" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/vdot32in/ct"'
                    ' port="10000"/>\n    <record name="Value"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_sis3820" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/sis3820/ct"'
                    ' port="10000"/>\n    <record name="Counts"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_tip551" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/tip551/ct"'
                    ' port="10000"/>\n    <record name="Voltage"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_tip850dac" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/tip850dac/ct"'
                    ' port="10000"/>\n    <record name="Voltage"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_tip830" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/tip830/ct"'
                    ' port="10000"/>\n    <record name="Counts"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_tip850adc" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/tip850adc/ct"'
                    ' port="10000"/>\n    <record name="Value"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                    '<?xml version="1.0" ?>\n'
                    '<definition>\n'
                    '  <datasource name="my_test_vfcadc" type="TANGO">\n'
                    '    <device group="__CLIENT__" hostname="haso000"'
                    ' member="attribute" name="mytest/vfcadc/ct"'
                    ' port="10000"/>\n    <record name="Counts"/>\n'
                    '  </datasource>\n'
                    '</definition>\n',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)

                    for i, ds in enumerate(arg[1]):
                        xml = self.getds(ds)
                        self.assertEqual(
                            arg[2][i], xml)

                    for ds in arg[1]:
                        self.deleteds(ds)
        finally:
            os.remove(fname)
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_attributes_alias(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = '<?xml version="1.0"?>\n' \
              '<hw>\n' \
              '<device>\n' \
              '    <name>%s</name>\n' \
              '    <type>type_tango</type>\n' \
              '    <module>counter_tango</module>\n' \
              '    <device>%s</device>\n' \
              '    <control>tango</control>\n' \
              '    <hostname>haso000:10000</hostname>\n' \
              '</device>\n' \
              '</hw>\n'

        dsout = \
            '<?xml version="1.0" ?>\n' \
            '<definition>\n' \
            '  <datasource name="%s"' \
            ' type="TANGO">\n' \
            '    <device group="__CLIENT__" hostname="%s"' \
            ' member="attribute" name="%s"' \
            ' port="%s"/>\n    <record name="%s"/>\n' \
            '  </datasource>\n' \
            '</definition>\n'

        command = ('nxscreate onlineds %s %s'
                   % (fname, self.flags)).split()

        args = [
            ['my_test_%s' % ky, "mytest/%s/00" % ky, vl[0]]
            for ky, vl in nxsdevicetools.moduleAttributes.items()
            if ky not in nxsdevicetools.moduleAttributes.keys()
        ]

        totest = []
        try:
            for arg in args:
                ds = arg[0]
                dv = arg[1]
                attr = arg[2]
                print("%s %s %s " % (ds, dv, attr))
                if os.path.isfile(fname):
                    raise Exception("Test file %s exists" % fname)
                print(xml % (ds, dv))
                with open(fname, "w") as fl:
                    fl.write(xml % (ds, dv))
                try:
                    tsv = TestServerSetUp.TestServerSetUp(
                        dv, "MYTESTS1",
                        ds
                    )
                    tsv.setUp()
                    skip = False
                    if self.dsexists(ds):
                        skip = True
                    if not skip:
                        totest.append(ds)

                        vl, er = self.runtest(command)

                        if er:
                            self.assertTrue(er.startswith(
                                "Info"))
                        else:
                            self.assertEqual('', er)
                        self.assertTrue(vl)

                        dsxml = self.getds(ds)
                        self.assertEqual(
                            dsout % (ds, self.host, dv, self.port, attr),
                            dsxml)

                        self.deleteds(ds)
                finally:
                    os.remove(fname)
                    if tsv:
                        tsv.tearDown()
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_attributes_multi(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = '<?xml version="1.0"?>\n' \
              '<hw>\n' \
              '<device>\n' \
              '    <name>%s</name>\n' \
              '    <type>type_tango</type>\n' \
              '    <module>%s</module>\n' \
              '    <device>%s</device>\n' \
              '    <control>tango</control>\n' \
              '    <hostname>%s:%s</hostname>\n' \
              '</device>\n' \
              '</hw>\n'

        dsout = \
            '<?xml version="1.0" ?>\n' \
            '<definition>\n' \
            '  <datasource name="%s"' \
            ' type="TANGO">\n' \
            '    <device group="%s" hostname="%s"' \
            ' member="attribute" name="%s"' \
            ' port="%s"/>\n    <record name="%s"/>\n' \
            '  </datasource>\n' \
            '</definition>\n'

        command = ('nxscreate onlineds %s %s'
                   % (fname, self.flags)).split()

        args = [
            ['my_test_%s' % ky, "mytest/%s/00" % ky, vl, ky]
            for ky, vl in nxstools.xmltemplates.moduleMultiAttributes.items()
        ]

        totest = []
        try:
            for arg in args:
                ds = arg[0]
                dv = arg[1]
                attr = list(arg[2])
                module = arg[3]
                if ("%s@pool" % module) in \
                   nxstools.xmltemplates.moduleMultiAttributes.keys():
                    attr.extend(
                        nxstools.xmltemplates.moduleMultiAttributes[
                            "%s@pool" % module])
                    attr.append("")
                if os.path.isfile(fname):
                    raise Exception("Test file %s exists" % fname)
                with open(fname, "w") as fl:
                    fl.write(xml % (ds, module, dv, self.host, self.port))
                try:
                    tsv = TestServerSetUp.TestServerSetUp(
                        dv, "MYTESTS1",
                        ds
                    )
                    tsv.setUp()
                    # for el in attr:
                    #     if el not in [""]:
                    #         try:
                    #             tsv.dp.CreateAttribute(el)
                    #         except Exception as e:
                    #             print(e)
                    #             tsv.dp.CreateAttribute(el)

                    skip = False
                    for el in attr:
                        if self.dsexists(
                                "%s_%s" % (ds, el.lower())
                                if el else ds):
                            skip = True
                    if not skip:
                        for el in attr:
                            totest.append(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )

                        vl, er = self.runtest(command)

                        if er:
                            self.assertTrue(er.startswith(
                                "Info"))
                        else:
                            self.assertEqual('', er)
                        self.assertTrue(vl)

                        for el in attr:
                            dsxml = self.getds(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )
                            self.assertEqual(
                                dsout % (
                                    "%s_%s" % (ds, el.lower()) if el else ds,
                                    "%s_" % (ds) if el else "__CLIENT__",
                                    self.host, dv, self.port, el or "Value"),
                                dsxml)

                        for el in attr:
                            self.deleteds(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )
                finally:
                    os.remove(fname)
                    if tsv:
                        tsv.tearDown()
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_attributes_multi_xmltemplates(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = '<?xml version="1.0"?>\n' \
              '<hw>\n' \
              '<device>\n' \
              '    <name>%s</name>\n' \
              '    <type>type_tango</type>\n' \
              '    <module>%s</module>\n' \
              '    <device>%s</device>\n' \
              '    <control>tango</control>\n' \
              '    <hostname>%s:%s</hostname>\n' \
              '</device>\n' \
              '</hw>\n'

        dsout = \
            '<?xml version="1.0" ?>\n' \
            '<definition>\n' \
            '  <datasource name="%s"' \
            ' type="TANGO">\n' \
            '    <device group="%s" hostname="%s"' \
            ' member="attribute" name="%s"' \
            ' port="%s"/>\n    <record name="%s"/>\n' \
            '  </datasource>\n' \
            '</definition>\n'

        commands = [
            ('nxscreate onlineds -p nxstools.xmltemplates %s %s'
             % (fname, self.flags)).split(),
            ('nxscreate onlineds --xml-package nxstools.xmltemplates %s %s'
             % (fname, self.flags)).split(),
        ]

        args = [
            ['my_test_%s' % ky, "mytest/%s/00" % ky, vl, ky]
            for ky, vl in nxstools.xmltemplates.moduleMultiAttributes.items()
        ]

        totest = []
        try:
            for ci, arg in enumerate(args):
                ds = arg[0]
                dv = arg[1]
                attr = list(arg[2])
                module = arg[3]
                if ("%s@pool" % module) in \
                   nxstools.xmltemplates.moduleMultiAttributes.keys():
                    attr.extend(
                        nxstools.xmltemplates.moduleMultiAttributes[
                            "%s@pool" % module])
                    attr.append("")
                if os.path.isfile(fname):
                    raise Exception("Test file %s exists" % fname)
                with open(fname, "w") as fl:
                    fl.write(xml % (ds, module, dv, self.host, self.port))
                try:
                    tsv = TestServerSetUp.TestServerSetUp(
                        dv, "MYTESTS1",
                        ds
                    )
                    tsv.setUp()
                    # for el in attr:
                    #     if el not in [""]:
                    #         try:
                    #             tsv.dp.CreateAttribute(el)
                    #         except Exception as e:
                    #             print(e)
                    #             tsv.dp.CreateAttribute(el)

                    skip = False
                    for el in attr:
                        if self.dsexists(
                                "%s_%s" % (ds, el.lower())
                                if el else ds):
                            skip = True
                    if not skip:
                        for el in attr:
                            totest.append(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )

                        vl, er = self.runtest(commands[ci % 2])

                        if er:
                            self.assertTrue(er.startswith(
                                "Info"))
                        else:
                            self.assertEqual('', er)
                        self.assertTrue(vl)
                        for el in attr:
                            dsxml = self.getds(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )
                            self.assertEqual(
                                dsout % (
                                    "%s_%s" % (ds, el.lower()) if el else ds,
                                    "%s_" % (ds) if el else "__CLIENT__",
                                    self.host, dv, self.port, el or "Value"),
                                dsxml)

                        for el in attr:
                            self.deleteds(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )
                finally:
                    os.remove(fname)
                    if tsv:
                        tsv.tearDown()
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_attributes_multi_nxsextrasp00(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = '<?xml version="1.0"?>\n' \
              '<hw>\n' \
              '<device>\n' \
              '    <name>%s</name>\n' \
              '    <type>type_tango</type>\n' \
              '    <module>%s</module>\n' \
              '    <device>%s</device>\n' \
              '    <control>tango</control>\n' \
              '    <hostname>%s:%s</hostname>\n' \
              '</device>\n' \
              '</hw>\n'

        dsout = \
            '<?xml version="1.0" ?>\n' \
            '<definition>\n' \
            '  <datasource name="%s"' \
            ' type="TANGO">\n' \
            '    <device group="%s" hostname="%s"' \
            ' member="attribute" name="%s"' \
            ' port="%s"/>\n    <record name="%s"/>\n' \
            '  </datasource>\n' \
            '</definition>\n'

        if __name__ == 'test.NXSCreateOnlineDSFSTest':
            commands = [
                ('nxscreate onlineds -p test.nxsextrasp00 %s %s'
                 % (fname, self.flags)).split(),
                ('nxscreate onlineds --xml-package test.nxsextrasp00 %s %s'
                 % (fname, self.flags)).split(),
            ]
        else:
            commands = [
                ('nxscreate onlineds -p nxsextrasp00 %s %s'
                 % (fname, self.flags)).split(),
                ('nxscreate onlineds --xml-package nxsextrasp00 %s %s'
                 % (fname, self.flags)).split(),
            ]

        args = [
            ['my_test_%s' % ky, "mytest/%s/00" % ky, vl, ky]
            for ky, vl in nxsextrasp00.moduleMultiAttributes.items()
        ]

        totest = []
        try:
            for ci, arg in enumerate(args):
                ds = arg[0]
                dv = arg[1]
                attr = list(arg[2])
                module = arg[3]
                if ("%s@pool" % module) in \
                   nxsextrasp00.moduleMultiAttributes.keys():
                    attr.extend(
                        nxsextrasp00.moduleMultiAttributes[
                            "%s@pool" % module])
                    attr.append("")
                if os.path.isfile(fname):
                    raise Exception("Test file %s exists" % fname)
                with open(fname, "w") as fl:
                    fl.write(xml % (ds, module, dv, self.host, self.port))
                try:
                    tsv = TestServerSetUp.TestServerSetUp(
                        dv, "MYTESTS1",
                        ds
                    )
                    tsv.setUp()
                    # for el in attr:
                    #     if el not in [""]:
                    #         try:
                    #             tsv.dp.CreateAttribute(el)
                    #         except Exception as e:
                    #             print(e)
                    #             tsv.dp.CreateAttribute(el)

                    skip = False
                    for el in attr:
                        if self.dsexists(
                                "%s_%s" % (ds, el.lower())
                                if el else ds):
                            skip = True
                    if not skip:
                        for el in attr:
                            totest.append(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )

                        vl, er = self.runtest(commands[ci % 2])

                        if er:
                            self.assertTrue(er.startswith(
                                "Info"))
                        else:
                            self.assertEqual('', er)
                        self.assertTrue(vl)

                        for el in attr:
                            dsxml = self.getds(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )
                            self.assertEqual(
                                dsout % (
                                    "%s_%s" % (ds, el.lower()) if el else ds,
                                    "%s_" % (ds) if el else "__CLIENT__",
                                    self.host, dv, self.port, el or "Value"),
                                dsxml)

                        for el in attr:
                            self.deleteds(
                                "%s_%s" % (ds, el.lower())
                                if el else ds
                            )
                finally:
                    os.remove(fname)
                    if tsv:
                        tsv.tearDown()
        finally:
            for ds in totest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_onlineds_attributes_nomodule(self):
        """ test nxsccreate onlineds file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.xml' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """<?xml version="1.0"?>
<hw>
<device>
    <name>my_test_mythenroi</name>
    <type>type_tango</type>
    <module>mythenroi</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_mca8715roi</name>
    <type>type_tango</type>
    <module>mca8715roi</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_sis3302roi</name>
    <type>type_tango</type>
    <module>sis3302roi</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_sis3302</name>
    <type>type_tango</type>
    <module>sis3302</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_sis3302multiscan</name>
    <type>type_tango</type>
    <module>sis3302multiscan</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_tangoattributectctrl</name>
    <type>type_tango</type>
    <module>tangoattributectctrl</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>
<device>
    <name>my_test_xmcd</name>
    <type>type_tango</type>
    <module>xmcd</module>
    <device>mytest/vcexecutor/ct</device>
    <control>tango</control>
    <hostname>haso000:10000</hostname>
</device>

</hw>
"""

        args = [
            [
                ('nxscreate onlineds %s %s'
                 % (fname, self.flags)).split(),
                [
                    'my_test_mythenroi',
                    'my_test_mca8715roi',
                    'my_test_sis3302roi',
                    'my_test_sis3302',
                    'my_test_sis3302multiscan',
                    'my_test_tangoattributectctrl',
                    'my_test_xmcd',
                ],
            ],
        ]

        totest = []
        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                skip = False
                for ds in arg[1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1]:
                        totest.append(ds)

                    vl, er = self.runtest(arg[0])

                    if er:
                        self.assertTrue(er.startswith(
                            "Info"))
                    else:
                        self.assertEqual('', er)
                    self.assertTrue(vl)
                    for i, ds in enumerate(arg[1]):
                        self.assertTrue(
                            "SKIPPING %s:    " % (ds) in vl
                        )
        finally:
            os.remove(fname)


if __name__ == '__main__':
    unittest.main()
