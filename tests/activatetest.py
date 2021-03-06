# Written by Arno Bakker
# see LICENSE.txt for license information

import unittest

import os
import sys
import tempfile
import random
import shutil
import time
import subprocess
import urllib2
import string
import binascii
from traceback import print_exc

from testasserver import TestAsServer
from SwiftDef import SwiftDef
from swiftconn import *

DEBUG=False


class TestDirSeedFramework(TestAsServer):
    """
    Framework for multi-swarm tests.
    """

    def setUpPreSession(self):
        TestAsServer.setUpPreSession(self)
        #self.cmdport = None
        self.httpport = None
        self.scandir = "seeder2"
        self.progress = True
        
        self.setUpScanDir()

        try:
            shutil.rmtree(self.scandir)
        except:
            pass
        os.mkdir(self.scandir)
        
        # Create content
        for i in range(len(self.filelist)):
            fn = self.filelist[i][0]
            s = self.filelist[i][1]
            f = open(fn,"wb")
            data = '#' * s
            f.write(data)
            f.close()
            
            # Pre hash check and checkpoint them
            sdef = SwiftDef()
            sdef.add_content(fn)
            sdef.finalize(self.binpath)
            self.filelist[i][2] = sdef.get_id() # save roothash

        for i in range(len(self.filelist)):
            print >>sys.stderr,"test: Configured from filelist",binascii.hexlify(self.filelist[i][2])


    def setUpScanDir(self):
        self.filelist = []
        # Minimum 1 entry
        # DO NOT MODIFY THESE ENTRIES without adjusting tests, e.g. requesttest.py
        self.filelist.append([os.path.join(self.scandir,"anita.ts"), 1234, None])
        self.filelist.append([os.path.join(self.scandir,"bill.ts"),  200487, None])
        self.filelist.append([os.path.join(self.scandir,"claire.ts"),65535, None])

    def setUpPostSession(self):
        TestAsServer.setUpPostSession(self)
        
    def tearDown(self):
        TestAsServer.tearDown(self)
        time.sleep(1)
        try:
            shutil.rmtree(self.scandir)
        except:
            pass


class TestDirSeed(TestDirSeedFramework):
    """
    Basic test for the SwarmManager activation code to see if it found the
    swarms in the scandir.
    """

    def test_connect_one(self):
        myaddr = ("127.0.0.1",15353)
        hisaddr = ("127.0.0.1",self.listenport)
        
        # last
        swarmid = self.filelist[len(self.filelist)-1][2]
        
        s = SwiftConnection(myaddr,hisaddr,swarmid)
        d = s.recv()
        responded = False
        while True:
            msg = d.get_message()
            if msg is None:
                break 
            if msg.get_id() == MSG_ID_HANDSHAKE:
                print >>sys.stderr,"test: Parsed",`msg`
                responded = True
                
        self.assertTrue(responded)
        
        time.sleep(10)
    

    def test_connect_reactivate(self):
        
        self.test_connect_one()
        
        print >>sys.stderr,"test: Now sleeping so swift deactivates swarm"
        time.sleep(60)
        # Should be deactivated
        
        print >>sys.stderr,"test: Testing if reactivate works"
        self.test_connect_one()

    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirSeed))
    
    return suite


def main():
    unittest.main(defaultTest='test_suite',argv=[sys.argv[0]])

if __name__ == "__main__":
    main()

            