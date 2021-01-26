# -*- coding: utf-8 -*-

import unittest

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass

from .TraceMetadata import SplitNameAndFormatDetails


class TraceMetadataTest(unittest.TestCase):

    def testGetNameAndFormatDetails(self):
        self.assertEqual((None, None), SplitNameAndFormatDetails(None))
        self.assertEqual((None, None), SplitNameAndFormatDetails(""))
        self.assertEqual(("ABC", ""), SplitNameAndFormatDetails("ABC"))
        self.assertEqual(("ABC (", ""), SplitNameAndFormatDetails("ABC ("))
        self.assertEqual(("ABC )", ""), SplitNameAndFormatDetails("ABC )"))
        self.assertEqual(("ABC", "XYZ"), SplitNameAndFormatDetails("ABC (XYZ)"))
        self.assertEqual(("ABC", "XYZ (xyz)"), SplitNameAndFormatDetails("ABC (XYZ (xyz))"))
        self.assertEqual(("ABC(XYZ", "xyz)"), SplitNameAndFormatDetails("ABC(XYZ (xyz))"))
        self.assertEqual(("", ""), SplitNameAndFormatDetails(" ()"))
