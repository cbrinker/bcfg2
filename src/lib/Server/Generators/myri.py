#!/usr/bin/env python

from socket import getaddrinfo

from Bcfg2.Server.Generator import Generator
from Bcfg2.Server.Types import ConfigFile

class myri(Generator):
    __name__ = 'myri'
    __version__ = '$Id$'
    __author__ = 'bcfg-dev@mcs.anl.gov'

    filedata="DEVICE=myri0\nIPADDR=%s\nBROADCAST=140.221.69.255\nNETMASK=255.255.254.0\nNETWORK=140.221.68.0\nONBOOT=yes\nBOOTPROTO=none"

    def __setup__(self):
        self.__provides__ = {'ConfigFile':{'/etc/sysconfig/network-scripts/ifcfg-myri0':self.build_myri}}

    def build_myri(self,name,metadata):
        client = metadata.hostname
        (ip,port) = getaddrinfo(client,None)[0][4]
        subnet = int(ip.split('.')[2])+2
        lo = ip.split('.')[3]
        addr = "140.221.%s.%s"%(subnet,lo)
        return ConfigFile('/etc/sysconfig/network-scripts/ifcfg-myri0','root','root','0755',self.filedata%(addr))
