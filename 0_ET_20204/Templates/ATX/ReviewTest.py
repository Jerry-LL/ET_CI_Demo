# -*- coding: utf-8 -*-
'''
Created on 23.03.2020

@author: Philipp
'''

import unittest
from mockito import mock, when


try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass

from .Review import Review


class ReviewTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

        import gettext
        gettext.NullTranslations().install()

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testSortOnSameExecLevelBadVerdictWins(self):
        # ARRANGE
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

        # ACT
        result = sorted([review1, review3, review2])

        # ASSERT
        self.assertEqual("ERROR", result.pop(0).GetRevaluationVerdict())
        self.assertEqual("FAILED", result.pop(0).GetRevaluationVerdict())
        self.assertEqual("PASSED", result.pop(0).GetRevaluationVerdict())

    def testSortOnSameIndexLevelRecentVerdictWins(self):
        # ARRANGE
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
        when(reportCommentMock2).GetTimestamp().thenReturn(1)
        review2 = Review(reportCommentMock2, "Level 1", 1, 1, None)

        # ACT
        result = sorted([review1, review2])

        # ASSERT
        self.assertEqual("PASSED", result.pop(0).GetRevaluationVerdict())
        self.assertEqual("FAILED", result.pop(0).GetRevaluationVerdict())


if __name__ == '__main__':
    unittest.main()
