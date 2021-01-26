# -*- coding: utf-8 -*-

'''
Created on 29.10.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''
import sys
import unittest
import tempfile
import shutil
import os
from datetime import datetime
import zipfile
from xml.etree import ElementTree

from hashlib import md5
from mockito import mock, when, any, eq

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass

from constants import RESULT_LIST

import gettext
gettext.NullTranslations().install()

from tts.core.report.db.ReportItemComment import ReportItemComment

from .Utils import (CompareGlobalConstantsLists, GetExtendedWindowsPath,
                    MakeCompressedZip, GetNextShortNameInList, GetIsoDate, FilterSUCCESS,
                    AutoShortnameUnderscoreCut, FilterShortName, FilterUniqueShortName,
                    SplitVersionString, GetVerdictWeighting, GroupReviewsPerPackage,
                    ReplaceAsciiCtrlChars, GetReviewsForReportItem, DefectClassException)


class UtilsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(UtilsTest, cls).setUpClass()
        try:
            cls.__tmpDir = tempfile.mkdtemp(u'_UtilsTest')
        except BaseException:
            cls.tearDownClass()

    @classmethod
    def tearDownClass(cls):
        super(UtilsTest, cls).tearDownClass()
        shutil.rmtree(cls.__tmpDir, True)

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testGetIsoDateWinterTime(self):
        # ARRANGE
        # https://www.worldtimebuddy.com/
        winterTime = datetime(2016, 3, 10, 12, 42)
        # ACT
        result = GetIsoDate(winterTime)
        # ASSERT
        self.assertEqual(u"2016-03-10T11:42:00+00:00", result)

    def testGetIsoDateSummerTime(self):
        # ARRANGE
        # https://www.worldtimebuddy.com/
        summerTime = datetime(2016, 4, 10, 12, 42)
        # ACT
        result = GetIsoDate(summerTime)
        # ASSERT
        self.assertEqual(u"2016-04-10T10:42:00+00:00", result)

    def testEqualDicts(self):
        # ARRANGE
        listA = [{u'SHORT-NAME': u'EqualDicts', u'VALUE': u'EqualValues'}]
        listB = listA

        # ACT
        compareResult = CompareGlobalConstantsLists(listA, listB)

        # ASSERT
        self.assertTrue(compareResult, u'Die zwei Listen sollten gleich sein.')

    def testDiffKeyCount(self):
        # ARRANGE
        listA = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues'}]
        listB = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues'}]

        # ACT
        compareResult = CompareGlobalConstantsLists(listA, listB)

        # ASSERT
        self.assertFalse(compareResult, u'Die zwei Listen sollten nicht gleich sein.')

    def testDiffConsecutivelyOrderedKeys(self):
        # ARRANGE
        listA = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_3', u'VALUE': u'EqualValues'}]
        listB = [{u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_3', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_4', u'VALUE': u'EqualValues'}]

        # ACT
        compareResultA = CompareGlobalConstantsLists(listA, listB)
        compareResultB = CompareGlobalConstantsLists(listB, listA)

        # ASSERT
        self.assertFalse(compareResultA, u'Die zwei Listen sollten nicht gleich sein.')
        self.assertFalse(compareResultB, u'Die zwei Listen sollten nicht gleich sein.')

    def testDiffShuffledKeys(self):
        # ARRANGE
        listA = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_3', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues'}]
        listB = [{u'SHORT-NAME': u'NonEqualDicts_4', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues'}]

        # ACT
        compareResultA = CompareGlobalConstantsLists(listA, listB)
        compareResultB = CompareGlobalConstantsLists(listB, listA)

        # ASSERT
        self.assertFalse(compareResultA, u'Die zwei Listen sollten nicht gleich sein.')
        self.assertFalse(compareResultB, u'Die zwei Listen sollten nicht gleich sein.')

    def testNonDiffValues(self):
        # ARRANGE
        listA = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_3', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues'}]
        listB = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues'},
                 {u'SHORT-NAME': u'NonEqualDicts_3', u'VALUE': u'EqualValues'}]

        # ACT
        compareResultA = CompareGlobalConstantsLists(listA, listB)
        compareResultB = CompareGlobalConstantsLists(listB, listA)

        # ASSERT
        self.assertTrue(compareResultA, u'Die zwei Listen sollten gleich sein.')
        self.assertTrue(compareResultB, u'Die zwei Listen sollten gleich sein.')

    def testDiffValues(self):
        # ARRANGE
        listA = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues_A'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues_B'},
                 {u'SHORT-NAME': u'NonEqualDicts_3', u'VALUE': u'EqualValues_C'}]
        listB = [{u'SHORT-NAME': u'NonEqualDicts_1', u'VALUE': u'EqualValues_A'},
                 {u'SHORT-NAME': u'NonEqualDicts_2', u'VALUE': u'EqualValues_C'},
                 {u'SHORT-NAME': u'NonEqualDicts_3', u'VALUE': u'EqualValues_D'}]

        # ACT
        compareResultA = CompareGlobalConstantsLists(listA, listB)
        compareResultB = CompareGlobalConstantsLists(listB, listA)

        # ASSERT
        self.assertFalse(compareResultA, u'Die zwei Listen sollten nicht gleich sein.')
        self.assertFalse(compareResultB, u'Die zwei Listen sollten nicht gleich sein.')

    @unittest.skipIf(sys.platform != 'win32', 'only for Windows')
    def testGetExtendedWindowsUNCPath(self):
        # ARRANGE
        expected = u"\\\\?\\UNC\\tt-ddvs15\\CORE_BaseTest\\report\\BasePackageTest"
        sourcePath = r"\\tt-ddvs15\CORE_BaseTest\report\BasePackageTest"
        # ACT
        extPath = GetExtendedWindowsPath(sourcePath)
        # ASSERT
        self.assertEqual(expected, extPath)

    def testGetExtendedWindowsPath(self):
        # ARRANGE
        expected = u"\\\\?\\C:\\Daten\\report\\BasePackageTest"
        sourcePath = r"C:\Daten\report\BasePackageTest"
        # ACT
        extPath = GetExtendedWindowsPath(sourcePath)
        # ASSERT
        self.assertEqual(expected, extPath)

    @unittest.skipIf(sys.platform != 'win32', 'currently only for Windows')
    def testMakeCompressedZip(self):
        # ARRANGE
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "dummy.tmp"), "wb") as source:
                for dummy in range(1000000):
                    source.write(b'%i' % (dummy % 1000))

            target = os.path.join(tmpdir, 'dummy.zip')

            # ACT
            MakeCompressedZip([source.name], target)
            # ASSERT
            self.assertTrue(os.path.exists(target), u'Die Zieldatei sollte existieren.')
            self.assertTrue(zipfile.is_zipfile(target),
                            u'Die erzeugte Datei sollte eine ZIP Datei sein.')
            with zipfile.ZipFile(target) as zf:
                infos = zf.infolist()
                self.assertEqual(len(infos), 1)
                info = infos[0]

                self.assertLess(info.compress_size, info.file_size,
                                u'Die entpackte Größe muss größer als die Komprimierte sein.')

                if sys.version_info > (3,):
                    # Zip muss reproduzierbar sein (Metadaten prüfen)
                    self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                    self.assertEqual(info.external_attr, 0o600 << 16)
                    self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)

            if sys.version_info > (3,):
                # Zip muss reproduzierbar sein, damit TEST-GUIDE immer gleichen Dateihash ermittelt
                with open(target, "rb") as zf:
                    self.assertEqual(md5(zf.read()).hexdigest(), "9adb30b2a2ade77336ba12d7cab4bf4a")

    def testNextShortNameInListHasOne(self):
        # ARRANGE
        dummyList = [{u'SHORT-NAME': u'foo_0'}, {u'SHORT-NAME': u'bar'}]

        # ACT
        result = GetNextShortNameInList(dummyList, u'foo')

        # ASSERT
        self.assertEqual(u'foo_1', result, u'Der Name sollte "foo_1" sein.')

    def testNextShortNameInListHasNone(self):
        # ARRANGE
        dummyList = [{u'SHORT-NAME': u'bar'}]

        # ACT
        result = GetNextShortNameInList(dummyList, u'foo')

        # ASSERT
        self.assertEqual(u'foo_0', result, u'Der Name sollte "foo_0" sein.')

    def testNextShortNameInListHasMany(self):
        # ARRANGE
        dummyList = [{u'SHORT-NAME': u'foo_0'}, {u'SHORT-NAME': u'foo_1'}, {u'SHORT-NAME': u'foo_2'},
                     {u'SHORT-NAME': u'foo_3'}, {u'SHORT-NAME': u'foo_4'}, {u'SHORT-NAME': u'foo_5'}]

        # ACT
        result = GetNextShortNameInList(dummyList, u'foo')

        # ASSERT
        self.assertEqual(u'foo_6', result, u'Der Name sollte "foo_6" sein.')

    def testAutoShortnameUnderscoreCutOnNotRequiredCut(self):
        # ARRANGE
        shortname = u"jo_jo_jo_Ba"
        maxLength = 11

        # ACT
        result = AutoShortnameUnderscoreCut(shortname, maxLength)

        # ASSERT
        self.assertEqual(shortname, result)

    def testAutoShortnameUnderscoreCutOnNoUnderscore(self):
        # ARRANGE
        shortname = u"jojojoBa"
        maxLength = 4

        # ACT
        result = AutoShortnameUnderscoreCut(shortname, maxLength)

        # ASSERT
        self.assertEqual(shortname, result)

    def testAutoShortnameUnderscoreCut(self):
        # ARRANGE
        shortname = u"jo_jo_jo_Ba"
        maxLength = 10

        # ACT
        result = AutoShortnameUnderscoreCut(shortname, maxLength)

        # ASSERT
        self.assertEqual(u'jo_jo_joBa', result)

    def testSplitVersionString(self):
        # ARRANGE
        version = u"5.6.1.55366"

        # ACT
        result = SplitVersionString(version)

        # ASSERT
        self.assertEqual((u'5', u'6', u'1', u'55366'), result)

    def testSplitVersionStringOnNoneString(self):
        # ARRANGE
        version = None

        # ACT
        result = SplitVersionString(version)

        # ASSERT
        self.assertEqual((u'0', u'0', u'0', u'0'), result)

    def testSplitVersionStringInNewYearFormat(self):
        # ARRANGE
        version = u"2020.1.95870"

        # ACT
        result = SplitVersionString(version)

        # ASSERT
        self.assertEqual((u'2020', u'1', u'0', u'95870'), result)

    def testSplitVersionStringOnInvalidString(self):
        # ARRANGE
        version = u"5.6.1"

        # ACT
        result = SplitVersionString(version)

        # ASSERT
        self.assertEqual((u'0', u'0', u'0', u'0'), result)

    def testFilterShortName(self):
        # ARRANGE
        packageName = u"__7MyPäckage_"

        # ACT
        result = FilterShortName(packageName)

        # ASSERT
        self.assertEqual(u"i7MyPaeckage_", result)

    def testFilterUniqueShortName(self):
        # ARRANGE
        packageName = u"MyPackage_"

        # ACT
        result = FilterUniqueShortName(packageName, 2)

        # ASSERT
        self.assertEqual(u"MyPackage_2", result)

    def testGetVerdictWeighting(self):
        # ARRANGE
        # ACT
        checkWeighting = -1
        for each in RESULT_LIST:
            result = GetVerdictWeighting(FilterSUCCESS(each))

            # ASSERT
            self.assertTrue(checkWeighting < result,
                            u"Die Gewichtung des Results sollte kleiner als sein Vorgänger sein!")

            checkWeighting = result

    def testGroupReviewsPerPackage(self):
        # ARRANGE

        from .Review import Review

        reportCommentMock1 = mock()
        when(reportCommentMock1).GetText().thenReturn(u'Comment')
        when(reportCommentMock1).GetAuthor().thenReturn(u'WerkOhneNamen')
        when(reportCommentMock1).GetOverriddenResult().thenReturn(u'SUCCESS')
        when(reportCommentMock1).GetTimestamp().thenReturn(2)
        review1 = Review(reportCommentMock1, "Level 1", 1, 1, None)

        reportCommentMock2 = mock()
        when(reportCommentMock2).GetText().thenReturn(u'Comment')
        when(reportCommentMock2).GetAuthor().thenReturn(u'WerkOhneNamen')
        when(reportCommentMock2).GetOverriddenResult().thenReturn(u'FAILED')
        when(reportCommentMock2).GetTimestamp().thenReturn(3)
        review2 = Review(reportCommentMock2, "Level 1", 1, 2, None)

        reportCommentMock3 = mock()
        when(reportCommentMock3).GetText().thenReturn(u'Comment')
        when(reportCommentMock3).GetAuthor().thenReturn(u'WerkOhneNamen')
        when(reportCommentMock3).GetOverriddenResult().thenReturn(u'ERROR')
        when(reportCommentMock3).GetTimestamp().thenReturn(1)
        review3 = Review(reportCommentMock3, "Level 1", 1, 3, None)

        reportCommentMock4 = mock()
        when(reportCommentMock4).GetText().thenReturn(u'Comment')
        when(reportCommentMock4).GetAuthor().thenReturn(u'WerkOhneNamen')
        when(reportCommentMock4).GetOverriddenResult().thenReturn(u'ERROR')
        when(reportCommentMock4).GetTimestamp().thenReturn(1)
        review4 = Review(reportCommentMock4, "Level 1", 2, 3, None)

        # ACT
        result = GroupReviewsPerPackage([review1, review3, review4, review2])

        # ASSERT
        self.assertEqual("ERROR", result.pop(0).GetRevaluationVerdict())
        self.assertEqual("FAILED", result.pop(0).GetRevaluationVerdict())
        self.assertEqual("PASSED", result.pop(0).GetRevaluationVerdict())
        self.assertEqual(0, len(result))

    def testReplaceAsciiCtrlCharsWitNoneValue(self):
        # ARRANGE
        inputVal = None
        # ACT
        result = ReplaceAsciiCtrlChars(inputVal)
        # ASSERT
        self.assertEqual(None, result)

    def testReplaceAsciiCtrlChars(self):
        # ARRANGE
        inputVal = 'C:\\Tmp\x07pple\x08at\x0cood\new\\New\reference\title\\upper\\Upp\x0bolvo\x0001'
        # ACT
        result = ReplaceAsciiCtrlChars(inputVal)
        # ASSERT
        self.assertEqual('C:\\Tmpppleatoodew\\Neweferenceitle\\upper\\Uppolvo01', result)

    def testReplaceAsciiCtrlFromNumber(self):
        # ARRANGE
        inputVal = 23
        # ACT
        result = ReplaceAsciiCtrlChars(inputVal)
        # ASSERT
        self.assertEqual("23", result)

    def testReplaceAsciiCtrlFromList(self):
        # ARRANGE
        inputVal = ["test", "\\Upp\x0bolvo\x0001"]
        # ACT
        result = ReplaceAsciiCtrlChars(inputVal)
        # ASSERT
        self.assertEqual("['test', '\\\\Upp\\x0bolvo\\x0001']", result)

    def testGetReviewsForReportItem_Defect(self):
        # ARRANGE
        reportItem = mock()
        when(reportItem).GetSrcIndex().thenReturn(1)
        when(reportItem).GetName().thenReturn(u'Name')
        when(reportItem).GetActivity().thenReturn(u'abc')
        when(reportItem).GetId().thenReturn(1)
        when(reportItem).GetAbortCode().thenReturn(u'')
        when(reportItem).GetExecLevel().thenReturn(1)
        
        reviewDefect = u'Fehlerklasse'
        
        review = ReportItemComment(1, 1, u'Author', datetime.now().timestamp(), u'Kommentar |{0}|'.format(reviewDefect), u'SUCCESS')

        reportApi = mock()
        when(reportApi).IterUserComments(any()).thenReturn( item for item in [review] )
        when(reportApi).GetSetting(eq(u'detectReviewDefects')).thenReturn(reviewDefect)
        
        # ACT
        result = GetReviewsForReportItem(reportApi, reportItem)
        
        # ASSERT
        result[0].SetTestCaseRef('ref')
        xml = ElementTree.tostring(result[0].GetXml(), encoding='unicode', method='xml')
        self.assertIn(u'<DEFECT>{0}</DEFECT>'.format(reviewDefect), xml)

    def testGetReviewsForReportItem_OnlyOneDefect(self):
        # ARRANGE
        reportItem = mock()
        when(reportItem).GetSrcIndex().thenReturn(1)
        when(reportItem).GetName().thenReturn(u'Name')
        when(reportItem).GetActivity().thenReturn(u'abc')
        when(reportItem).GetId().thenReturn(1)
        when(reportItem).GetAbortCode().thenReturn(u'')
        when(reportItem).GetExecLevel().thenReturn(1)
        
        reviewDefect = u'Fehlerklasse1;Fehlerklasse2'
        
        review = ReportItemComment(1, 1, u'Author', datetime.now().timestamp(), u'Kommentar |Fehlerklasse1| |Fehlerklasse2|', u'SUCCESS')

        reportApi = mock()
        when(reportApi).IterUserComments(any()).thenReturn( item for item in [review] )
        when(reportApi).GetSetting(eq(u'detectReviewDefects')).thenReturn(reviewDefect)
        
        # ACT + ASSERT
        with self.assertRaises(DefectClassException):
            GetReviewsForReportItem(reportApi, reportItem)

    def testGetReviewsForReportItem_Tags(self):
        # ARRANGE
        reportItem = mock()
        when(reportItem).GetSrcIndex().thenReturn(1)
        when(reportItem).GetName().thenReturn(u'Name')
        when(reportItem).GetActivity().thenReturn(u'abc')
        when(reportItem).GetId().thenReturn(1)
        when(reportItem).GetAbortCode().thenReturn(u'')
        when(reportItem).GetExecLevel().thenReturn(1)
        
        review = ReportItemComment(1, 1, u'Author', datetime.now().timestamp(), u'#Tag2# Kommentar #Tag1# und #Tag3# etc.pp.', u'SUCCESS')

        reportApi = mock()
        when(reportApi).IterUserComments(any()).thenReturn( item for item in [review] )
        when(reportApi).GetSetting(eq(u'detectReviewTags')).thenReturn(u'Tag1;Tag2;Tag3')
        
        # ACT
        result = GetReviewsForReportItem(reportApi, reportItem)
        
        # ASSERT
        result[0].SetTestCaseRef('ref')
        xml = ElementTree.tostring(result[0].GetXml(), encoding='unicode', method='xml')
        self.assertIn(u'<TAGS>', xml)
        self.assertIn(u'<TAG>Tag1</TAG>', xml)
        self.assertIn(u'<TAG>Tag2</TAG>', xml)
        self.assertIn(u'<TAG>Tag3</TAG>', xml)
        self.assertIn(u'</TAGS>', xml)

if __name__ == '__main__':
    unittest.main()
