# -*- coding: utf-8 -*-

'''
Created on 13.10.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''


from datetime import datetime
import zipfile
import glob
import os

from lib.PathHandler import IsSubpath
from log import DPrint, ExcPrint, LEVEL_VERBOSE

from .Config import Config


class ScanReportDir(object):
    '''
    Erstellt eine komprimierte Zip Datei im aktuellen Report-Verzeichnis mit den Dateien,
    welche anhand der Nant Pattern der config.xml gefunden werden. Das Suchverzeichnis ist
    ebenfalls das Report-Verzeichnis. Die erzeugte Zip Datei spiegelt die relative
    Verzeichnisstruktur im Report Dir wider, wobei leere Verzeichnisse nicht übernommen werden.
    '''

    def __init__(self, reportApi, api, scanDir, fileExp):
        '''
        Konstruktor.
        @param reportApi: Report API Objekt
        @type reportApi: ReportApi
        @param api: Zugriff auf die API um an das aktuelle TestReport-Verzeichnisse zu gelangen.
        @type api: application.api.Api.Api
        @param scanDir: Verzeichnis, welches durchsucht werden soll.
        @type scanDir: str
        @param fileExp: Expression der Form **/*.zip;*.log welche angewandet werden soll
                        auf das zu durchsuchende Verzeichnis.
        @type fileExp: str
        '''
        self.__scanDir = scanDir
        canArchiveMiscFiles = self.__CanArchiveMiscFiles(reportApi, api)

        self.__distinctFilesFound = []

        if canArchiveMiscFiles and fileExp:

            discoveredFiles = []

            for searchExpression in fileExp.split(';'):
                discoveredFiles.extend(self.__ExecuteSearchExpression(scanDir, searchExpression))

            for fileItem in set(discoveredFiles):
                self.__AddArchiveFile(scanDir, fileItem)

            DPrint(LEVEL_VERBOSE,
                   u"ScanReportDir {1}: distinctFilesFound={0}".format(self.__distinctFilesFound,
                                                                       scanDir))

        else:
            DPrint(LEVEL_VERBOSE,
                   (u"Did not scan the 'misc files'. "
                    u"canArchiveMiscFiles={0} "
                    u"fileExpression={1} ").format(canArchiveMiscFiles, fileExp)
                   )

    def __CanArchiveMiscFiles(self, reportApi, api):
        '''
        Überprüft zum Einen ob nur aus dem aktuellen Report-Verzeichnis überhaupt Archiv-Dateien
        angezogen werden dürfen und ob es sich beim dem aktuellen Report-Verzeichnis überhaupt
        um ein ECU-TEST Report-Verzeichnis handelt oder ob die TRF z.B. im Downloads-Ordner von
        Windows geöffnet wurde.
        @param reportApi: Report API Objekt
        @type reportApi: ReportApi
        @param api: Zugriff auf die API um an das aktuelle TestReport-Verzeichnisse zu gelangen.
        @type api: application.api.Api.Api
        @return: True, wenn anderen Daten mit archiviert werden sollen und können, sonst False.
        @rtype: boolean
        '''

        archiveOnlyInTestRpeortFolder = Config.GetSetting(
            reportApi, u'archiveMiscFilesOnlyInTestReportDir') == u'True'

        result = True
        if archiveOnlyInTestRpeortFolder:
            # 1. Heuristik für die Erkennung
            # Prüfen ob die TRF im aktuellen Testreport-Verzeichnis ist.
            result = IsSubpath(api.GetSetting(u"reportPath"), reportApi.GetReportDir())

            # 2. Heuristik für die Erkennung
            # Prüfe ob es sich um einen ECU-TEST Report-Ordner handeln kann.
            if not result:
                trf = reportApi.GetDbFile()
                result = self.__CheckIsTestReportDirOnDirnameHeuristic(trf)
                if not result:
                    result = self.__CheckIfGrandParentDirIsValidTestReportDir(trf)

        return result

    def __CheckIsTestReportDirOnDirnameHeuristic(self, trf):
        '''
        Prüfe ob es zu der aktuellen TRF das passende TRF-Basisverzeichnis gibt
        z.B.: TestReports\\AttributChoice_2016-09-14_225305\\AttributChoice.trf
        AttributChoice.trf -> AttributChoice_2016-09-14_225305 -> True
        Ist eine Lösungstrategie für die Option archiveMiscFilesOnlyInTestReportDir.
        @param trf: Pfad zu der aktuellen TRF-Datei, welche zur Prüfung verwendet werden soll
        @type trf: str
        @return: True, wenn es zu der TRF-Datei auch den passenden TRF-Report-Ordner gibt, sonst
                 False
        @rtype: boolean
        '''
        result = False
        if trf and os.path.exists(trf):
            trfNameWithoutExt = os.path.splitext(os.path.basename(trf))[0]
            parentTrfDir = os.path.dirname(trf)
            parentTrfDirname = os.path.basename(parentTrfDir)

            if parentTrfDirname.startswith(trfNameWithoutExt):
                result = True

        return result

    def __CheckIfGrandParentDirIsValidTestReportDir(self, trf):
        '''
        Wenn der aktuelle TestReport-Ordner nicht passt, dann schau mal ob es sich um
        ein SubProjekt mit extra Reportnamen handelt, indem im Parent-Ordner
        nachgeschaut wird ob eine TRF mit dem entsprechenden Ordnernamen vorhanden ist.
        Ist eine Lösungstrategie für die Option archiveMiscFilesOnlyInTestReportDir.
        @param trf: Pfad zu der aktuellen TRF-Datei, welche zur Prüfung verwendet werden soll
        @type trf: str
        @return: True, wenn es zu der TRF-Datei auch den passenden übergeordneten TRF-Report-Ordner
                 gibt, sonst False
        @rtype: boolean
        '''
        result = False
        if trf and os.path.exists(trf):
            grandParentTRFDir = os.path.dirname(os.path.dirname(trf))
            for each in os.listdir(grandParentTRFDir):
                eachFile = os.path.join(grandParentTRFDir, each)
                if eachFile.lower().endswith(u".trf"):
                    if self.__CheckIsTestReportDirOnDirnameHeuristic(eachFile):
                        result = True
                        break
        return result

    def GetScannedFiles(self):
        '''
        @return: Liste der ermittelten Dateipfade.
        @rtype: list
        '''
        return [os.path.join(self.__scanDir, each) for each in self.__distinctFilesFound]

    def CreateZipArchive(self, zipFilePrefix, targetdir):
        '''
        Erzeugt eine Zip-Datei mit den gefundenen Dateien ggfs. mit dem gewünschten Präfix
        im angegebenen Ordner und gibt den Pfad zur generierten Zip Datei zurück.
        @param zipFilePrefix: Präfix der Zip-Datei, die sonst als Name einen Zeitstempel erhält.
        @type zipFilePrefix: str
        @param targetdir: Pfad zum Zielverzeichnis, wo die Datei erstellt werden soll.
        @type targetdir: str
        @return: Pfad der erstellten Zip Datei oder None, wenn keine Dateien gefunden wurden.
        @rtype: str oder None
        '''
        result = None
        if self.__distinctFilesFound:
            try:
                fileName = u"{0}{1}".format(zipFilePrefix,
                                            datetime.now().strftime(u'%Y-%m-%d_%H%M%S'))
                result = os.path.join(targetdir, u'{file}.zip'.format(file=fileName))

                with zipfile.ZipFile(result, u'w',
                                     zipfile.ZIP_DEFLATED, True) as zipHandler:
                    for path in self.__distinctFilesFound:
                        toZipFile = os.path.join(self.__scanDir, path)
                        if os.path.isfile(toZipFile):
                            zipHandler.write(toZipFile, path)
            except BaseException as err:
                ExcPrint()
                raise err

        return result

    def __ExecGlob(self, dbDir, modifiedExpr):
        '''
        Führt einen Nant Ausdruck im aktuellen übergebenen Verzeichnis aus.
        @param dbDir: Verzeichnis in welchem gesucht werden soll.
        @type: dbDir: str
        @param modifiedExpr: Nant Ausdruck
        @type modifiedExpr: str
        '''
        filesFoundByGlob = []

        if u"[" in dbDir:
            dbDir = dbDir.replace(u'[', u'[[]')

        for discoveredPath in glob.glob(os.path.join(dbDir, modifiedExpr)):

            discoveredRelPath = os.path.relpath(discoveredPath, dbDir)

            if os.path.isfile(discoveredPath):
                filesFoundByGlob.append(discoveredRelPath)
            elif os.path.isdir(discoveredPath):
                # alle rel. Pfade für Dateien und Unterordner rekursiv hinzufügen
                for folder, __, files in os.walk(discoveredPath):
                    for fileName in files:
                        relDir = os.path.relpath(folder, discoveredPath)
                        relFile = os.path.join(relDir, fileName)
                        subDir = folder.replace(discoveredPath, u"")
                        filesFoundByGlob.append(os.path.normpath(os.path.join(discoveredRelPath,
                                                                              subDir,
                                                                              relDir,
                                                                              relFile)))
        return filesFoundByGlob

    def __ExecuteSearchExpression(self, dbDir, expr):
        '''
        Vorverarbeitung des Nant Ausdrucks: Zwei-Sternchen-Operatoren "**" werden in einer
        Schleife in 1 bis 10 einzelne Sternchen ersetzt und für jeden Durchlauf ausgeführt.
        @param dbDir: Verzeichnis in welchem gesucht werden soll.
        @type: dbDir: str
        @param expr: einzelner Nant Ausdruck
        @type expr: str
        @return: Liste der gefundenen Pfade
        @rtype: list->str
        '''
        filesFound = []

        if u'**' in expr:
            if u'**/' in expr:
                expr = expr.replace(u'**/', u'**')

            for i in range(1, 10):
                rexpr = expr.replace(u'**', u'*/' * i)
                filesFound.extend(self.__ExecGlob(dbDir, rexpr))
        else:
            filesFound.extend(self.__ExecGlob(dbDir, expr))
        return filesFound

    def __AddArchiveFile(self, dbDir, path):
        '''
        Fügt den Pfad zur Liste der gefundenen Pfade hinzu, wenn er noch nicht enthalten ist.
        @param dbDir: Verzeichnis in welchem der Pfad zulässig ist.
        @type: dbDir: str
        @param path: Pfad einer Datei
        @type path: str
        '''
        if path not in self.__distinctFilesFound:

            # Prüfung das keine Bestands ATX-Verzeichnisse erneut erfasst werden, die von einer
            # vorherigen Generierung noch vorhanden sind
            checkHasMappingXml = False
            checkHasReportXml = False

            # Nur prüfen wenn ATX im Pfad vorhanden
            if u"ATX" in path:
                try:
                    # Datei gleich direkt prüfen
                    if u"mapping.xml" in path:
                        checkHasMappingXml = True

                    if u"report.xml" in path:
                        checkHasReportXml = True

                    # relatives Stammverzeichnis ermitteln
                    rootDir = path[:path.index(os.sep)] if os.sep in path else path
                    for __, __, filenames in os.walk(os.path.join(dbDir, rootDir)):

                        # Prüfe ob mapping.xml bekannt ist
                        if not checkHasMappingXml and u"mapping.xml" in filenames:
                            checkHasMappingXml = True

                        # Prüfe ob report.xml bekannt ist
                        if not checkHasReportXml and u"report.xml" in filenames:
                            checkHasReportXml = True

                        # Wenn mapping.xml und report.xml gefunden wurden, dann handelt es sich um
                        # ATX-Reportverzeichnis und es sollte keine weiteren Daten daraus extrahiert
                        # werden.
                        if checkHasMappingXml and checkHasReportXml:
                            break
                except BaseException:
                    # Falls es bei der Pfad-Ermittlung zu einem Fehler kommt, kann dieser ignoriert
                    # werden, da ggfs. nur mehr Dateien angezogen werden, als notwendig.
                    ExcPrint()

            # Wenn report.xml noch mapping.xml im Dateipfad gefunden wurde, dann hinzufügen
            if not checkHasMappingXml and not checkHasReportXml:
                self.__distinctFilesFound.append(path)
