# -*- coding: utf-8 -*-

"""
Created on 15.08.2014

Erzeugt aus dem übergebenen TraceAnalyse-Job die ATX Struktur im Speicher.

:author: Christoph Groß <christoph.gross@tracetronic.de>
"""

import tempfile

from .Config import Config
from .ProcessTestStepImage import ProcessTestStepImage
from .Node import Node
from .Utils import (FilterSUCCESS, GetReviewsForReportItem, UpdateRefOnReviews)


class TraceAnalysisJob(object):
    """
    Konvertiert ein ECU-TEST TraceAnalyse-Job in ein ATX TestCase.
    """
    def __init__(self, job, refPath, report):
        """
        Konstruktor.
        :param job: Der zu konvertierende Job.
        :type job: AnalysisJobItem
        :param refPath: Ref Pfad des Packages
        :type refPath: str
        :param report: Durchgereichtes ReportApi Objekt.
        :type report: ReportApi
        """
        self.__report = report
        self.__refPath = refPath
        self.__traceAnalyseSteps = {}
        self.__reviews = []
        self.__imageProcessor = ProcessTestStepImage()
        self.__createTestSteps = Config.GetSetting(report, u'includePkgTestSteps') == u"True"

        self.__convertedJob = self.__ConvertJob(job)

    def GetConvertedJob(self):
        """
        Gibt den konvertierten Analyse-Job zurück.
        :return: Der konvertierte Job.
        :rtype: dict
        """
        return self.__convertedJob

    def GetTestStepPlots(self):
        """
        :return: die Test-Step ATX-RefPaths mit der Datei-Liste der Plots, welche in diesem
                 Test-Step erstellt wurden.
        :rtype: dict
        """
        return self.__imageProcessor.GetTestStepImages()

    def GetReviews(self, reportRefPath):
        """
        Gibt die Reviews des Packages zurück.
        :param reportRefPath: REF Pfad zum Report TestCase
        :type reportRefPath: str
        :return: Liste der Reviews
        :rtype: List->Review
        """
        return UpdateRefOnReviews(self.__reviews, reportRefPath)

    def __CreateReviewsForTraceStep(self, traceStep):
        """
        Ermittelt alle Nachbewertungen zu dem TraceStep und erzeugt für jede ein Review Objekt.
        :param traceStep: TraceStep, zu dem Nachbewertungen erfasst werden
        :type traceStep: ReportItem
        """
        self.__reviews.extend(GetReviewsForReportItem(self.__report, traceStep))

    def __ConvertJob(self, job):
        """
        Führt die Konvertierung aus.
        :param job: Der zu konvertierende Job.
        :type job: AnalysisJobItem
        :return: Liste mit TestSteps
        :rtype: list
        """
        tmpDir = tempfile.mkdtemp(prefix=u'plotArchive_')

        # initial node, taking all depth=0 nodes
        rootNode = None

        if self.__createTestSteps:
            for traceItem in job.IterTraceItems():
                """
                @type traceItem: lib.report.db.ReportItem.ReportItem
                """
                reportId = int(traceItem.GetReportItemId())
                result = FilterSUCCESS(traceItem.GetResult())
                name = traceItem.GetActivity()
                execLevel = traceItem.GetExecLevel()

                # Falls noch kein Root-Knoten vorhanden ist wird er angelegt (erster valider
                # Iterationsschritt)
                if not rootNode:
                    # root Knoten bekommt als SHORT-NAME den Ref Pfad seines TestCases
                    # -> wird im else von Node.getRefPath() abgerufen
                    rootNode = Node(execLevel - 1, {u'SHORT-NAME': self.__refPath})

                plots = self.__imageProcessor.GetImageFilesForTestStep(reportId, traceItem, tmpDir)

                # CATEGORY für die Plots/Images in den ATX TEST-STEPS festlegen
                args = {u'id': reportId,
                        u'verdict': result,
                        u'longName': name,
                        u'category': u"TRACE_ANALYSIS_PLOT" if len(plots) > 0 else False}
                createdTestStep = self.__CreateTestStep(args)

                rootNode.AddNode(execLevel, createdTestStep)
                self.__CreateReviewsForTraceStep(traceItem)

                self.__imageProcessor.ComputeImageRefPaths(plots,
                                                           rootNode,
                                                           createdTestStep[u'SHORT-NAME'])

        if rootNode:
            stepLists = rootNode.GetList()
            if len(stepLists[u'testSteps']) > 0:
                if stepLists[u'testSteps'][0][u'@type'] == u'TEST-STEP':
                    # Die Traceanalyse wurde nicht ausgeführt, aber erstellt
                    # Daher eine "leere" Traceanalyse erzeugen
                    # --> TestStepFolder ohne Kinder
                    stepLists[u'testSteps'][0][u'@type'] = u'TEST-STEP-FOLDER'
                    stepLists[u'testSteps'][0][u'*TEST-STEPS'] = []
                    stepLists[u'reportSteps'][0][u'@type'] = u'TEST-STEP-FOLDER'
                    stepLists[u'reportSteps'][0][u'*TEST-STEPS'] = []

            return stepLists

        return False

    def __CreateTestStep(self, args):
        """
        Erzeugt aus den übergebenen Argumenten das TestStep Dict.
        :param args: Parameter für einen TestStep.
        :type args: dict
        :return: TestStep Objekt.
        :rtype: dict
        """
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

        return ret
