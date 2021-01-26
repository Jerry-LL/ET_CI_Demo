# -*- coding: utf-8 -*-

'''
Created on 07.02.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''


from collections import OrderedDict
from copy import deepcopy


class Node(object):
    '''
    Erzeugt rekursiv die Knotenstruktur der Testschritte aus der gegebenen Liste und gibt diese
    dann als Dictionary zurück.
    '''
    def __init__(self, depth, data, parent=None):
        '''
        Konstruktor.
        @param depth: Tiefenebene des Testschritts.
        @type depth: int
        @param data: Datenobjekt des Testschritts (SHORT-NAME, LONG-NAME, VERDICT, usw.).
        @type data: dict
        @param parent: Parent Node Objekt, um den REF Pfad rekursiv zu ermitteln.
        @type parent: Node
        '''
        self.__subNodes = []
        self.__depth = depth
        self.__data = data
        self.__parent = parent

    def AddNode(self, depth, data):
        '''
        Fügt dieser Instanz einen neuen Kind-Knoten hinzu oder reicht das Objekt an sein letztes
        Kind weiter.
        @param depth: Tiefenebene des Testschritts.
        @type depth: int
        @param data: Datenobjekt des Testschritts (SHORT-NAME, LONG-NAME, VERDICT, usw.).
        @type data: dict
        '''
        if depth == self.__depth:
            pass
        elif depth - self.__depth == 1:
            self.__subNodes.append(Node(depth, data, self))
        else:
            try:
                if len(self.__subNodes) > 0:
                    self.__subNodes[-1].AddNode(depth, data)
                else:
                    # es wurde eine execLevel-Stufe ausgelassen
                    pass
            except IndexError as ie:
                # Wenn es bei eine TestStep zu einem Fehler kommt wird das toleriert, da wir den
                # kompletten Report nicht abbilden können.
                print(u'IndexError: {ie}'.format(ie=ie))

    def GetData(self):
        '''
        @return: Datenobjekt des Testschritts (SHORT-NAME, LONG-NAME, VERDICT, usw.).
        @rtype: dict
        '''
        return self.__data

    def HasNodes(self):
        '''
        @return: True wenn Kind-Knoten vorhanden sind, sonst False
        @rtype: boolean
        '''
        return len(self.__subNodes) > 0

    def GetRefPath(self):
        '''
        Erzeugt den Teil des REF Pfads, welcher die Testschritte identifiziert.
        @return: Teil des REF Pfad für den Testschritt.
        @rtype: str
        '''
        if self.__parent is not None:
            return u'{0}/{1}'.format(self.__parent.GetRefPath(), self.__data[u'SHORT-NAME'])
        else:
            return self.__data[u'SHORT-NAME']

    def GetList(self):
        '''
        Erzeugt aus den Kind-Knoten die ATX Struktur.
        @return: Dictionary mit unbewerteten Testschritten und bewerteten Testschritten.
        @rtype: dict
        '''
        testStepList = []
        reportList = []

        for each in self.__subNodes:
            testStep = OrderedDict([(u'@type', u'TEST-STEP'),
                                    (u'SHORT-NAME', each.GetData()[u'SHORT-NAME']),
                                    (u'LONG-NAME', each.GetData()[u'LONG-NAME']), ])

            if u'CATEGORY' in each.GetData() and each.GetData()[u'CATEGORY']:
                testStep[u'CATEGORY'] = each.GetData()[u'CATEGORY']

            # Verdict Definition nur in die TestSpec übernehmen.
            if u'VERDICT-DEFINITION' in each.GetData():
                testStep[u'VERDICT-DEFINITION'] = each.GetData()[u'VERDICT-DEFINITION']

            # Daten für den Report von der Spec duplizieren und ab hier nur noch Daten für den
            # Reportteil übernehmen.
            reportStep = deepcopy(testStep)
            reportStep[u'VERDICT-RESULT'] = {
                u'VERDICT': each.GetData()[u'VERDICT']
            }

            if each.HasNodes():
                testStep[u'@type'] = u'TEST-STEP-FOLDER'
                reportStep[u'@type'] = u'TEST-STEP-FOLDER'
                iterLists = each.GetList()
                testStep[u'*TEST-STEPS'] = iterLists[u'testSteps']
                reportStep[u'*TEST-STEPS'] = iterLists[u'reportSteps']

            testStepList.append(testStep)
            reportList.append(reportStep)

        return {u'testSteps': testStepList, u'reportSteps': reportList}
