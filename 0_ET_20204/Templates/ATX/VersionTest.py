# -*- coding: utf-8 -*-

'''
Created on 28.10.2014

@author: Philipp
'''

import unittest

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass
from .Version import GetDownloadLinkForATXMako


class VersionTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def GetClientVersion(self):
        from constantsVersionInfo import GetFullName, GetVersionString
        return u"{0}__v{1}".format(GetFullName().replace(" ", "_"), GetVersionString())

    def testGetDownloadLinkForATXMakoWithoutContextPath(self):
        # ARRANGE + ACT
        link = GetDownloadLinkForATXMako(False, u"localhost", 8080, u"", u"")
        # ASSERT
        self.assertEqual(u"http://localhost:8080/api/download-file/ATXGenerator?clientVersion={0}&"
                         u"authKey=".format(self.GetClientVersion()), link)

    def testGetDownloadLinkForATXMakoWithoutHttps(self):
        # ARRANGE + ACT
        link = GetDownloadLinkForATXMako(False, u"localhost", 8080, u"ttstm", u"MyKey")
        # ASSERT
        self.assertEqual(u"http://localhost:8080/ttstm/api/download-file/ATXGenerator?"
                         u"clientVersion={0}&authKey=MyKey".format(self.GetClientVersion()), link)

    def testGetDownloadLinkForATXMakoWithHttps(self):
        # ARRANGE + ACT
        link = GetDownloadLinkForATXMako(True, u"localhost", 8080, u"ttstm", u"Key")
        # ASSERT
        self.assertEqual(u"https://localhost:8080/ttstm/api/download-file/ATXGenerator?"
                         u"clientVersion={0}&authKey=Key".format(self.GetClientVersion()), link)


if __name__ == "__main__":
    unittest.main()
