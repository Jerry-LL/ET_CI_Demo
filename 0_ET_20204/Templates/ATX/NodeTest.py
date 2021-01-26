# -*- coding: utf-8 -*-

'''
Created on 16.12.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''

import unittest

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass
from .Node import Node
from .Utils import ConvertConditionBlocks


class NodeTest(unittest.TestCase):

    def setUp(self):
        self.__testNode = Node(-1, {u'SHORT-NAME': u'Void'}, None)
        unittest.TestCase.setUp(self)

    def tearDown(self):
        self.__testNode = None
        unittest.TestCase.tearDown(self)

    def testHasPreAndPostConditionBlocksSimple(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Precondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Postcondition'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(1, len(atxTestSteps[u'setup']), u'Es sollte genau 1 Setup Element geben.')
        self.assertEqual(1, len(atxTestSteps[u'execution']), u'Es sollte genau 1 Execution Element geben.')
        self.assertEqual(1, len(atxTestSteps[u'teardown']), u'Es sollte genau 1 Teardown Element geben.')

    def testHasPreAndPostConditionBlocksComplex(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Precondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 1'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 2'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 3'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 4'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Postcondition'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(1, len(atxTestSteps[u'setup']), u'Es sollte genau 1 Setup Element geben.')
        self.assertEqual(4, len(atxTestSteps[u'execution']), u'Es sollte genau 4 Execution Elemente geben.')
        self.assertEqual(1, len(atxTestSteps[u'teardown']), u'Es sollte genau 1 Teardown Element geben.')

    def testHasNoPreAndPostConditionBlocks(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'NO_Precondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'NO_Postcondition'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(0, len(atxTestSteps[u'setup']), u'Es sollte kein Setup Element geben.')
        self.assertEqual(3, len(atxTestSteps[u'execution']), u'Es sollte genau 3 Execution Elemente geben.')
        self.assertEqual(0, len(atxTestSteps[u'teardown']), u'Es sollte kein Teardown Element geben.')

    def testHasPreAndPostConditionBlocksWrongOrder(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Postcondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Precondition'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(0, len(atxTestSteps[u'setup']), u'Es sollte kein Setup Element geben.')
        self.assertEqual(1, len(atxTestSteps[u'execution']), u'Es sollte genau 1 Execution Element geben.')
        self.assertEqual(2, len(atxTestSteps[u'teardown']), u'Es sollte geanu 2 Teardown Elemente geben.')

    def testHasOnlyPreConditionBlock(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Precondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 1'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 2'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(1, len(atxTestSteps[u'setup']), u'Es sollte genau 1 Setup Element geben.')
        self.assertEqual(2, len(atxTestSteps[u'execution']), u'Es sollte genau 2 Execution Elemente geben.')
        self.assertEqual(0, len(atxTestSteps[u'teardown']), u'Es sollte kein Teardown Element geben.')

    def testHasOnlyPostConditionBlock(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 1'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 2'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Postcondition'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(0, len(atxTestSteps[u'setup']), u'Es sollte kein Setup Element geben.')
        self.assertEqual(2, len(atxTestSteps[u'execution']), u'Es sollte genau 2 Execution Elemente geben.')
        self.assertEqual(1, len(atxTestSteps[u'teardown']), u'Es sollte genau 1 Teardown Element geben.')

    def testHasOnlyPostConditionBlockAtWrongPosition(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Postcondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 1'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 2'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(0, len(atxTestSteps[u'setup']), u'Es sollte kein Setup Element geben.')
        self.assertEqual(0, len(atxTestSteps[u'execution']), u'Es sollte kein Execution Element geben.')
        self.assertEqual(3, len(atxTestSteps[u'teardown']), u'Es sollte genau 3 Teardown Elemente geben.')

    def testHasOnlyPreConditionBlockAtWrongPosition(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 1'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 2'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Precondition'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(0, len(atxTestSteps[u'setup']), u'Es sollte kein Setup Element geben.')
        self.assertEqual(3, len(atxTestSteps[u'execution']), u'Es sollte genau 3 Execution Elemente geben.')
        self.assertEqual(0, len(atxTestSteps[u'teardown']), u'Es sollte kein Teardown Element geben.')

    def testHasOnlyActionConditionBlockSingle(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 1'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(0, len(atxTestSteps[u'setup']), u'Es sollte kein Setup Element geben.')
        self.assertEqual(1, len(atxTestSteps[u'execution']), u'Es sollte genau 1 Execution Element geben.')
        self.assertEqual(0, len(atxTestSteps[u'teardown']), u'Es sollte kein Teardown Element geben.')

    def testHasOnlyActionConditionBlockMultiple(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 1'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 2'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 3'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action 4'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(0, len(atxTestSteps[u'setup']), u'Es sollte kein Setup Element geben.')
        self.assertEqual(4, len(atxTestSteps[u'execution']), u'Es sollte genau 4 Execution Elemente geben.')
        self.assertEqual(0, len(atxTestSteps[u'teardown']), u'Es sollte kein Teardown Element geben.')

    def testHasNoPreOrPostConditionBlock(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Precondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Postcondition'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(1, len(atxTestSteps[u'setup']), u'Es sollte genau 1 Setup Element geben.')
        self.assertEqual(0, len(atxTestSteps[u'execution']), u'Es sollte kein Execution Element geben.')
        self.assertEqual(1, len(atxTestSteps[u'teardown']), u'Es sollte genau 1 Teardown Element geben.')

    def testHasPreAndPostConditionBlocksSimpleWithTraceAnalysis(self):
        # ARRANGE
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Precondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Action'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'Postcondition'}}})
        self.__testNode.AddNode(0, {u'SHORT-NAME': u'shortname', u'CATEGORY': u'cat', u'VERDICT': u'verdict', u'LONG-NAME': {u'L-4': {u'#': u'AnalysisJob'}}})
        # ACT
        testSteps = self.__testNode.GetList()
        atxTestSteps = ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])
        # ASSERT
        self.assertEqual(1, len(atxTestSteps[u'setup']), u'Es sollte genau 1 Setup Element geben.')
        self.assertEqual(1, len(atxTestSteps[u'execution']), u'Es sollte genau 1 Execution Element geben.')
        self.assertEqual(2, len(atxTestSteps[u'teardown']), u'Es sollte genau 2 Teardown Elemente geben.')


if __name__ == u'__main__':
    unittest.main()
