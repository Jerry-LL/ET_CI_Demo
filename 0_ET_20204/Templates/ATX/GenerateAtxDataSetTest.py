# -*- coding: utf-8 -*-

"""
Created on 09.07.2015

@author: Philipp
"""

import unittest

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass

# pylint: disable=protected-access


class GenerateAtxDataSetTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

        import gettext
        gettext.NullTranslations().install()

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testGetWildcardWordsFromWordListWithAsterisk(self):
        """
        Prüfe RegEx Erfassung z.B. der Attribute mit *-Wildcard.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        word = u'Section*'
        words = [u'SectionA', u'SectionB', u'SectionC', u'Sectio', u'SectionB2', u'SectionBXyZ']

        # ACT
        wildcardWordsFromWordList = GenerateAtxDataSet.GetWildcardWordsFromWordList(word, words)

        # ASSERT
        self.assertEqual([u'SectionA', u'SectionB', u'SectionC', u'SectionB2', u'SectionBXyZ'],
                         wildcardWordsFromWordList)

    def testGetWildcardWordsFromWordListWithQuestionMark(self):
        """
        Prüfe RegEx Erfassung z.B. der Attribute mit ?-Wildcard.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        word = u'?ection??'
        words = [u'ASectionA0', u'SectionA', u'SectionB', u'SectionC', u'Sectio', u'SectionB2',
                 u'SectionB1', u'SectionBXyZ']

        # ACT
        wildcardWordsFromWordList = GenerateAtxDataSet.GetWildcardWordsFromWordList(word, words)

        # ASSERT
        self.assertEqual([u'SectionB2', u'SectionB1'], wildcardWordsFromWordList)

    def testGetWildcardWordsFromWordListWithoutWildCards(self):
        """
        Prüfe Erfassung der Attribute.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        word = u'Sectio'
        words = [u'ASectionA0', u'SectionA', u'SectionB', u'SectionC', u'Sectio', u'SectionB2',
                 u'SectionB1', u'SectionBXyZ']

        # ACT
        wildcardWordsFromWordList = GenerateAtxDataSet.GetWildcardWordsFromWordList(word, words)

        # ASSERT
        self.assertEqual([u'Sectio'], wildcardWordsFromWordList)

    def testGetConstantsOneConstant(self):
        """
        Prüfe die Konvertierung der Konstanten.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        constInput = u'myConstant=NightlyTest'
        expected = {u'myConstant': u'NightlyTest'}

        # ACT
        result = GenerateAtxDataSet.GetConstants(constInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetConstants(self):
        """
        Prüfe die Konvertierung der Konstanten.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        constInput = u'myConstant=NightlyTest; Buildnumber=42'
        expected = {u'myConstant': u'NightlyTest', u'Buildnumber': u'42'}

        # ACT
        result = GenerateAtxDataSet.GetConstants(constInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetConstantsOnEmptyInput(self):
        """
        Prüfe die Konvertierung der Konstanten.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        constInput = u""
        expected = {}

        # ACT
        result = GenerateAtxDataSet.GetConstants(constInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetConstantsOnNoneInput(self):
        """
        Prüfe die Konvertierung der Konstanten.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        constInput = None
        expected = {}

        # ACT
        result = GenerateAtxDataSet.GetConstants(constInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetConstantsOnCorruptInput(self):
        """
        Prüfe die Konvertierung der Konstanten.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        constInput = u'myConstant: NightlyTest; Buildnumber=42'

        # ACT
        try:
            result = GenerateAtxDataSet.GetConstants(constInput)

        # ASSERT
            self.fail('Exception expected but not thrown')
        except Exception:
            pass

    def testGetAttributesOneAttribute(self):
        """
        Prüfe die Konvertierung der Attribute, exakt wie bei den GetConstants-Tests.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        attrInput = u'myAttr=NightlyTest'
        expected = {u'myAttr': u'NightlyTest'}

        # ACT
        result = GenerateAtxDataSet.GetAttributes(attrInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetAttributes(self):
        """
        Prüfe die Konvertierung der Attribute, exakt wie bei den GetConstants-Tests.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        attrInput = u'myAttr=NightlyTest; myReqId=42'
        expected = {u'myAttr': u'NightlyTest',
                    u'myReqId': u'42'}

        # ACT
        result = GenerateAtxDataSet.GetAttributes(attrInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testConvertKeyLineToListOnCorrectInput(self):
        """
        Prüfe das Auslesen der Attribute.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'SOP;ReqId'
        expected = [u'SOP', u'ReqId']

        # ACT
        result = GenerateAtxDataSet.ConvertKeyLineToList(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testConvertKeyLineToListOnCorrectSingleInput(self):
        """
        Prüfe das Auslesen der Attribute.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'SOP'
        expected = [u'SOP']

        # ACT
        result = GenerateAtxDataSet.ConvertKeyLineToList(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testConvertKeyLineToListOnCorrectSingleInputWithDelimiter(self):
        """
        Prüfe das Auslesen der Attribute.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'SOP;'
        expected = [u'SOP']

        # ACT
        result = GenerateAtxDataSet.ConvertKeyLineToList(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testConvertKeyLineToListOnNoneInput(self):
        """
        Prüfe das Auslesen der Attribute.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = None
        expected = []

        # ACT
        result = GenerateAtxDataSet.ConvertKeyLineToList(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testConvertKeyLineToListOnEmptyInput(self):
        """
        Prüfe das Auslesen der Attribute.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u""
        expected = []

        # ACT
        result = GenerateAtxDataSet.ConvertKeyLineToList(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetAttributeDelimiter(self):
        """
        Prüfe das Auslesen der Trennzeichen für Attribute-Splitting.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'ReqId=-'
        expected = {}
        expected[u'ReqId'] = u'-'

        # ACT
        result = GenerateAtxDataSet.GetAttributeDelimiterFromConfig(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetEmptyAttributeDelimiter(self):
        """
        Prüfe das Auslesen der Trennzeichen für Attribute-Splitting.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'ReqId=_;Empty='
        expected = {}
        expected[u'ReqId'] = u'_'

        # ACT
        result = GenerateAtxDataSet.GetAttributeDelimiterFromConfig(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetAttributeSingleDelimiterWithEndingSemiconlon(self):
        """
        Prüfe das Auslesen der Trennzeichen für Attribute-Splitting.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'ReqId=;;'
        expected = {}
        expected[u'ReqId'] = u';'

        # ACT
        result = GenerateAtxDataSet.GetAttributeDelimiterFromConfig(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetAttributeSingleDelimiterWithoutEndingSemiconlon(self):
        """
        Prüfe das Auslesen der Trennzeichen für Attribute-Splitting.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'ReqId=;'
        expected = {}
        expected[u'ReqId'] = u';'

        # ACT
        result = GenerateAtxDataSet.GetAttributeDelimiterFromConfig(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def testGetAttributeMultiDelimiter(self):
        """
        Prüfe das Auslesen der Trennzeichen für Attribute-Splitting.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet
        confgInput = u'ReqId=;;JIRA=-; Doors=_;Space= ;Redmine=-;'
        expected = {}
        expected[u'ReqId'] = u';'
        expected[u'JIRA'] = u'-'
        expected[u'Doors'] = u'_'
        expected[u'Space'] = u' '
        expected[u'Redmine'] = u'-'

        # ACT
        result = GenerateAtxDataSet.GetAttributeDelimiterFromConfig(confgInput)

        # ASSERT
        self.assertEqual(expected, result)

    def test_GetAttrSpecDefinitionName_ProjectAttributeName(self):
        """
        Prüfe das Abschneiden des Prefix bei Projekt Attribut Namen
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet

        expectedName = 'TestName'
        atxProjectAttributeName = '{0}{1}'.format(GenerateAtxDataSet.PRJ_ATT_PREFIX, expectedName)

        # ACT
        result = GenerateAtxDataSet._GetAttrSpecDefinitionName(atxProjectAttributeName)

        # ASSERT
        self.assertEqual(expectedName, result)

    def test_GetAttrSpecDefinitionName_PackageAttributeName(self):
        """
        Prüfe das Nicht Abschneiden des Prefix bei Package Attribut Namen
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet

        expectedName = 'TestName'
        atxPacakgeAttributeName = expectedName

        # ACT
        result = GenerateAtxDataSet._GetAttrSpecDefinitionName(atxPacakgeAttributeName)

        # ASSERT
        self.assertEqual(expectedName, result)

    def test_GetAttributeDelimiter_DelimiterConfig(self):
        """
        Prüfe das zurückgeben, des richtigen Delimiters aus der Delimiter Config
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet

        expectedName = 'TestName'
        expectedDelimiter = ';'
        atxPacakgeAttributeName = expectedName
        delimiterConfig = '{0}={1}'.format(expectedName, expectedDelimiter)

        # ACT
        result = GenerateAtxDataSet._GetAttributeDelimiter(
            atxPacakgeAttributeName,
            None,
            delimiterConfig)

        # ASSERT
        self.assertEqual(expectedDelimiter, result)

    def test_GetAttributeDelimiter_AttrSpec_MultiChoide(self):
        """
        Prüfe das zurückgeben, des richtigen Delimiters aus der AttrSpec falls 
        Attribute MultiChoice unterstützt
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet

        expectedName = 'TestName'
        expectedDelimiter = '!'
        atxPacakgeAttributeName = expectedName

        from tts.lib.attributes.AttrSpec import AttributeTreeValueDef
        definition = AttributeTreeValueDef(expectedName,
                                           valueSeparator=expectedDelimiter,
                                           isMultiChoice=True)

        # ACT
        result = GenerateAtxDataSet._GetAttributeDelimiter(
            atxPacakgeAttributeName,
            definition)

        # ASSERT
        self.assertEqual(expectedDelimiter, result)

    def test_GetAttributeDelimiter_Default(self):
        """
        Prüfe das zurückgeben, des default Delimiters
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet

        expectedName = 'TestName'
        expectedDelimiter = ','
        atxPacakgeAttributeName = expectedName

        # ACT
        result = GenerateAtxDataSet._GetAttributeDelimiter(
            atxPacakgeAttributeName,
            None)

        # ASSERT
        self.assertEqual(expectedDelimiter, result)

    # TODO: Mehr ATX Format Tests schreiben
    def test_GetATXAttributeFormat_Basic(self):
        """
        Prüfe das Erstellen des ATX Attribut Formats.
        """
        # ARRANGE
        from .GenerateAtxDataSet import GenerateAtxDataSet

        attributeName = 'TestName'
        attrubuteValue = 'Val1,Val2,Val3'
        expectedValues = 3
        # ACT
        result = GenerateAtxDataSet._GetATXAttributeFormat(attributeName, attrubuteValue , False)

        # ASSERT
        self.assertEqual(attributeName, result[u'@GID'])
        self.assertEqual(expectedValues, len(result[u'*SDS']))


if __name__ == '__main__':
    unittest.main()
