# -*- coding: utf-8 -*-

'''
Created on 19.10.2015

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''

import sys
import re

from datetime import datetime
from lxml import etree

if sys.version_info < (3,):
    str = unicode


class Review(object):
    '''
    Bildet eine Nachbewertung im TRF als Review für den ATX Upload ab.
    '''

    FIND_ASCII_CTRL_REG_EXP = re.compile(r'[\x00-\x1F]+')

    def __init__(self, comment, teststepName, execLevel, indexLevel, customVerdict):
        '''
        Konstruktor.
        @param comment: Nachbewertung eines TestSteps
        @type comment: UserComment
        @param teststepName: Name des TestSteps
        @type teststepName: str
        @param execLevel: Gibt die Ebene des Test-Steps an, welche einem Review unterzogen wurde,
                          damit eine eine Gruppierung möglich ist.
        @type execLevel: str
        @param indexLevel: Gibt das Level des Test-Steps an, welche einem Review unterzogen wurde,
                           damit eine Sortierung möglich ist.
        @type indexLevel: str
        @param customVerdict: Custom-Verdict, dass der Nutzer für die Nachbewertung gesetzt hat.
                              Muss beim Zurückspielen zu TEST-GUIDE bekannt sein.
        @type customVerdict: str
        '''
        # Zyklischen Import vermeiden!
        from .Utils import FilterSUCCESS

        commentText = comment.GetText()
        if not commentText:
            commentText = u''
        commentText = self.FIND_ASCII_CTRL_REG_EXP.sub(u'', commentText)

        self.__testcaseRef = None
        self.__author = comment.GetAuthor()
        self.__result = FilterSUCCESS(comment.GetOverriddenResult())
        self.__comment = u'{0}{1}: {2}'.format(teststepName,
                                               u" -> {0}".format(self.__result) if self.__result
                                               else u"",
                                               commentText)
        self.__timestamp = comment.GetTimestamp()
        self.__customVerdict = customVerdict
        self.__reviewTags = set()
        self.__defectClass = None

        def Isfloat(value):
            '''
            Prüft ob es sich beim übergebenen String um ein Float-Wert handelt oder nicht.
            @param value: zu prüfender String
            @type value: str
            @return: True, wenn Float, sonst False.
            @rtype: boolean
            '''
            try:
                float(value)
                return True
            except ValueError:
                return False

        # Leider ist der SrcIndex auf TraceAnalyse-TestSteps nicht vorhanden und wird daher
        # hart gesetzt!
        # Zusätzlich haben Reviews bei ERROR-PACKAGES keine korrekten "Float-Index"
        if not indexLevel or not Isfloat(indexLevel):
            indexLevel = 0

        # Fallback, falls mal das ExecLevel nicht gesetzt wurde
        if not execLevel:
            execLevel = 0

        self.__indexLevel = float(indexLevel)
        self.__execLevel = int(execLevel)

    def __lt__(self, other):
        # Wird im Utils.GroupReviewsPerPackage verwendet um die korrekte Reihenfolge der Reviews
        # auf gleichen Ebene zu ermitteln.

        # Zyklischen Import vermeiden!
        from .Utils import GetVerdictWeighting

        if hasattr(other, u'GetIndexLevel'):
            # Wenn beide Reviews auf gleicher Ebene sind, dann muss
            # 1. das schlechtere Review-Verdict gewinnen!
            # 2. oder bei Gleichstand das jüngst erstellte!
            if (self.GetExecLevel() == other.GetExecLevel() and
                    self.GetIndexLevel() != other.GetIndexLevel()):
                if self.GetRevaluationVerdict() and other.GetRevaluationVerdict():
                    return (GetVerdictWeighting(other.GetRevaluationVerdict()) <
                            GetVerdictWeighting(self.GetRevaluationVerdict()))

                return other.GetTimestamp() < self.GetTimestamp()

            # Wenn beide Reviews auf gleichem Block sind, dann muss der ältere aktueller sein!
            if self.GetIndexLevel() == other.GetIndexLevel():
                return other.GetTimestamp() < self.GetTimestamp()

            return self.GetIndexLevel() < other.GetIndexLevel()
        return None

    def GetTimestamp(self):
        '''
        @return: Zeitstempel, wann das Review erstellt wurde.
        @rtype: float
        '''
        return self.__timestamp

    def GetIndexLevel(self):
        '''
        @return: eindeutiger Index, des nachbewerteten TestSteps für eine Sortierung der Reviews.
        @rtype: float
        '''
        return self.__indexLevel

    def GetExecLevel(self):
        '''
        @return: Ebene, des nachbewerteten TestSteps für eine Gruppierung der Ergebnisse.
        @rtype: integer
        '''
        return self.__execLevel

    def AppendReview(self, review):
        '''
        Fügt dem aktuellen Review die Reviewkommentare des übergebenen Reviews hinzu.
        Dies ist sinnvoll, wenn Reviews gebündelt werden sollen.
        @param review: das Review, von welchem der Kommentar dem Bestands-Review hinzugefügt
                       werden soll.
        @type review: Review
        '''
        self.__comment = u"{0}<br/><hr/>{1}".format(self.__comment, review.GetComment())

    def GetComment(self):
        '''
        @return: Gibt den Review-Kommentar zurück.
        @rtype: str
        '''
        return self.__comment

    def GetRevaluationVerdict(self):
        '''
        @return: Gibt die Review-ATX-Nachbewertung zurück.
        @rtype: str
        '''
        # Workaround für TTS-13508 und ET 8.0
        # Nicht entfernbar wegen Abwärtskompatibilität!
        # de: Keine (nur Kommentar)
        # eng: None (only comment)
        if self.__result and ("(" in self.__result and ")" in self.__result):
            return None

        return self.__result

    def SetRevaluationVerdict(self, atxVerdict):
        '''
        Setzt das ATX-Nachbewertungs-Verdict für dieses Review.
        @param atxVerdict: Review-ATX-Nachbewertung, die gesetzt werden soll.
        @type atxVerdict: str
        '''
        self.__result = atxVerdict

    def SetTestCaseRef(self, testCaseRefPath):
        '''
        Setzt den REF Pfad des Reviews
        @param testCaseRefPath: REF Pfad des Report TestCase, auf den sich das Review bezieht
        @type testCaseRefPath: str
        '''
        self.__testcaseRef = testCaseRefPath

    def GetTestCaseRef(self):
        '''
        Gibt den REF Pfad des Reviews zurück für einen Vergleich z.B. der Ebenen.
        @return: testCaseRefPath: REF Pfad des Report TestCase, auf den sich das Review bezieht
        @rtype testCaseRefPath: str
        '''
        return self.__testcaseRef

    def AddReviewTag(self, tag):
        '''
        Fügt einen Review-Tag dem Review hinzu, welches beim Upload ins TEST-GUIDE auch im
        TEST-GUIDE vorhanden/konfiguriert sein muss.
        @param tag: Review-Tag er hinzugefügt werden soll.
        @type tag: str
        '''
        self.__reviewTags.add(tag)

    def SetDefectClass(self, defectClass):
        '''
        Fügt dem Review eine Fehlerklasse hinzu, welches beim Upload ins TEST-GUIDE auch im
        TEST-GUIDE vorhanden/konfiguriert sein muss.
        @param defectClass: Fehlerklasse
        @type defectClass: str
        '''
        self.__defectClass = defectClass

    def GetXml(self):
        '''
        Erzeugt für das Review ein ETree Objekt.
        @return: XML Objekt des Reviews
        @rtype: etree.Element
        '''
        # Zyklischen Import vermeiden!
        from .Utils import GetIsoDate

        if not self.__testcaseRef:
            raise ValueError()
        review = etree.Element(u'TESTCASE-REVIEW')
        etree.SubElement(review, u'VERDICT-REVALUATION').text = self.__result

        # Review-Tags übernehmen
        if self.__reviewTags:
            tags = etree.SubElement(review, u'TAGS')
            for each in self.__reviewTags:
                etree.SubElement(tags, u'TAG').text = each

        # Review-Fehlerklasse übernehmen
        if self.__defectClass:
            defect = etree.SubElement(review, u'DEFECT')
            defect.text = self.__defectClass

        # Custom Verdict übernehmen, wenn gesetzt
        if self.__customVerdict:
            etree.SubElement(review, u'CUSTOM-EVALUATION-KEY').text = self.__customVerdict

        etree.SubElement(review, u'REVIEWER').text = etree.CDATA(str(self.__author))
        # Fehlerhaftes Copy und Paste aus Excel mit Vertical Tabs unterbinden.
        etree.SubElement(review, u'COMMENT').text = etree.CDATA(str(self.__comment).replace('\v',
                                                                                            '\n'))
        etree.SubElement(review,
                         u'DATE').text = GetIsoDate(datetime.fromtimestamp(self.__timestamp))
        etree.SubElement(review, u'REF', DEST=u"TEST-CASE").text = self.__testcaseRef
        return review
