# -*- coding: utf-8 -*-

'''
Created on 07.02.2014

Erzeugt aus dem übergebenen Package die ATX Struktur im Speicher.

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''

from collections import OrderedDict

from .Config import Config
from .Node import Node
from .Utils import FilterSUCCESS, FilterShortName, ConvertConditionBlocks,\
    GetReviewsForReportItem, GetReviewsForPackage, UpdateRefOnReviews, ReplaceAsciiCtrlChars
from .TraceAnalysisJob import TraceAnalysisJob
from .ProcessTestStepImage import ProcessTestStepImage


class ProcessPackage(object):
    '''
    Konvertiert ein ECU-TEST Package in ein ATX TestCase.
    '''
    def __init__(self, report, package, refPath):
        '''
        Konstruktor.
        @param report: Durchgereichtes ReportApi Objekt.
        @type report: tts.core.report.parser.ReportApi
        @param package: Das zu konvertierende Package.
        @type package: Package
        @param refPath: Ref Pfad des Packages
        @type refPath: str
        '''
        self.__createTestSteps = Config.GetSetting(report, u'includePkgTestSteps') == u"True"
        self.__captureSubPackageOnVerdict = self.__GetCaptureSubPackageOnVerdictList(report)
        self.__sepPkg = True
        self.__traceJobIds = []
        self.__refPath = refPath
        self.__reviews = []
        self.__rootNode = None
        self.__skipStepFlag = [False, -1]
        self.__subPackages = []
        self.__traceJobs = []
        self.__swkIds = []
        self.__imageProcessor = ProcessTestStepImage()
        self.__convertedPkg = self.__ConvertPkg(report, package)

    def __GetCaptureSubPackageOnVerdictList(self, report):
        '''
        Ermittelt aus der Konfig, bei welchen ECU-TEST Verdicts ggf. die TestSteps der SubPackages
        mit erfasst werden sollen.
        @param report: ReportApi für den Zugriff auf die Konfigurationseinstellungen
        @type report: tts.core.report.parser.ReportApi
        @return: Liste mit Strings der ATX-Verdicts welche vearbeitet werden
        @rtype: list
        '''
        configValue = Config.GetSetting(report, u'captureSubPackageOnVerdict')

        if not configValue:
            return []

        return [FilterSUCCESS(each.strip()) for each in configValue.split(u";")]

    def GetSwkIds(self):
        '''
        @return: Liste (ohne Doppelungen) von enthaltenen SWK-Ids, welche verwendet wurden.
        @rtype: list
        '''
        return list(set(self.__swkIds))

    def GetConvertedPkg(self):
        '''
        Gibt das konvertierte Package zurück.
        @return: Das konvertierte Package.
        @rtype: dict
        '''
        return self.__convertedPkg

    def GetTestStepImages(self):
        """
        :return: die Test-Step ATX-RefPaths mit der Datei-Liste den Bilder, welche in diesem
                 Test-Step erstellt wurden.
        :rtype: dict
        """
        return self.__imageProcessor.GetTestStepImages()

    def GetTraceJobs(self):
        '''
        @return: Liste der TraceAnalysisJob aus diesem Package.
        @rtype: list
        '''
        return self.__traceJobs

    def GetReviews(self, reportRefPath):
        '''
        Gibt die Reviews des Packages zurück.
        @param reportRefPath: REF Pfad zum Report TestCase
        @type reportRefPath: str
        @return: Liste der Reviews
        @rtype: List->Review
        '''
        return UpdateRefOnReviews(self.__reviews, reportRefPath)

    def GetSubPackages(self):
        '''
        @return: Ermittelte SubPackages des aktuellen Package
        @rtype: list->ReportItem
        '''
        return self.__subPackages

    def __CreateReviewsForTestCase(self, report, package):
        '''
        Ermittelt alle direkten Nachbewertungen auf dem Package und erzeugt für jede ein
        Review Objekt.
        @param report: Durchgereichtes ReportApi Objekt
        @type report: tts.core.report.parser.ReportApi
        @param package: Das zu konvertierende Package.
        @type package: Package
        @return: True, wenn es eine Nachbewertung auf dem kompletten Testfall gab, sonst False.
        @rtype: boolean
        '''
        resultReviews = GetReviewsForPackage(report, package)
        self.__reviews.extend(resultReviews)
        return len(resultReviews) > 0

    def __CreateReviewsForTestStep(self, report, teststep):
        '''
        Ermittelt alle Nachbewertungen zu dem TestStep und erzeugt für jede ein Review Objekt.
        @param report: Durchgereichtes ReportApi Objekt
        @type report: tts.core.report.parser.ReportApi
        @param teststep: TestStep, zu dem Nachbewertungen erfasst werden
        @type teststep: ReportItem
        '''
        self.__reviews.extend(GetReviewsForReportItem(report, teststep))

    def __ConvertPkg(self, report, pkg):
        '''
        Führt die Konvertierung aus.
        @param report: Durchgereichtes ReportApi Objekt.
        @type report: tts.core.report.parser.ReportApi
        @param pkg: Das zu konvertierende Package.
        @type pkg: tts.core.report.parser.Package.Package
        @return: Dictionary mit den TestSteps
        @rtype: dict
        '''

        # Reviews für dieses Package/Testfall erzeugen!
        hasTestCaseReview = self.__CreateReviewsForTestCase(report, pkg)

        for testStep in pkg.GetTestCase(self.__sepPkg).IterTestSteps():

            self.__ConvertTestStep(report, testStep, hasTestCaseReview)

            # Wenn ein Review für den Testfall vorhanden ist, dann gilt dieses und nicht die
            # TestStep-Reviews
            if not hasTestCaseReview:
                # Reviews für diesen Teststep erzeugen
                self.__CreateReviewsForTestStep(report, testStep)

        # Wenn das Package leer ist, dann prüfen ob es Fehler gab und diese als TestStep
        # hinterlegen
        if not self.__rootNode:
            if pkg.GetCallError() is not None:
                self.__CreateErrorPkgTestStep(pkg)
            else:
                return None

        testSteps = self.__rootNode.GetList()

        if pkg.HasAnalysisJobs(self.__sepPkg):
            for analysisJobItem in pkg.IterAnalysisJobs(True):
                job = TraceAnalysisJob(analysisJobItem, self.__refPath, report)

                self.__traceJobs.append(job)

                cjob = job.GetConvertedJob()
                if cjob:
                    testSteps[u'testSteps'].extend(cjob[u'testSteps'])
                    testSteps[u'reportSteps'].extend(cjob[u'reportSteps'])

        return ConvertConditionBlocks(testSteps[u'testSteps'], testSteps[u'reportSteps'])

    def __CreateErrorPkgTestStep(self, pkg):
        '''
        Erzeugt im Falle eines Packages, welches zum Beispiel nicht geladen werden kann, ein Error-
        TestStep mit der Fehlermeldung als Block-Inhalt, damit das Package im TEST-GUIDE auch
        erfasst wird da leere Packages ignoriert werden.
        @param pkg: Das Package zu welchem der ErrorTestStep erzeugt werden soll.
        @type pkg: tts.core.report.parser.Package.Package
        '''
        self.__rootNode = Node(-1, {u'SHORT-NAME': self.__refPath})
        pkgVerdict = FilterSUCCESS(pkg.GetOriginalResult())

        args = {u'id': 0, u'verdict': pkgVerdict}
        args[u'longName'] = u'{0}'.format(pkg.GetCallError())

        self.__rootNode.AddNode(0, self.__CreateTestStep(args))

    def __ConvertTestStep(self, report, testStep, hasTestCaseReview):
        '''
        Konvertiert einen TestStep nach ATX.
        @param report: Durchgereichtes ReportApi Objekt.
        @type report: tts.core.report.parser.ReportApi
        @param testStep: TestStep von ECU-TEST
        @type testStep:  tts.core.report.parser.Package.ReportItem
        @param hasTestCaseReview: True, wenn schon ein Package-Review vorhanden ist und
                                  dies das TestStep-Review überschreibt, sonst False
        @type hasTestCaseReview: bool
        '''

        if not self.__createTestSteps:
            return

        execLevel = testStep.GetExecLevel()
        activity = testStep.GetActivity()
        srcType = testStep.GetSrcType()
        subSrcType = testStep.GetSrcSubType()
        result = FilterSUCCESS(testStep.GetOriginalResult())
        lineNo = testStep.GetSrcIndex()
        # Nachbewertungen/Kommentare in Packages erfassen, wenn
        # 1. es eine gibt und die Bewertung ändert
        # 2. es sich um eine Errorpackage handelt.
        hasDeepRevaluation = (testStep.GetResult() != testStep.GetOriginalResult() or
                              lineNo == "ERRORPACKAGE")
        info = testStep.GetInfo()
        # comment = testStep.GetComment()
        name = testStep.GetName()

        # Wenn keine ID-Referenz vorhanden ist, dann überspringen!
        if testStep.GetSrc() is None:
            return

        # Jeden Activity auf Großbuchstaben konvertieren und damit vergleichen!
        if activity is None:
            activity = u''
        cmpActivity = activity.upper()

        if cmpActivity == u'ABORT':
            return

        # Jeden Namen auf Großbuchstaben konvertieren und damit vergleichen!
        if name is None:
            name = u''
        cmpName = name.upper()

        if subSrcType is None:
            subSrcType = u""
        cmpSubSrcType = subSrcType.upper()

        stepId = testStep.GetSrc()

        if self.__skipStepFlag[0]:
            if self.__skipStepFlag[1] < execLevel:
                return
            if self.__skipStepFlag[1] >= execLevel:
                self.__skipStepFlag = [False, -1]

        if srcType == u'UTILITY' and (cmpActivity.startswith((u'SWITCHDEF',
                                                              u'IF',
                                                              u'FOR')) or
                                      cmpName.startswith(u'IFDEF')):
            # critical block (If, For, IfDef): ignore subsequent blocks until flag is released
            self.__skipStepFlag = [True, execLevel]
            if cmpName.startswith(u'IFDEF'):
                return

        # Falls noch kein Root-Knoten vorhanden ist wird er angelegt (erster valider
        # Iterationsschritt)
        if not self.__rootNode:
            # root Knoten bekommt als SHORT-NAME den Ref Pfad seines TestCases -> wird im else
            # von Node.getRefPath() abgerufen
            self.__rootNode = Node(execLevel - 1, {u'SHORT-NAME': self.__refPath})

        images = []

        # valide Elemente erkennen und hinzugefügen:
        # Blöcke und SubPackages
        if srcType in [u'UTILITY', u'UNDEFINED', u'PACKAGE', u'PARALLEL_PACKAGE', u'CALL']:
            args = {u'id': FilterShortName(stepId), u'verdict': result}

            if srcType == u'UNDEFINED':
                # Nur Images Undefined zulassen.
                if cmpSubSrcType == u"IMAGE":
                    reportId = int(testStep.GetReportItemId())
                    images = self.__imageProcessor.GetImageFilesForTestStep(reportId, testStep)
                    args[u'category'] = u"TRACE_ANALYSIS_PLOT" if images else False
                    args[u'verdictDefinition'] = info
                    args[u'longName'] = activity
                else:
                    return
            elif srcType == u'UTILITY':
                # Bei Block-Testschritten die Erwartungswerte (info) erfassen.
                if u":BLOCK" in cmpSubSrcType and info:
                    args[u'verdictDefinition'] = info

                if cmpActivity == u'UTILITY' and cmpName != _(u'Analyse-Job').upper():
                    return

                args[u'longName'] = activity

                if cmpName == _(u'Analyse-Job').upper():
                    # Wenn die TraceAnalyse noch nicht bekannt ist wird sie angelegt und mit 0
                    # initialisiert
                    i = 0
                    traceJobId = u'traceanalyse_{0}'.format(FilterShortName(info))
                    while traceJobId in self.__traceJobIds:
                        i += 1
                        traceJobId = u'{0}_{1}'.format(traceJobId, i)

                    # Die id des Schritts wird für TraceAnalysen überschrieben, da hier ein
                    # Fehler in der ReportApi dazu führt,
                    # dass TraceAnalysen im Gegensatz zu normalen Blöcken usw. bei
                    # Parametrierten Packages keine feste id haben.
                    args[u'id'] = traceJobId
                    args[u'longName'] = info
                    args[u'category'] = u'TRACEANALYSE'
            elif srcType in [u'PACKAGE', u'PARALLEL_PACKAGE']:
                args[u'longName'] = u'{0}'.format(name)
                args[u'category'] = u'SUB_PACKAGE'

                # SubPackages für separate Erfassung als Testfall mit speichern
                pkg = report.GetPackage(testStep)
                self.__subPackages.append(pkg)

                # ggf. die SWK-Ids ermitteln und bereitstellen
                self.__swkIds.extend(self.__ExtractSWKTestStepId(testStep))

                # ggf. die SWK-Erwartungen erfassen
                swkExpectation = self.__ConvertSWKTestStepExpectationToVerdictDefinition(testStep)
                if swkExpectation:
                    args[u'verdictDefinition'] = swkExpectation
                else:
                    pkgParamLabel = self.__GetPackageCallParameterToVerdictDefinition(pkg)
                    if pkgParamLabel:
                        args[u'verdictDefinition'] = u"({0})".format(pkgParamLabel)

                # SubPackages (nicht parallel ausgeführte) ausklappen, als TestSteps,
                # wenn das SubPackge bei entsprechendem Fehler erfasst werden soll
                if srcType in [u'PACKAGE'] and (result in self.__captureSubPackageOnVerdict or
                                                hasDeepRevaluation):

                    # Bestandkonten hinzufügeun und unter diesem die neuen Teststeps anordnen.
                    self.__rootNode.AddNode(execLevel, self.__CreateTestStep(args))

                    for eachTestStep in pkg.GetTestCase(self.__sepPkg).IterTestSteps():
                        self.__ConvertTestStep(report, eachTestStep, hasTestCaseReview)

                        if not hasTestCaseReview:
                            self.__CreateReviewsForTestStep(report, eachTestStep)

                    return

            elif srcType == u'CALL':
                args[u'longName'] = u'{0}'.format(name)
                args[u'category'] = u'AXS'

            testStepObj = self.__CreateTestStep(args)
            self.__rootNode.AddNode(execLevel, testStepObj)
            self.__imageProcessor.ComputeImageRefPaths(images,
                                                       self.__rootNode,
                                                       testStepObj[u'SHORT-NAME'])

    def __GetPackageCallParameterToVerdictDefinition(self, pkg):
        '''
        Ermittelt die Parameter des Packages, welche als Label im TEST-GUIDE für den Package-Call
        angezeigt werden soll.
        @param pkg: Package
        @type pkg: :class:`~Package.Package`
        @return: Label für den Package-Call
        @rtype: str
        '''
        result = ""
        for pkgParam in pkg.IterParameterVariables():
            result = u"{0}, {1}={2}".format(result,
                                            pkgParam.GetName(),
                                            pkgParam.GetValue())
            result = result.strip(", ")
        return result

    def __ConvertSWKTestStepExpectationToVerdictDefinition(self, testStep):
        '''
        Ermittelt aus dem TestStep die SWK-SOLL-Erwartungen, falls es sich bei dem TestStep um
        einen SWK-Aufruf handelt.
        @param testStep: Aktueller Package Teststep
        @type testStep: tts.core.report.parser.Package.ReportItem
        @return: Leeren String oder die Erwartung
        @rtype: str
        '''
        # Tabel-Entities durchsuchen
        for eachEntity in testStep.IterEntities():
            if (eachEntity.GetType() == u"tableentity_cell" and
                    eachEntity.GetName() == u"keywordReprCompare"):
                for each in eachEntity.IterRows():
                    # Wenn der folgende String vorhanden ist, dann den SWK-Soll-Wert daraus
                    # ermitteln.
                    # Beispielaufbau: [u'SOLL:', u'Abbiegelicht', u"'beidseitig'", u"'aus'"]
                    if _(u"SOLL:") in each:
                        # nur die Parameter und Erwartungen erfassen
                        if len(each) > 2:
                            return u" ".join(each[2:])
                    # abbrechen nach der ersten Zeile, da nur dort der Soll-Wert enthalten ist
                    break
        return u""

    def __ExtractSWKTestStepId(self, testStep):
        '''
        Ermittelt aus dem TestStep die SWK-Ids, falls es sich bei dem TestStep um
        einen SWK-Aufruf handelt.
        @param testStep: Aktueller Package Teststep
        @type testStep: tts.core.report.parser.Package.ReportItem
        @return: Liste von enthaltenen SWK-Ids
        @rtype: list
        '''
        result = []
        # Tabel-Entities durchsuchen
        for eachEntity in testStep.IterEntities():
            if (eachEntity.GetType() == u"tableentity_cell" and
                    eachEntity.GetName() == u"keywordId"):
                for each in eachEntity.IterRows():
                    # Wenn der folgende String vorhanden ist, dann die SWK-Id daraus
                    # ermitteln. Beispielaufbau: ['2660']
                    result.extend(each)
                    break
        return result

    def __CreateTestStep(self, args):
        '''
        Erzeugt aus den übergebenen Argumenten das TestStep Dict.
        @param args: Parameter für einen TestStep.
        @type args: dict
        @return: TestStep Objekt.
        @rtype: dict
        '''
        default = {u'language': u'DE'}
        params = dict(list(default.items()) + list(args.items()))

        ret = {
            u'SHORT-NAME': u'step_{0}'.format(params[u'id']),
            u'LONG-NAME': {
                u'L-4': {
                    u'@L': params[u'language'],
                    u'#': params[u'longName'],
                }
            },
            u'CATEGORY': False,
            u'VERDICT': params[u'verdict'],
        }

        if u'category' in params:
            ret[u'CATEGORY'] = params[u'category']

        verdictDefinition = ReplaceAsciiCtrlChars(params.get(u'verdictDefinition'))
        if verdictDefinition:
            verdictDef = OrderedDict({u'VERDICT-DEFINITION':
                                      OrderedDict([(u'REPORT-FREQUENCY', u'SINGLE'),
                                                   (u'PROVIDES-VERDICT', u'EVALUATE'),
                                                   (u'EXPECTED-RESULT', {
                                                       u'P': {
                                                           u'L-1': {
                                                               u'@L': params[u'language'],
                                                               u'#': verdictDefinition,
                                                           }
                                                       }
                                                   }), ])
                                      },)
            ret.update(verdictDef)
        return ret
