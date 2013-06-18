#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2013 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
## \package ndtstools tools for ndts
## \file CollCompCreator.py
# datasource creator

from simpleXML import *

from optparse import OptionParser

PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass

## generates device names
# \param prefix device name prefix
# \param first first device index
# \param last last device index
# \returns device names
def generateDeviceNames(prefix, first, last):
    names = []
    if prefix.strip():
        for i in range (first, last+1):
            names.append(prefix + ("0" if len(str(i)) == 1 else "" ) 
                            + str(i))
    return names

## opens connection to the configuration server
# \param configuration server device
# \returns configuration server proxy
def openServer(device):
    found = False
    cnt = 0
    ## spliting character
    try:
        ## configuration server proxy
        cnfServer = PyTango.DeviceProxy(device)
    except Exception, e:
        found = True
            
    if found:
        sys.stderr.write("Error: Cannot connect into configuration server: %s\n"% device)
        sys.stderr.flush()
        sys.exit(0)

    while not found and cnt < 1000:
        if cnt > 1:
            time.sleep(0.01)
        try:
            if cnfServer.state() != PyTango.DevState.RUNNING:
                found = True
        except Exception,e:
            time.sleep(0.01)
            found = False
        cnt +=1
        
    if not found:
        sys.stderr.write("Error: Setting up %s takes to long\n"% device)
        sys.stderr.flush()
        sys.exit(0)

            
    cnfServer.Open()
    return cnfServer    

## stores components
# \param name component name
# \param xml component xml string
# \param server configuration server
def storeComponent(name, xml, server):
    proxy = openServer(server)
    proxy.XMLString = str(xml)
    proxy.StoreComponent(str(name))
    

## creates component file
# \param name device name
# \param directory output file directory
# \param fileprefix file name prefix
# \param collection collection group name
# \param strategy field strategy
# \param nexusType nexus Type of the field 
# \param units field units
# \param server configuration server
def createComponent(name, directory, fileprefix, collection,
                    strategy, nexusType, units, links, server):
    df = XMLFile("%s/%s%s.xml" %(directory, fileprefix ,name))  
    en = NGroup(df, "entry", "NXentry")
    ins = NGroup(en, "instrument", "NXinstrument")
    col = NGroup(ins, collection, "NXcollection")
    f = NField(col, name, nexusType)
    f.setStrategy(strategy)

    if units.strip():
        f.setUnits(units.strip())

    if links:    
        f.setText("$datasources.%s" % name)
    else:
        sr = NDSource(f)
        sr.initClient(name, name)

    if server:
        xml = df.prettyPrint()
        storeComponent(name, xml, server)
    else: 
        df.dump()
           

           
## provides XMLConfigServer device names
# \returns list of the XMLConfigServer device names
def getServers():
    try:
        db=PyTango.Database()
    except:
        sys.stderr.write(
            "Error: Cannot connect into the tango database on host: \n    %s \n "% os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""
        
    servers = db.get_device_exported_for_class("XMLConfigServer").value_string
    return servers

## provides XMLConfigServer device name if only one or error in the other case
# \returns XMLConfigServer device name or empty string if error appears
def checkServer():
    servers = getServers()
    if not servers:
        sys.stderr.write(
            "Error: No XMLConfigServer on current host running. \n\n"
            +"    Please specify the server from the other host. \n\n")
        sys.stderr.flush()
        return ""
    if len(servers) > 1:
        sys.stderr.write(
            "Error: More than on XMLConfigServer on current host running. \n\n"
            +"    Please specify the server:\n        %s\n\n"% "\n        ".join(servers))
        sys.stderr.flush()
        return ""
    return servers[0]

## the main function
def main():
    ## usage example
    usage = "usage: %prog [options] [name1] [name2]"
    ## option parser
    parser = OptionParser(usage=usage)

    parser.add_option("-p", "--device-prefix", type="string",
                      help="device prefix, i.e. exp_c",
                      dest="device", default="")
    parser.add_option("-f", "--first",
                      help="first index",
                      dest="first", default="1")
    parser.add_option("-l", "--last",
                      help="last index",
                      dest="last", default=None)

    parser.add_option("-d", "--directory", type="string",
                      help="output component directory",
                      dest="directory", default=".")
    parser.add_option("-x", "--file-prefix", type="string",
                      help="file prefix, i.e. counter",
                      dest="file", default="")

    parser.add_option("-c", "--collection", type="string",
                      help="collection name",
                      dest="collection", default="collection")


    parser.add_option("-s", "--strategy", type="string",
                      help="writing strategy, i.e. STEP, INIT, FINAL, POSTRUN",
                      dest="strategy", default="STEP")
    parser.add_option("-t", "--type", type="string",
                      help="nexus type of the field",
                      dest="type", default="NX_FLOAT")
    parser.add_option("-u", "--units", type="string",
                      help="nexus units of the field",
                      dest="units", default="")


    parser.add_option("-k","--links",  action="store_true",
                      default=False, dest="links", 
                      help="create datasource links")


    parser.add_option("-b","--database",  action="store_true",
                      default=False, dest="database", 
                      help="store components in Coinfiguration Server database")

    parser.add_option("-r","--server", dest="server", 
                      help="configuration server device name")



    (options, args) = parser.parse_args()


    if options.database and not options.server:
        if not PYTANGO:
            print  >> sys.stderr, "CollCompCreator No PyTango installed\n"
            parser.print_help()
            sys.exit(255)
            
        options.server = checkServer()
        if not options.server:
            parser.print_help()
            print ""
            sys.exit(0)

    if options.database:    
        print "CONFIG SERVER:", options.server
    else: 
        print "OUTPUT DIRECTORY:", options.directory
            


    aargs = []
    if options.device.strip():
        try:    
            first = int(options.first)
        except:
            print  >> sys.stderr, "CollCompCreator Invalid --first parameter\n"
            parser.print_help()
            sys.exit(255)


        try:    
            last = int(options.last)
        except:
            print  >> sys.stderr, "CollCompCreator Invalid --last parameter\n"
            parser.print_help()
            sys.exit(255)




        aargs = generateDeviceNames(options.device, first, last)
        
    args += aargs
    if not len(args):
        parser.print_help()
        sys.exit(255)

    for name in args:
        if not options.database:
            print "CREATING: %s%s.xml" % (options.file, name)
        else:
            print "STORING: %s" % (name)
        createComponent(name, options.directory, options.file,
                        options.collection, 
                        options.strategy,
                        options.type,
                        options.units,
                        options.links,
                        options.server if options.database else None)
    
        


if __name__ == "__main__":
    main()