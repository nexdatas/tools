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
import time
import PyTango
from nxstools import nxsetup
import socket
import subprocess

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    import TestMacroServerSetUp
except Exception:
    from . import TestMacroServerSetUp

try:
    import TestPoolSetUp
except Exception as e:
    print(str(e))
    from . import TestPoolSetUp


try:
    import whichcraft
    WHICHCRAFT = True
except Exception:
    WHICHCRAFT = False

try:
    __import__("nxsconfigserver")
    if not WHICHCRAFT or whichcraft.which("NXSConfigServer"):
        CNFSRV = True
    else:
        CNFSRV = False
except Exception:
    CNFSRV = False

try:
    __import__("nxswriter")
    if not WHICHCRAFT or whichcraft.which("NXSDataWriter"):
        DTWRITER = True
    else:
        DTWRITER = False
except Exception:
    DTWRITER = False

try:
    __import__("nxsrecconfig")
    if not WHICHCRAFT or whichcraft.which("NXSRecSelector"):
        RECSEL = True
    else:
        RECSEL = False
except Exception:
    RECSEL = False


if sys.version_info > (3,):
    unicode = str
    long = int


class mytty(object):

    def __init__(self, underlying):
        #        underlying.encoding = 'cp437'
        self.__underlying = underlying

    def __getattr__(self, name):
        return getattr(self.__underlying, name)

    def isatty(self):
        return True


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

# from nxsconfigserver.XMLConfigurator  import XMLConfigurator
# from nxsconfigserver.Merger import Merger
# from nxsconfigserver.Errors import (
# NonregisteredDBRecordError, UndefinedTagError,
#                                    IncompatibleNodeError)
# import nxsconfigserver


def myinput(w, text):
    myio = os.fdopen(w, 'w')
    myio.write(text)

    # myio.close()


