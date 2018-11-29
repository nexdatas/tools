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
# \file runtest.py
# the unittest runner
#

import os
import sys

try:
    import PyTango
    # if module PyTango avalable
    PYTANGO_AVAILABLE = True
except ImportError as e:
    PYTANGO_AVAILABLE = False
    print("PyTango is not available: %s" % e)

try:
    try:
        __import__("pni.io.nx.h5")
    except Exception:
        __import__("pni.nx.h5")
    # if module pni avalable
    PNI_AVAILABLE = True
except ImportError as e:
    PNI_AVAILABLE = False
    print("pni is not available: %s" % e)

try:
    __import__("h5py")
    # if module pni avalable
    H5PY_AVAILABLE = True
except ImportError as e:
    H5PY_AVAILABLE = False
    print("h5py is not available: %s" % e)

try:
    __import__("pninexus.h5cpp")
    # if module pni avalable
    H5CPP_AVAILABLE = True
except ImportError as e:
    H5CPP_AVAILABLE = False
    print("h5cpp is not available: %s" % e)
except SystemError as e:
    H5CPP_AVAILABLE = False
    print("h5cpp is not available: %s" % e)


import unittest

import NXSToolsTest

if not PNI_AVAILABLE and not H5PY_AVAILABLE and not H5CPP_AVAILABLE:
    raise Exception("Please install h5py, h5cpp or pni")

# if PNI_AVAILABLE:
# if H5PY_AVAILABLE:
# if PNI_AVAILABLE and H5PY_AVAILABLE:


# list of available databases
DB_AVAILABLE = []

try:
    import MySQLdb
    # connection arguments to MYSQL DB
    args = {}
    args["db"] = 'tango'
    args["host"] = 'localhost'
    args["read_default_file"] = '/etc/mysql/my.cnf'
    # inscance of MySQLdb
    mydb = MySQLdb.connect(**args)
    mydb.close()
    DB_AVAILABLE.append("MYSQL")
except Exception as e1:
    try:
        import MySQLdb
        from os.path import expanduser
        home = expanduser("~")
        # connection arguments to MYSQL DB
        cnffile = '%s/.my.cnf' % home
        args2 = {
            'host': u'localhost', 'db': u'tango',
            'read_default_file': '%s/.my.cnf' % home,
            'use_unicode': True}
        # inscance of MySQLdb
        mydb = MySQLdb.connect(**args2)
        mydb.close()
        DB_AVAILABLE.append("MYSQL")
    except ImportError as e2:
        print("MYSQL not available: %s %s" % (e1, e2))
    except Exception as e2:
        print("MYSQL not available: %s %s" % (e1, e2))
    except Exception:
        print("MYSQL not available")


try:
    import psycopg2
    # connection arguments to PGSQL DB
    args = {}
    args["database"] = 'mydb'
    # inscance of psycog2
    pgdb = psycopg2.connect(**args)
    pgdb.close()
    DB_AVAILABLE.append("PGSQL")
except ImportError as e:
    print("PGSQL not available: %s" % e)
except Exception as e:
    print("PGSQL not available: %s" % e)
except Exception:
    print("PGSQL not available")


try:
    import cx_Oracle
    # pwd
    passwd = open(
        '%s/pwd' % os.path.dirname(NXSToolsTest.__file__)).read()[:-1]

    # connection arguments to ORACLE DB
    args = {}
    args["dsn"] = (
        "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=dbsrv01.desy.de)"
        "(PORT=1521))(LOAD_BALANCE=yes)(CONNECT_DATA=(SERVER=DEDICATED)"
        "(SERVICE_NAME=desy_db.desy.de)(FAILOVER_MODE=(TYPE=NONE)"
        "(METHOD=BASIC)(RETRIES=180)(DELAY=5))))")
    args["user"] = "read"
    args["password"] = passwd
    # inscance of cx_Oracle
    ordb = cx_Oracle.connect(**args)
    ordb.close()
    DB_AVAILABLE.append("ORACLE")
except ImportError as e:
    print("ORACLE not available: %s" % e)
except Exception as e:
    print("ORACLE not available: %s" % e)
except Exception:
    print("ORACLE not available")

db = PyTango.Database()

if PNI_AVAILABLE:
    import FileWriterTest
    import PNIWriterTest
    import NXSCollectPNITest
if H5PY_AVAILABLE:
    import H5PYWriterTest
    import FileWriterH5PYTest
    import NXSCollectH5PYTest
if H5CPP_AVAILABLE:
    import H5CppWriterTest
    import FileWriterH5CppTest
    import NXSCollectH5CppTest
if PNI_AVAILABLE and H5PY_AVAILABLE:
    import FileWriterPNIH5PYTest
# if PNI_AVAILABLE and H5CPP_AVAILABLE:
#     import FileWriterPNIH5CppTest

if H5CPP_AVAILABLE or H5PY_AVAILABLE or H5CPP_AVAILABLE:
    import NXSCollectTest


if PYTANGO_AVAILABLE:
    if "MYSQL" in DB_AVAILABLE:
        import NXSConfigTest


# main function
def main():

    # test suit
    suite = unittest.TestSuite()

    if PNI_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(FileWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(PNIWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectPNITest))

    if H5PY_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(FileWriterH5PYTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5PYWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectH5PYTest))
    if H5CPP_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterH5CppTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5CppWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectH5CppTest))
    if PNI_AVAILABLE and H5PY_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterPNIH5PYTest))

    if H5CPP_AVAILABLE or H5PY_AVAILABLE or H5CPP_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectTest))

    if PYTANGO_AVAILABLE:
        if "MYSQL" in DB_AVAILABLE:
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSConfigTest))

    # test runner
    runner = unittest.TextTestRunner()
    # test result
    result = runner.run(suite).wasSuccessful()
    sys.exit(not result)

    #   if ts:
    #       ts.tearDown()


if __name__ == "__main__":
    main()
