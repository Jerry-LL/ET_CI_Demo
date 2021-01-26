# -*- coding: utf-8 -*-
'''
Created on 16.04.2020

@author: Philipp
'''
import os
import tempfile

# ImageEntity wird in einem isinstance()-Ausdruck benutzt. Daher funktioniert FakeApiModules
# nicht.
try:
    # ab ECU-TEST 8.1
    from tts.core.report.db.ImageEntity import ImageEntity
except ImportError:
    # bis ECU-TEST 8.0
    from lib.report.db.ImageEntity import ImageEntity

from log import EPrint


class ProcessTestStepImage():
    '''
    Extrahiert aus den übergebene TestStep-ReportItems alle enthaltenen Images und stellt diese
    für den Upload bereit, nachdem Sie mit dem TestStep-Ref-Path verknüpft wurden.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.__images = {}

    def GetTestStepImages(self):
        """
        :return: die Test-Step ATX-RefPaths mit der Datei-Liste der Bilder, welche in diesem
                 Test-Step erstellt wurden.
        :rtype: dict
        """
        return self.__images

    def GetImageFilesForTestStep(self, reportId, reportItem, tmpDir=None):
        """
        Ermittelt ob in dem aktuellen TestStep Images enthalten sind und wenn ja, werden
        diese als Liste mit Pfadzugriff zurückgegeben.
        :param reportId: eindeutige ID des TEST-STEPS, welches für die Erzeugung des Verzeichnisses
                         für die Ploterstellung verwendet wird.
        :type reportId: int
        :param reportItem: aktuelles ReportItem
        :type reportItem: tts.core.report.db.ReportItem.ReportItem
        :param tmpDir: Verzeichnis, in welchem die Images erstellt werden sollen. Wenn keins
                       angegeben wird automatisch ein Temp-Verzeichnis angelegt.
        :type tmpDir: str
        :return: Liste der Pfade zu den Plots, welche zu diesem TestStep gehören.
        :rtype: list
        """
        result = []
        if reportItem.HasEntities():
            for each in reportItem.IterEntities():
                if isinstance(each, ImageEntity):

                    try:
                        if not tmpDir:
                            tmpDir = tempfile.mkdtemp(prefix=u'imageArchive_')

                        imageDir = os.path.join(tmpDir, u"{0}".format(reportId))
                        if not os.path.exists(imageDir):
                            os.mkdir(imageDir)

                        imagePath = each.ToFile(imageDir)

                        # Wenn das Image keine Extension hat, dann automatisch PNG zuweisen
                        pathSplit = os.path.splitext(imagePath)
                        if len(pathSplit) == 2 and len(pathSplit[1]) < 3:
                            tempImagePath = u"{0}.png".format(imagePath)
                            # Wenn gleiche Datei mehrfach erfasst wird, dann nicht erneut
                            # umbenennen.
                            if not os.path.exists(tempImagePath):
                                os.rename(imagePath, tempImagePath)
                            imagePath = tempImagePath

                        result.append(imagePath)

                    except BaseException as err:
                        EPrint(u'GetImageFilesForTestStep error: {0}'.format(err))

        return result

    def ComputeImageRefPaths(self, images, rootNode, stepShortName):
        """
        Ermittelt zu den übergebenen Bildern und dem TEST-STEP die Zuweisung der Dateien über den
        RefPath der TEST-STEPS.
        :param images: Liste der Bilder, welche im TEST-STEP gefunden wurden.
        :type images: list
        :param rootNode: Root-Node, welcher durchsucht werden solle
        :type rootNode: Node
        :param stepShortName: eindeutiger TEST-STEP Shortname zu welchem die Bilder gesucht werden
                              sollen
        :type stepShortName: str
        """
        if len(images) > 0:

            def GetRefTestStepPath(prePath, steps):
                """
                Ermittelt den RefPath des gesuchten TEST-STEP-Shortnames,
                ausgehend vom Root Teststep.
                :param prePath: beim Abstieg erzeugter Ref Pfad 
                :type prePath: str
                :param steps: Liste mit den enthaltenen TEST-STEPS auf der Ebene
                :type steps: list
                :return: None oder den Ref-Path des TEST-STEPS.
                :rtype: str
                """
                result = None
                for eachStep in steps:
                    refPath = u'{0}/{1}'.format(prePath, eachStep[u'SHORT-NAME'])
                    if eachStep[u'SHORT-NAME'] == stepShortName:
                        return refPath
                    result = GetRefTestStepPath(refPath, eachStep.get(u'*TEST-STEPS', []))
                return result

            refPath = GetRefTestStepPath(u'', rootNode.GetList()[u'reportSteps'])
            if refPath is None:
                EPrint(u'Compute Report TEST-STEP RefPath failed!')
            else:
                if refPath not in self.__images:
                    self.__images[refPath] = []
                self.__images[refPath].extend(images)