# test fixture
class NXSetUpSetTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self.helperror = "Error: too few arguments\n"

        self.helpinfo = """usage: nxsetup [-h]
               {set,restart,start,stop,move-prop,change-prop,add-recorder-path}
               ...

Command-line tool for setting up  NeXus Tango Servers

positional arguments:
  {set,restart,start,stop,move-prop,change-prop,add-recorder-path}
                        sub-command help
    set                 set up NXSConfigServer NXSDataWriter and
                        NXSRecSelector servers
    restart             restart tango server
    start               start tango server
    stop                stop tango server
    move-prop           change property name
    change-prop         change property value
    add-recorder-path   add-recorder-path into MacroServer(s) property

optional arguments:
  -h, --help            show this help message and exit

For more help:
  nxsetup <sub-command> -h
"""

        try:
            # random seed
            self.seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            # random seed
            self.seed = long(time.time() * 256)  # use fractional seconds

        self.__rnd = random.Random(self.seed)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self.__args = '{"host":"localhost", "db":"nxsconfig", ' \
                      '"read_default_file":"/etc/my.cnf", "use_unicode":true}'
        self.__cmps = []
        self.__ds = []
        self.__man = []
        self.children = ("record", "doc", "device", "database", "query",
                         "datasource", "result")

        from os.path import expanduser
        home = expanduser("~")
        self.__args2 = '{"host":"localhost", "db":"nxsconfig", ' \
                       '"read_default_file":"%s/.my.cnf", ' \
                       '"use_unicode":true}' % home
        self.db = PyTango.Database()
        self.tghost = self.db.get_db_host().split(".")[0]
        self.tgport = self.db.get_db_port()
        self.host = socket.gethostname()
        self._ms = TestMacroServerSetUp.TestMacroServerSetUp()
        self._pool = TestPoolSetUp.TestPoolSetUp()

    def checkDevice(self, dvname):

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                dp = PyTango.DeviceProxy(dvname)
                time.sleep(0.01)
                dp.ping()
                if dp.state() == PyTango.DevState.ON:
                    found = True
                found = True
            except Exception as e:
                print("%s %s" % (dvname, e))
                found = False
            except Exception:
                found = False

            cnt += 1
        self.assertTrue(found)

    def stopServer(self, svname):
        svname, instance = svname.split("/")
        if sys.version_info > (3,):
            with subprocess.Popen(
                    "ps -ef | grep '%s %s' | grep -v grep" %
                    (svname, instance),
                    stdout=subprocess.PIPE, shell=True) as proc:

                pipe = proc.stdout
                res = str(pipe.read(), "utf8").split("\n")
                for r in res:
                    sr = r.split()
                    if len(sr) > 2:
                        subprocess.call(
                            "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                            shell=True)
                pipe.close()
        else:
            pipe = subprocess.Popen(
                "ps -ef | grep '%s %s' | grep -v grep" %
                (svname, instance),
                stdout=subprocess.PIPE, shell=True).stdout

            res = str(pipe.read()).split("\n")
            for r in res:
                sr = r.split()
                if len(sr) > 2:
                    subprocess.call(
                        "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                        shell=True)
            pipe.close()

        # HardKillServer does not work
        # admin = nxsetup.SetUp().getStarterName(self.host)
        # adp = PyTango.DeviceProxy(admin)
        # adp.UpdateServersInfo()
        # adp.HardKillServer(svname)

    def unregisterServer(self, svname, dvname=None):
        if dvname is not None:
            self.db.delete_device(dvname)
        self.db.delete_server(svname)

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        # self._sv.setUp()
        self._ms.setUp()
        self._pool.setUp()
        print("SEED = %s" % self.seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")
        self._pool.tearDown()
        self._ms.tearDown()

    def runtest(self, argv):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        etxt = None
        try:
            nxsetup.main()
        except Exception as e:
            etxt = str(e)
        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        # print(vl)
        # print(er)
        if etxt:
            print(etxt)
        self.assertTrue(etxt is None)
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
            nxsetup.main()
        except exception as e:
            etxt = str(e)
            error = True
        self.assertEqual(error, True)

        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er, etxt

    # Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error = False
            method(*args, **kwargs)
        except Exception:
            error = True
        self.assertEqual(error, True)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_default(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        vl, er, et = self.runtestexcept(['nxsetup'], SystemExit)
        self.assertTrue(self.helpinfo in vl)
        self.assertEqual(self.helperror, er)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_help(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        helps = ['-h', '--help']
        for hl in helps:
            vl, er, et = self.runtestexcept(['nxsetup', hl], SystemExit)
            self.assertTrue(self.helpinfo in vl)
            self.assertEqual('', er)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            cnf = nxsetup.knownHosts[self.host]
        else:
            cnf = {'beamline': 'nxs',
                   'masterhost': '%s' % self.host,
                   'user': 'tango',
                   'dbname': 'nxsconfig'}

        cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
        dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
        rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
        cfdvname = "%s/nxsconfigserver/%s" % \
            (cnf['beamline'], cnf["masterhost"])
        dwdvname = "%s/nxsdatawriter/%s" % \
            (cnf['beamline'], cnf["masterhost"])
        rsdvname = "%s/nxsrecselector/%s" % \
            (cnf['beamline'], cnf["masterhost"])

        cfservers = self.db.get_server_list(cfsvname).value_string
        dwservers = self.db.get_server_list(dwsvname).value_string
        rsservers = self.db.get_server_list(rssvname).value_string

        dwdevices = self.db.get_device_exported_for_class(
            "NXSDataWriter").value_string
        cfdevices = self.db.get_device_exported_for_class(
            "NXSConfigServer").value_string
        rsdevices = self.db.get_device_exported_for_class(
            "NXSRecSelector").value_string
        skiptest = False
        if cfsvname in cfservers:
            skiptest = True
        if dwsvname in dwservers:
            skiptest = True
        if rssvname in rsservers:
            skiptest = True
        if cfdvname in cfdevices:
            skiptest = True
        if dwdvname in dwdevices:
            skiptest = True
        if rsdvname in rsdevices:
            skiptest = True

        skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

        admin = nxsetup.SetUp().getStarterName(self.host)
        if not admin:
            skiptest = True
            adminproxy = None
        else:
            adminproxy = PyTango.DeviceProxy(admin)

        commands = ['nxsetup set'.split()]
        for cmd in commands:
            if not skiptest:
                try:
                    vl, er = self.runtest(cmd)
                    self.assertEqual('', er)
                    # print(vl)
                    # print(er)
                    cfservers = self.db.get_server_list(cfsvname).value_string
                    dwservers = self.db.get_server_list(dwsvname).value_string
                    rsservers = self.db.get_server_list(rssvname).value_string
                    self.assertTrue(cfsvname in cfservers)
                    self.assertTrue(dwsvname in dwservers)
                    self.assertTrue(rssvname in rsservers)

                    cfdevices = self.db.get_device_exported_for_class(
                        "NXSConfigServer").value_string
                    dwdevices = self.db.get_device_exported_for_class(
                        "NXSDataWriter").value_string
                    rsdevices = self.db.get_device_exported_for_class(
                        "NXSRecSelector").value_string
                    self.assertTrue(cfdvname in cfdevices)
                    self.assertTrue(dwdvname in dwdevices)
                    self.assertTrue(rsdvname in rsdevices)
                    self.checkDevice(cfdvname)
                    self.checkDevice(dwdvname)
                    self.checkDevice(rsdvname)
                finally:
                    try:
                        self.stopServer(rssvname)
                    except Exception:
                        pass
                    finally:
                        try:
                            self.unregisterServer(rssvname, rsdvname)
                        except Exception:
                            pass
                    try:
                        self.stopServer(cfsvname)
                    except Exception:
                        pass
                    finally:
                        try:
                            self.unregisterServer(cfsvname, cfdvname)
                        except Exception:
                            pass
                    try:
                        self.stopServer(dwsvname)
                    except Exception:
                        pass
                    finally:
                        try:
                            self.unregisterServer(dwsvname, dwdvname)
                        except Exception:
                            pass
                    setup = nxsetup.SetUp()
                    setup.waitServerNotRunning(
                        cfsvname, cfdvname,  adminproxy, verbose=False)
                    setup.waitServerNotRunning(
                        dwsvname, dwdvname, adminproxy, verbose=False)
                    setup.waitServerNotRunning(
                        rssvname, rsdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_master_beamline(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True
                adminproxy = None
            else:
                adminproxy = PyTango.DeviceProxy(admin)

            commands = [
                ('nxsetup set -b %s -m %s ' %
                 (cnf['beamline'], cnf['masterhost'])).split(),
                ('nxsetup set --beamline %s --masterhost %s ' %
                 (cnf['beamline'], cnf['masterhost'])).split(),
            ]
            for cmd in commands:
                if not skiptest:
                    try:
                        vl, er = self.runtest(cmd)
                        self.assertEqual('', er)
                        self.assertTrue(vl)
                        cfservers = self.db.get_server_list(
                            cfsvname).value_string
                        dwservers = self.db.get_server_list(
                            dwsvname).value_string
                        rsservers = self.db.get_server_list(
                            rssvname).value_string
                        self.assertTrue(cfsvname in cfservers)
                        self.assertTrue(dwsvname in dwservers)
                        self.assertTrue(rssvname in rsservers)

                        cfdevices = self.db.get_device_exported_for_class(
                            "NXSConfigServer").value_string
                        dwdevices = self.db.get_device_exported_for_class(
                            "NXSDataWriter").value_string
                        rsdevices = self.db.get_device_exported_for_class(
                            "NXSRecSelector").value_string
                        self.assertTrue(cfdvname in cfdevices)
                        if dwdvname not in dwdevices:
                            print(dwdvname)
                            print(dwdevices)
                        self.assertTrue(dwdvname in dwdevices)
                        self.assertTrue(rsdvname in rsdevices)
                        self.checkDevice(cfdvname)
                        self.checkDevice(dwdvname)
                        self.checkDevice(rsdvname)
                    finally:
                        try:
                            self.stopServer(rssvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(rssvname, rsdvname)
                            except Exception:
                                pass
                        try:
                            self.stopServer(cfsvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(cfsvname, cfdvname)
                            except Exception:
                                pass
                        try:
                            self.stopServer(dwsvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(dwsvname, dwdvname)
                            except Exception:
                                pass
                        setup = nxsetup.SetUp()
                        setup.waitServerNotRunning(
                            cfsvname, cfdvname,  adminproxy, verbose=False)
                        setup.waitServerNotRunning(
                            dwsvname, dwdvname, adminproxy, verbose=False)
                        setup.waitServerNotRunning(
                            rssvname, rsdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_all(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True
                adminproxy = None
            else:
                adminproxy = PyTango.DeviceProxy(admin)

            commands = [
                ('nxsetup set '
                 ' -b %s '
                 ' -m %s '
                 ' -u %s '
                 ' -d %s '
                 % (cnf['beamline'], cnf['masterhost'],
                    cnf['user'], cnf['dbname'])).split(),
                ('nxsetup set '
                 ' --beamline %s '
                 ' --masterhost %s '
                 ' --user %s '
                 ' --database %s '
                 % (cnf['beamline'], cnf['masterhost'],
                    cnf['user'], cnf['dbname'])).split(),
            ]
            for cmd in commands:
                if not skiptest:
                    try:
                        vl, er = self.runtest(cmd)
                        # print(vl)
                        # print(el)
                        self.assertEqual('', er)
                        self.assertTrue(vl)
                        cfservers = self.db.get_server_list(
                            cfsvname).value_string
                        dwservers = self.db.get_server_list(
                            dwsvname).value_string
                        rsservers = self.db.get_server_list(
                            rssvname).value_string
                        self.assertTrue(cfsvname in cfservers)
                        self.assertTrue(dwsvname in dwservers)
                        self.assertTrue(rssvname in rsservers)

                        cfdevices = self.db.get_device_exported_for_class(
                            "NXSConfigServer").value_string
                        dwdevices = self.db.get_device_exported_for_class(
                            "NXSDataWriter").value_string
                        rsdevices = self.db.get_device_exported_for_class(
                            "NXSRecSelector").value_string
                        self.assertTrue(cfdvname in cfdevices)
                        self.assertTrue(dwdvname in dwdevices)
                        self.assertTrue(rsdvname in rsdevices)
                        self.checkDevice(cfdvname)
                        self.checkDevice(dwdvname)
                        self.checkDevice(rsdvname)

                    finally:
                        try:
                            self.stopServer(rssvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(rssvname, rsdvname)
                            except Exception:
                                pass
                        try:
                            self.stopServer(cfsvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(cfsvname, cfdvname)
                            except Exception:
                                pass
                        try:
                            self.stopServer(dwsvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(dwsvname, dwdvname)
                            except Exception:
                                pass
                        setup = nxsetup.SetUp()
                        setup.waitServerNotRunning(
                            cfsvname, cfdvname,  adminproxy, verbose=False)
                        setup.waitServerNotRunning(
                            dwsvname, dwdvname, adminproxy, verbose=False)
                        setup.waitServerNotRunning(
                            rssvname, rsdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_nxsconfigserver(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True
                adminproxy = None
            else:
                adminproxy = PyTango.DeviceProxy(admin)
            commands = [
                ('nxsetup set NXSConfigServer '
                 ' -b %s '
                 ' -m %s '
                 ' -u %s '
                 ' -d %s '
                 % (cnf['beamline'], cnf['masterhost'],
                    cnf['user'], cnf['dbname'])).split(),
                ('nxsetup set NXSConfigServer '
                 ' --beamline %s '
                 ' --masterhost %s '
                 ' --user %s '
                 ' --database %s '
                 % (cnf['beamline'], cnf['masterhost'],
                    cnf['user'], cnf['dbname'])).split(),
            ]
            for cmd in commands:
                if not skiptest:
                    try:
                        vl, er = self.runtest(cmd)
                        self.assertEqual('', er)
                        self.assertTrue(vl)
                        cfservers = self.db.get_server_list(
                            cfsvname).value_string
                        dwservers = self.db.get_server_list(
                            dwsvname).value_string
                        rsservers = self.db.get_server_list(
                            rssvname).value_string
                        self.assertTrue(cfsvname in cfservers)
                        self.assertTrue(dwsvname not in dwservers)
                        self.assertTrue(rssvname not in rsservers)

                        cfdevices = self.db.get_device_exported_for_class(
                            "NXSConfigServer").value_string
                        dwdevices = self.db.get_device_exported_for_class(
                            "NXSDataWriter").value_string
                        rsdevices = self.db.get_device_exported_for_class(
                            "NXSRecSelector").value_string
                        self.assertTrue(cfdvname in cfdevices)
                        self.assertTrue(dwdvname not in dwdevices)
                        self.assertTrue(rsdvname not in rsdevices)
                        self.checkDevice(cfdvname)
                    finally:
                        try:
                            self.stopServer(cfsvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(cfsvname, cfdvname)
                            except Exception:
                                pass
                        setup = nxsetup.SetUp()
                        setup.waitServerNotRunning(
                            cfsvname, cfdvname,  adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_csjson(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True
                adminproxy = None
            else:
                adminproxy = PyTango.DeviceProxy(admin)
            if not os.path.isfile("/home/%s/.my.cnf" % cnf['user']):
                skiptest = True
            csjson = '{"host":"localhost","db":"%s",' \
                     '"use_unicode":true,'\
                     '"read_default_file":"/home/%s/.my.cnf"}' % \
                     (cnf['dbname'], cnf['user'])
            commands = [
                ('nxsetup set '
                 ' -b %s '
                 ' -m %s '
                 ' -j %s '
                 % (cnf['beamline'], cnf['masterhost'], csjson)).split(),
                ('nxsetup set '
                 ' --beamline %s '
                 ' --masterhost %s '
                 ' --csjson %s '
                 % (cnf['beamline'], cnf['masterhost'], csjson)).split(),
            ]
            for cmd in commands:
                if not skiptest:
                    try:
                        vl, er = self.runtest(cmd)
                        self.assertEqual('', er)
                        self.assertTrue(vl)
                        cfservers = self.db.get_server_list(
                            cfsvname).value_string
                        dwservers = self.db.get_server_list(
                            dwsvname).value_string
                        rsservers = self.db.get_server_list(
                            rssvname).value_string
                        self.assertTrue(cfsvname in cfservers)
                        self.assertTrue(dwsvname in dwservers)
                        self.assertTrue(rssvname in rsservers)

                        cfdevices = self.db.get_device_exported_for_class(
                            "NXSConfigServer").value_string
                        dwdevices = self.db.get_device_exported_for_class(
                            "NXSDataWriter").value_string
                        rsdevices = self.db.get_device_exported_for_class(
                            "NXSRecSelector").value_string
                        self.assertTrue(cfdvname in cfdevices)
                        if dwdvname not in dwdevices:
                            print(dwdvname)
                            print(dwdevices)
                        self.assertTrue(dwdvname in dwdevices)
                        self.assertTrue(rsdvname in rsdevices)
                        self.checkDevice(cfdvname)
                        self.checkDevice(dwdvname)
                        self.checkDevice(rsdvname)
                    finally:
                        try:
                            self.stopServer(rssvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(rssvname, rsdvname)
                            except Exception:
                                pass
                        try:
                            self.stopServer(cfsvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(cfsvname, cfdvname)
                            except Exception:
                                pass
                        try:
                            self.stopServer(dwsvname)
                        except Exception:
                            pass
                        finally:
                            try:
                                self.unregisterServer(dwsvname, dwdvname)
                            except Exception:
                                pass
                        setup = nxsetup.SetUp()
                        setup.waitServerNotRunning(
                            cfsvname, cfdvname,  adminproxy, verbose=False)
                        setup.waitServerNotRunning(
                            dwsvname, dwdvname, adminproxy, verbose=False)
                        setup.waitServerNotRunning(
                            rssvname, rsdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_all_loop(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for i in range(1):
            # print(i)
            for cnf in cnfs:
                cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                cfdvname = "%s/nxsconfigserver/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                dwdvname = "%s/nxsdatawriter/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                rsdvname = "%s/nxsrecselector/%s" % \
                    (cnf['beamline'], cnf["masterhost"])

                cfservers = self.db.get_server_list(cfsvname).value_string
                dwservers = self.db.get_server_list(dwsvname).value_string
                rsservers = self.db.get_server_list(rssvname).value_string

                dwdevices = self.db.get_device_exported_for_class(
                    "NXSDataWriter").value_string
                cfdevices = self.db.get_device_exported_for_class(
                    "NXSConfigServer").value_string
                rsdevices = self.db.get_device_exported_for_class(
                    "NXSRecSelector").value_string
                skiptest = False
                if cfsvname in cfservers:
                    skiptest = True
                if dwsvname in dwservers:
                    skiptest = True
                if rssvname in rsservers:
                    skiptest = True
                if cfdvname in cfdevices:
                    skiptest = True
                if dwdvname in dwdevices:
                    skiptest = True
                if rsdvname in rsdevices:
                    skiptest = True

                skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

                admin = nxsetup.SetUp().getStarterName(self.host)
                if not admin:
                    skiptest = True
                    adminproxy = None
                else:
                    adminproxy = PyTango.DeviceProxy(admin)

                commands = [
                    ('nxsetup set '
                     ' -b %s '
                     ' -m %s '
                     ' -u %s '
                     ' -d %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                    ('nxsetup set '
                     ' --beamline %s '
                     ' --masterhost %s '
                     ' --user %s '
                     ' --database %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                ]
                for cmd in commands:
                    if not skiptest:
                        # print(cmd)
                        try:
                            vl, er = self.runtest(cmd)
                            # print(vl)
                            # print(er)
                            self.assertEqual('', er)
                            self.assertTrue(vl)
                            cfservers = self.db.get_server_list(
                                cfsvname).value_string
                            dwservers = self.db.get_server_list(
                                dwsvname).value_string
                            rsservers = self.db.get_server_list(
                                rssvname).value_string
                            self.assertTrue(cfsvname in cfservers)
                            self.assertTrue(dwsvname in dwservers)
                            self.assertTrue(rssvname in rsservers)

                            cfdevices = self.db.get_device_exported_for_class(
                                "NXSConfigServer").value_string
                            dwdevices = self.db.get_device_exported_for_class(
                                "NXSDataWriter").value_string
                            rsdevices = self.db.get_device_exported_for_class(
                                "NXSRecSelector").value_string
                            self.assertTrue(cfdvname in cfdevices)
                            if dwdvname not in dwdevices:
                                print("%s %s" % (dwdvname, dwdevices))
                                print("%s %s" % (dwdvname, dwdevices))
                            self.assertTrue(dwdvname in dwdevices)
                            self.assertTrue(rsdvname in rsdevices)
                            self.checkDevice(cfdvname)
                            self.checkDevice(dwdvname)
                            self.checkDevice(rsdvname)
                        finally:
                            try:
                                self.stopServer(rssvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(rssvname, rsdvname)
                                except Exception:
                                    pass
                            try:
                                self.stopServer(cfsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(cfsvname, cfdvname)
                                except Exception:
                                    pass
                            try:
                                self.stopServer(dwsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(dwsvname, dwdvname)
                                except Exception:
                                    pass
                            setup = nxsetup.SetUp()
                            setup.waitServerNotRunning(
                                cfsvname, cfdvname,  adminproxy, verbose=False)
                            setup.waitServerNotRunning(
                                dwsvname, dwdvname, adminproxy, verbose=False)
                            setup.waitServerNotRunning(
                                rssvname, rsdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_all_loop2(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for _ in range(1):
            for cnf in cnfs:
                cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                cfdvname = "%s/nxsconfigserver/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                dwdvname = "%s/nxsdatawriter/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                rsdvname = "%s/nxsrecselector/%s" % \
                    (cnf['beamline'], cnf["masterhost"])

                cfservers = self.db.get_server_list(cfsvname).value_string
                dwservers = self.db.get_server_list(dwsvname).value_string
                rsservers = self.db.get_server_list(rssvname).value_string

                dwdevices = self.db.get_device_exported_for_class(
                    "NXSDataWriter").value_string
                cfdevices = self.db.get_device_exported_for_class(
                    "NXSConfigServer").value_string
                rsdevices = self.db.get_device_exported_for_class(
                    "NXSRecSelector").value_string
                skiptest = False
                if cfsvname in cfservers:
                    skiptest = True
                if dwsvname in dwservers:
                    skiptest = True
                if rssvname in rsservers:
                    skiptest = True
                if cfdvname in cfdevices:
                    skiptest = True
                if dwdvname in dwdevices:
                    skiptest = True
                if rsdvname in rsdevices:
                    skiptest = True

                skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

                admin = nxsetup.SetUp().getStarterName(self.host)
                if not admin:
                    skiptest = True
                    adminproxy = None
                else:
                    adminproxy = PyTango.DeviceProxy(admin)

                commands = [
                    ('nxsetup set '
                     ' NXSDataWriter NXSConfigServer NXSRecSelector '
                     ' -b %s '
                     ' -m %s '
                     ' -u %s '
                     ' -d %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                    ('nxsetup set '
                     ' NXSDataWriter NXSConfigServer NXSRecSelector '
                     ' --beamline %s '
                     ' --masterhost %s '
                     ' --user %s '
                     ' --database %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                ]
                for cmd in commands:
                    if not skiptest:
                        try:
                            vl, er = self.runtest(cmd)
                            self.assertEqual('', er)
                            self.assertTrue(vl)
                            cfservers = self.db.get_server_list(
                                cfsvname).value_string
                            dwservers = self.db.get_server_list(
                                dwsvname).value_string
                            rsservers = self.db.get_server_list(
                                rssvname).value_string
                            self.assertTrue(cfsvname in cfservers)
                            self.assertTrue(dwsvname in dwservers)
                            self.assertTrue(rssvname in rsservers)

                            cfdevices = self.db.get_device_exported_for_class(
                                "NXSConfigServer").value_string
                            dwdevices = self.db.get_device_exported_for_class(
                                "NXSDataWriter").value_string
                            rsdevices = self.db.get_device_exported_for_class(
                                "NXSRecSelector").value_string
                            self.assertTrue(cfdvname in cfdevices)
                            if dwdvname not in dwdevices:
                                print("%s %s" % (dwdvname, dwdevices))
                            self.assertTrue(dwdvname in dwdevices)
                            self.assertTrue(rsdvname in rsdevices)
                            self.checkDevice(cfdvname)
                            self.checkDevice(dwdvname)
                            self.checkDevice(rsdvname)
                        finally:
                            try:
                                self.stopServer(rssvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(rssvname, rsdvname)
                                except Exception:
                                    pass
                            try:
                                self.stopServer(cfsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(cfsvname, cfdvname)
                                except Exception:
                                    pass
                            try:
                                self.stopServer(dwsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(dwsvname, dwdvname)
                                except Exception:
                                    pass
                            setup = nxsetup.SetUp()
                            setup.waitServerNotRunning(
                                cfsvname, cfdvname,  adminproxy, verbose=False)
                            setup.waitServerNotRunning(
                                dwsvname, dwdvname, adminproxy, verbose=False)
                            setup.waitServerNotRunning(
                                rssvname, rsdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_nxsdatawriter_nxsconfigserver(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for _ in range(1):
            for cnf in cnfs:
                cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                cfdvname = "%s/nxsconfigserver/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                dwdvname = "%s/nxsdatawriter/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                rsdvname = "%s/nxsrecselector/%s" % \
                    (cnf['beamline'], cnf["masterhost"])

                cfservers = self.db.get_server_list(cfsvname).value_string
                dwservers = self.db.get_server_list(dwsvname).value_string
                rsservers = self.db.get_server_list(rssvname).value_string

                dwdevices = self.db.get_device_exported_for_class(
                    "NXSDataWriter").value_string
                cfdevices = self.db.get_device_exported_for_class(
                    "NXSConfigServer").value_string
                rsdevices = self.db.get_device_exported_for_class(
                    "NXSRecSelector").value_string
                skiptest = False
                if cfsvname in cfservers:
                    skiptest = True
                if dwsvname in dwservers:
                    skiptest = True
                if rssvname in rsservers:
                    skiptest = True
                if cfdvname in cfdevices:
                    skiptest = True
                if dwdvname in dwdevices:
                    skiptest = True
                if rsdvname in rsdevices:
                    skiptest = True

                skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

                admin = nxsetup.SetUp().getStarterName(self.host)
                if not admin:
                    skiptest = True
                    adminproxy = None
                else:
                    adminproxy = PyTango.DeviceProxy(admin)

                commands = [
                    ('nxsetup set NXSDataWriter NXSConfigServer '
                     ' -b %s '
                     ' -m %s '
                     ' -u %s '
                     ' -d %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                    ('nxsetup set NXSDataWriter NXSConfigServer '
                     ' --beamline %s '
                     ' --masterhost %s '
                     ' --user %s '
                     ' --database %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                ]
                for cmd in commands:
                    if not skiptest:
                        try:
                            vl, er = self.runtest(cmd)
                            self.assertEqual('', er)
                            self.assertTrue(vl)
                            cfservers = self.db.get_server_list(
                                cfsvname).value_string
                            dwservers = self.db.get_server_list(
                                dwsvname).value_string
                            rsservers = self.db.get_server_list(
                                rssvname).value_string
                            self.assertTrue(cfsvname in cfservers)
                            self.assertTrue(dwsvname in dwservers)
                            self.assertTrue(rssvname not in rsservers)

                            cfdevices = self.db.get_device_exported_for_class(
                                "NXSConfigServer").value_string
                            dwdevices = self.db.get_device_exported_for_class(
                                "NXSDataWriter").value_string
                            rsdevices = self.db.get_device_exported_for_class(
                                "NXSRecSelector").value_string
                            self.assertTrue(cfdvname in cfdevices)
                            if dwdvname not in dwdevices:
                                print("%s %s" % (dwdvname, dwdevices))
                            self.assertTrue(dwdvname in dwdevices)
                            self.assertTrue(rsdvname not in rsdevices)
                            self.checkDevice(cfdvname)
                            self.checkDevice(dwdvname)
                            # self.checkDevice(rsdvname)

                        finally:
                            try:
                                self.stopServer(cfsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(cfsvname, cfdvname)
                                except Exception:
                                    pass
                            try:
                                self.stopServer(dwsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(dwsvname, dwdvname)
                                except Exception:
                                    pass
                            setup = nxsetup.SetUp()
                            setup.waitServerNotRunning(
                                cfsvname, cfdvname,  adminproxy, verbose=False)
                            setup.waitServerNotRunning(
                                dwsvname, dwdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_nxsdatawriter(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for _ in range(1):
            for cnf in cnfs:
                cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                cfdvname = "%s/nxsconfigserver/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                dwdvname = "%s/nxsdatawriter/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                rsdvname = "%s/nxsrecselector/%s" % \
                    (cnf['beamline'], cnf["masterhost"])

                cfservers = self.db.get_server_list(cfsvname).value_string
                dwservers = self.db.get_server_list(dwsvname).value_string
                rsservers = self.db.get_server_list(rssvname).value_string

                dwdevices = self.db.get_device_exported_for_class(
                    "NXSDataWriter").value_string
                cfdevices = self.db.get_device_exported_for_class(
                    "NXSConfigServer").value_string
                rsdevices = self.db.get_device_exported_for_class(
                    "NXSRecSelector").value_string
                skiptest = False
                if cfsvname in cfservers:
                    skiptest = True
                if dwsvname in dwservers:
                    skiptest = True
                if rssvname in rsservers:
                    skiptest = True
                if cfdvname in cfdevices:
                    skiptest = True
                if dwdvname in dwdevices:
                    skiptest = True
                if rsdvname in rsdevices:
                    skiptest = True

                skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

                admin = nxsetup.SetUp().getStarterName(self.host)
                if not admin:
                    skiptest = True
                    adminproxy = None
                else:
                    adminproxy = PyTango.DeviceProxy(admin)

                commands = [
                    ('nxsetup set NXSDataWriter '
                     ' -b %s '
                     ' -m %s '
                     ' -u %s '
                     ' -d %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                    ('nxsetup set NXSDataWriter '
                     ' --beamline %s '
                     ' --masterhost %s '
                     ' --user %s '
                     ' --database %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                ]
                for cmd in commands:
                    if not skiptest:
                        try:
                            vl, er = self.runtest(cmd)
                            self.assertEqual('', er)
                            self.assertTrue(vl)
                            cfservers = self.db.get_server_list(
                                cfsvname).value_string
                            dwservers = self.db.get_server_list(
                                dwsvname).value_string
                            rsservers = self.db.get_server_list(
                                rssvname).value_string
                            self.assertTrue(cfsvname not in cfservers)
                            self.assertTrue(dwsvname in dwservers)
                            self.assertTrue(rssvname not in rsservers)

                            cfdevices = self.db.get_device_exported_for_class(
                                "NXSConfigServer").value_string
                            dwdevices = self.db.get_device_exported_for_class(
                                "NXSDataWriter").value_string
                            rsdevices = self.db.get_device_exported_for_class(
                                "NXSRecSelector").value_string
                            self.assertTrue(cfdvname not in cfdevices)
                            if dwdvname not in dwdevices:
                                print("%s %s" % (dwdvname, dwdevices))
                            self.assertTrue(dwdvname in dwdevices)
                            self.assertTrue(rsdvname not in rsdevices)
                            self.checkDevice(dwdvname)
                        finally:
                            try:
                                self.stopServer(dwsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(dwsvname, dwdvname)
                                except Exception:
                                    pass
                            setup = nxsetup.SetUp()
                            setup.waitServerNotRunning(
                                dwsvname, dwdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_nxsrecselector(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasoo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'
        for _ in range(1):
            for cnf in cnfs:
                cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                cfdvname = "%s/nxsconfigserver/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                dwdvname = "%s/nxsdatawriter/%s" % \
                    (cnf['beamline'], cnf["masterhost"])
                rsdvname = "%s/nxsrecselector/%s" % \
                    (cnf['beamline'], cnf["masterhost"])

                cfservers = self.db.get_server_list(cfsvname).value_string
                dwservers = self.db.get_server_list(dwsvname).value_string
                rsservers = self.db.get_server_list(rssvname).value_string

                dwdevices = self.db.get_device_exported_for_class(
                    "NXSDataWriter").value_string
                cfdevices = self.db.get_device_exported_for_class(
                    "NXSConfigServer").value_string
                rsdevices = self.db.get_device_exported_for_class(
                    "NXSRecSelector").value_string
                skiptest = False
                if cfsvname in cfservers:
                    skiptest = True
                if dwsvname in dwservers:
                    skiptest = True
                if rssvname in rsservers:
                    skiptest = True
                if cfdvname in cfdevices:
                    skiptest = True
                if dwdvname in dwdevices:
                    skiptest = True
                if rsdvname in rsdevices:
                    skiptest = True

                skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL

                admin = nxsetup.SetUp().getStarterName(self.host)
                if not admin:
                    skiptest = True
                    adminproxy = None
                else:
                    adminproxy = PyTango.DeviceProxy(admin)

                dwcfsvs = ['NXSDataWriter', 'NXSConfigServer']
                rssvs = ['NXSRecSelector']
                commands = [
                    ('nxsetup set '
                     ' -b %s '
                     ' -m %s '
                     ' -u %s '
                     ' -d %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                    ('nxsetup set '
                     ' --beamline %s '
                     ' --masterhost %s '
                     ' --user %s '
                     ' --database %s '
                     % (cnf['beamline'], cnf['masterhost'],
                        cnf['user'], cnf['dbname'])).split(),
                ]
                for cmd in commands:
                    if not skiptest:
                        try:
                            acmd = list(cmd)
                            acmd.extend(dwcfsvs)
                            vl, er = self.runtest(acmd)

                            cfservers = self.db.get_server_list(
                                cfsvname).value_string
                            dwservers = self.db.get_server_list(
                                dwsvname).value_string
                            rsservers = self.db.get_server_list(
                                rssvname).value_string
                            self.assertTrue(cfsvname in cfservers)
                            self.assertTrue(dwsvname in dwservers)
                            self.assertTrue(rssvname not in rsservers)

                            cfdevices = self.db.get_device_exported_for_class(
                                "NXSConfigServer").value_string
                            dwdevices = self.db.get_device_exported_for_class(
                                "NXSDataWriter").value_string
                            rsdevices = self.db.get_device_exported_for_class(
                                "NXSRecSelector").value_string
                            self.assertTrue(cfdvname in cfdevices)
                            self.assertTrue(dwdvname in dwdevices)
                            self.assertTrue(rsdvname not in rsdevices)
                            self.checkDevice(cfdvname)
                            self.checkDevice(dwdvname)
                            # self.checkDevice(rsdvname)

                            acmd = list(cmd)
                            acmd.extend(rssvs)
                            vl, er = self.runtest(acmd)
                            self.assertEqual('', er)
                            self.assertTrue(vl)
                            cfservers = self.db.get_server_list(
                                cfsvname).value_string
                            dwservers = self.db.get_server_list(
                                dwsvname).value_string
                            rsservers = self.db.get_server_list(
                                rssvname).value_string
                            self.assertTrue(cfsvname in cfservers)
                            self.assertTrue(dwsvname in dwservers)
                            self.assertTrue(rssvname in rsservers)

                            cfdevices = self.db.get_device_exported_for_class(
                                "NXSConfigServer").value_string
                            dwdevices = self.db.get_device_exported_for_class(
                                "NXSDataWriter").value_string
                            rsdevices = self.db.get_device_exported_for_class(
                                "NXSRecSelector").value_string
                            self.assertTrue(cfdvname in cfdevices)
                            self.assertTrue(dwdvname in dwdevices)
                            self.assertTrue(rsdvname in rsdevices)
                            self.checkDevice(cfdvname)
                            self.checkDevice(dwdvname)
                            self.checkDevice(rsdvname)

                        finally:
                            try:
                                self.stopServer(rssvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(rssvname, rsdvname)
                                except Exception:
                                    pass
                            try:
                                self.stopServer(cfsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(cfsvname, cfdvname)
                                except Exception:
                                    pass
                            try:
                                self.stopServer(dwsvname)
                            except Exception:
                                pass
                            finally:
                                try:
                                    self.unregisterServer(dwsvname, dwdvname)
                                except Exception:
                                    pass
                            setup = nxsetup.SetUp()
                            setup.waitServerNotRunning(
                                cfsvname, cfdvname,  adminproxy, verbose=False)
                            setup.waitServerNotRunning(
                                dwsvname, dwdvname, adminproxy, verbose=False)
                            setup.waitServerNotRunning(
                                rssvname, rsdvname, adminproxy, verbose=False)

    # comp_available test
    # \brief It tests XMLConfigurator
    def test_set_stop_start_restart(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if self.host in nxsetup.knownHosts.keys():
            dfcnf = nxsetup.knownHosts[self.host]
        else:
            dfcnf = {'beamline': 'nxs',
                     'masterhost': '%s' % self.host,
                     'user': 'tango',
                     'dbname': 'nxsconfig'}

        cnfs = [dict(dfcnf) for _ in range(4)]

        cnfs[0]['beamline'] = 'testnxs'
        cnfs[0]['masterhost'] = 'haso000'
        cnfs[1]['beamline'] = 'testnxs2'
        cnfs[1]['masterhost'] = 'hasoo12'
        cnfs[2]['beamline'] = 'test2nxs'
        cnfs[2]['masterhost'] = 'hasooo12'
        cnfs[3]['beamline'] = 'testnxs3'
        cnfs[3]['masterhost'] = 'hasoo000'

        for cnf in cnfs:
            # print(cnf)
            cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
            dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
            rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
            # acfsvname = "NXSConfigServer"
            # adwsvname = "NXSDataWriter"
            # arssvname = "NXSRecSelector"
            cfdvname = "%s/nxsconfigserver/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            dwdvname = "%s/nxsdatawriter/%s" % \
                (cnf['beamline'], cnf["masterhost"])
            rsdvname = "%s/nxsrecselector/%s" % \
                (cnf['beamline'], cnf["masterhost"])

            cfservers = self.db.get_server_list(cfsvname).value_string
            dwservers = self.db.get_server_list(dwsvname).value_string
            rsservers = self.db.get_server_list(rssvname).value_string
            # acfservers = self.db.get_server_list(acfsvname).value_string
            # adwservers = self.db.get_server_list(adwsvname).value_string
            # arsservers = self.db.get_server_list(arssvname).value_string

            dwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            cfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            rsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            skiptest = False
            if cfsvname in cfservers:
                skiptest = True
            if dwsvname in dwservers:
                skiptest = True
            if rssvname in rsservers:
                skiptest = True
            if cfdvname in cfdevices:
                skiptest = True
            if dwdvname in dwdevices:
                skiptest = True
            if rsdvname in rsdevices:
                skiptest = True
            acfdevices = self.db.get_device_exported_for_class(
                "NXSConfigServer").value_string
            adwdevices = self.db.get_device_exported_for_class(
                "NXSDataWriter").value_string
            arsdevices = self.db.get_device_exported_for_class(
                "NXSRecSelector").value_string
            if acfdevices:
                skiptest = True
            if adwdevices:
                skiptest = True
            if arsdevices:
                skiptest = True

            skiptest = skiptest or not CNFSRV or not DTWRITER or not RECSEL
            # print(skiptest)
            admin = nxsetup.SetUp().getStarterName(self.host)
            if not admin:
                skiptest = True
                adminproxy = None
            else:
                adminproxy = PyTango.DeviceProxy(admin)

        skiptests = skiptest

        if not skiptest:
            rservers = []
            try:
                for cnf in cnfs:
                    commands = [
                        ('nxsetup set '
                         ' -b %s '
                         ' -m %s '
                         ' -u %s '
                         ' -d %s '
                         % (cnf['beamline'], cnf['masterhost'],
                            cnf['user'], cnf['dbname'])).split(),
                        # ('nxsetup set '
                        #  ' --beamline %s '
                        #  ' --masterhost %s '
                        #  ' --user %s '
                        #  ' --database %s '
                        #  % (cnf['beamline'], cnf['masterhost'],
                        #     cnf['user'], cnf['dbname'])).split(),
                    ]
                    cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                    dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                    rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                    # acfsvname = "NXSConfigServer"
                    # adwsvname = "NXSDataWriter"
                    # arssvname = "NXSRecSelector"
                    cfdvname = "%s/nxsconfigserver/%s" % \
                               (cnf['beamline'], cnf["masterhost"])
                    dwdvname = "%s/nxsdatawriter/%s" % \
                               (cnf['beamline'], cnf["masterhost"])
                    rsdvname = "%s/nxsrecselector/%s" % \
                               (cnf['beamline'], cnf["masterhost"])

                    for cmd in commands:
                        try:

                            rservers.append((cfsvname, cfdvname))
                            rservers.append((dwsvname, dwdvname))
                            rservers.append((rssvname, rsdvname))
                            vl, er = self.runtest(cmd)
                            # print("VS")
                            # print(vl)
                            # print("VE")
                            self.assertEqual('', er)
                            self.assertTrue(vl)
                            cfservers = self.db.get_server_list(
                                cfsvname).value_string
                            dwservers = self.db.get_server_list(
                                dwsvname).value_string
                            rsservers = self.db.get_server_list(
                                rssvname).value_string
                            self.assertTrue(cfsvname in cfservers)
                            self.assertTrue(dwsvname in dwservers)
                            self.assertTrue(rssvname in rsservers)

                            cfdevices = self.db.get_device_exported_for_class(
                                "NXSConfigServer").value_string
                            dwdevices = self.db.get_device_exported_for_class(
                                "NXSDataWriter").value_string
                            rsdevices = self.db.get_device_exported_for_class(
                                "NXSRecSelector").value_string
                            self.assertTrue(cfdvname in cfdevices)
                            self.assertTrue(dwdvname in dwdevices)
                            self.assertTrue(rsdvname in rsdevices)
                            self.checkDevice(cfdvname)
                            self.checkDevice(dwdvname)
                            self.checkDevice(rsdvname)
                        except Exception as e:
                            print(str(e))
                            skiptests = True
                # time.sleep(5)
                if not skiptests:
                    print("TEST STOP")
                    vl, er = self.runtest(["nxsetup", "stop"])
                    self.assertEqual('', er)
                    # print("VS")
                    # print(vl)
                    # print("VE")
                    self.assertTrue(vl)
                    for cnf in cnfs:
                        # print(cnf)
                        cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                        dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                        rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                        # acfsvname = "NXSConfigServer"
                        # adwsvname = "NXSDataWriter"
                        # arssvname = "NXSRecSelector"
                        cfdvname = "%s/nxsconfigserver/%s" % \
                                   (cnf['beamline'], cnf["masterhost"])
                        dwdvname = "%s/nxsdatawriter/%s" % \
                                   (cnf['beamline'], cnf["masterhost"])
                        rsdvname = "%s/nxsrecselector/%s" % \
                                   (cnf['beamline'], cnf["masterhost"])

                        cfservers = self.db.get_server_list(
                            cfsvname).value_string
                        dwservers = self.db.get_server_list(
                            dwsvname).value_string
                        rsservers = self.db.get_server_list(
                            rssvname).value_string
                        self.assertTrue(cfsvname in cfservers)
                        self.assertTrue(dwsvname in dwservers)
                        self.assertTrue(rssvname in rsservers)

                        cfdevices = self.db.get_device_exported_for_class(
                            "NXSConfigServer").value_string
                        dwdevices = self.db.get_device_exported_for_class(
                            "NXSDataWriter").value_string
                        rsdevices = self.db.get_device_exported_for_class(
                            "NXSRecSelector").value_string
                        # print(cfdevices)
                        # print(dwdevices)
                        # print(rsdevices)
                        self.assertTrue(cfdvname not in cfdevices)
                        self.assertTrue(dwdvname not in dwdevices)
                        self.assertTrue(rsdvname not in rsdevices)
                        # self.checkDevice(cfdvname)
                        # self.checkDevice(dwdvname)
                        # self.checkDevice(rsdvname)
                    print("TEST START")
                    vl, er = self.runtest(["nxsetup", "start"])
                    self.assertEqual('', er)
                    # print("VS")
                    # print(vl)
                    # print("VE")
                    self.assertTrue(vl)
                    for cnf in cnfs:
                        # print(cnf)
                        cfsvname = "NXSConfigServer/%s" % cnf["masterhost"]
                        dwsvname = "NXSDataWriter/%s" % cnf["masterhost"]
                        rssvname = "NXSRecSelector/%s" % cnf["masterhost"]
                        # acfsvname = "NXSConfigServer"
                        # adwsvname = "NXSDataWriter"
                        # arssvname = "NXSRecSelector"
                        cfdvname = "%s/nxsconfigserver/%s" % \
                                   (cnf['beamline'], cnf["masterhost"])
                        dwdvname = "%s/nxsdatawriter/%s" % \
                                   (cnf['beamline'], cnf["masterhost"])
                        rsdvname = "%s/nxsrecselector/%s" % \
                                   (cnf['beamline'], cnf["masterhost"])

                        cfservers = self.db.get_server_list(
                            cfsvname).value_string
                        dwservers = self.db.get_server_list(
                            dwsvname).value_string
                        rsservers = self.db.get_server_list(
                            rssvname).value_string
                        self.assertTrue(cfsvname in cfservers)
                        self.assertTrue(dwsvname in dwservers)
                        self.assertTrue(rssvname in rsservers)

                        cfdevices = self.db.get_device_exported_for_class(
                            "NXSConfigServer").value_string
                        dwdevices = self.db.get_device_exported_for_class(
                            "NXSDataWriter").value_string
                        rsdevices = self.db.get_device_exported_for_class(
                            "NXSRecSelector").value_string
                        self.assertTrue(cfdvname in cfdevices)
                        self.assertTrue(dwdvname in dwdevices)
                        self.assertTrue(rsdvname in rsdevices)
                        self.checkDevice(cfdvname)
                        self.checkDevice(dwdvname)
                        self.checkDevice(rsdvname)
                    vl, er = self.runtest(["nxsetup", "stop"])
                    # print("VS")
                    # print(vl)
                    # print("VE")
            finally:
                print(rservers)
                for svname, dvname in set(rservers):
                    try:
                        self.stopServer(svname)
                    except Exception as e:
                        # print(str(e))
                        pass
                    try:
                        self.unregisterServer(svname, dvname)
                    except Exception as e:
                        # print(str(e))
                        pass
                setup = nxsetup.SetUp()
                for svname, dvname in set(rservers):
                    setup.waitServerNotRunning(
                        svname, dvname, adminproxy, verbose=False)


if __name__ == '__main__':
    unittest.main()
