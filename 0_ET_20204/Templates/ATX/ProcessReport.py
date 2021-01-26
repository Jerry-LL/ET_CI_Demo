# -*- coding: utf-8 -*-

'''
Created on 23.09.2014

@author: Philipp
'''
import io
import os
import shutil
import datetime
import sys
import traceback

from pkg_resources import parse_version

from log import EPrint, WPrint, DPrint, LEVEL_NORMAL
from application.api.Api import Api

from .Version import GetVersion, GetServerVersion, GetDownloadLinkForATXMako
from .Config import Config
from .HttpUtils import CreateRequestProxySettings
from .ConvertReportToATX import ConvertReportToATX
from .UploadManager import UploadManager
from .ZipArchive import ZipArchive
from .ScanReportDir import ScanReportDir
from .Utils import (GetExtendedWindowsPath, EmptyReportException, SameNameError,
                    ShowInfoOnTaskManager, DefectClassException)

if sys.version_info < (3,):
    str = unicode


def ProcessReport(reportApi, isPackageExecution):
    '''
    Führt die Reportgenerierung aus.
    @param reportApi: Aktuelles Objekt der ReportAPI.
    @type reportApi: ReportApi
    @param isPackageExecution: Handelt es sich um ein PackageReport.
    @type isPackageExecution: bool
    '''
    if not isinstance(isPackageExecution, bool):
        EPrint(u'isPackageExecution ist kein boolscher Wert!')
        return

    # Generierung startet
    DPrint(LEVEL_NORMAL,
           _(u"ATX-Dokument aus Report [{1}] mit Generator v{0} "
             u"wird erstellt...").format(GetVersion(), reportApi.GetDbFile()))
    startGenerateTime = datetime.datetime.now()

    try:
        url = Config.GetSetting(reportApi, u'serverURL')
        port = int(Config.GetSetting(reportApi, u'serverPort'))
        contextPath = Config.GetSetting(reportApi, u'serverContextPath')
        useHttps = Config.GetSetting(reportApi, u'useHttpsConnection') == u'True'
        proxies = CreateRequestProxySettings(reportApi)
        serverVersion = GetServerVersion(useHttps, url, port, contextPath, proxies)
        authKey = Config.GetSetting(reportApi, u'uploadAuthenticationKey')

        hasServerConnection = (serverVersion != u"0.0.0")
        hasSameVersion = parse_version(serverVersion) == parse_version(GetVersion())

        warnMsgNotUpToDateVer = _(u"Der verwendete ATX-Reportgenerator v{0} ist "
                                  u"ungleich der Version {1} welche vom Server gefordert "
                                  u"wird!\n"
                                  u"Die passende Version steht zum Download bereit unter:\n{2}\n"
                                  u"Nach dem Download den Ordner ATX im Workspace im eingestellten "
                                  u"Template-Verzeichnis '{3}' ablegen/ersetzen."
                                  u".").format(GetVersion(), serverVersion,
                                               GetDownloadLinkForATXMako(useHttps,
                                                                         url,
                                                                         port,
                                                                         contextPath,
                                                                         authKey),
                                               Api().GetSetting(u"templatePath"))

        # Warnung mit Downloadlink zur Server-Mako-Version anbieten.
        if hasServerConnection and not hasSameVersion:
            WPrint(warnMsgNotUpToDateVer)

        splitter = reportApi.GetDbDir().rfind(u'\\')
        zipFileName = reportApi.GetDbDir()[splitter + 1:]

        try:
            worker = ConvertReportToATX(reportApi, GetVersion(), isPackageExecution)
        except EmptyReportException:
            # Der Report hat keine verwertbaren Testcases erzeugt und daher wird die Generierung
            # abgebrochen
            WPrint(_(u'Der Report enthält keine Testfalldaten und wird daher verworfen.'))
            return

        # Wenn Target Verzeichnis nicht bereits angelegt, dann anlegen.
        targetDir = GetExtendedWindowsPath(reportApi.GetReportDir())
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)

        atxFileName = u'report.xml'
        atxFilePath = os.path.join(targetDir, atxFileName)

        # ATX-Datei anlegen und befüllen.
        worker.CreateATXXmlFile(atxFilePath)

        ShowInfoOnTaskManager(reportApi, _(u"Zip-Archiv für Upload wird erstellt..."))

        zipFileNameWithExtension = u'{0}.zip'.format(zipFileName)

        fileList = worker.GetFiles()

        # Zusätzliche Dateien aus dem Report Verzeichnis anziehen: eine Zip erstellen
        dbDir = reportApi.GetDbDir()
        reportDir = reportApi.GetReportDir()
        archiveMiscFiles = Config.GetSetting(reportApi, u'archiveMiscFiles').strip()
        archiveMiscPrefix = Config.GetSetting(reportApi, u'archiveMiscFilePrefix').strip()

        additionalFilesZipPath = ScanReportDir(reportApi, Api(),
                                               dbDir,
                                               archiveMiscFiles,
                                               ).CreateZipArchive(archiveMiscPrefix, reportDir)

        # Ref Pfade sammeln und jeden Testcase mit der Zip verknüpfen
        if additionalFilesZipPath:
            refs = []
            for item in fileList:
                if item[u'ref'] not in refs:
                    refs.append(item[u'ref'])
                    fileList.append({u'file': additionalFilesZipPath,
                                     u'ref': item[u'ref'], u'comment': None,
                                     u'refPathType': u"TEST-CASE",
                                     u'removeFileAfterZipped': False})

        # **** ZIP mit ATX Xml, Mapping Xml, TRF usw. erstellen
        zipArchive = ZipArchive(reportApi, zipFileNameWithExtension, atxFilePath,
                                fileList, worker.GetReviews())
        if not zipArchive.Make():
            # Fehler bei der Erstellung des Zip
            EPrint(_(u'Fehler beim Erstellen des Zip-Archivs.'))
        else:
            # Temp-Dateien ggf. löschen
            __CleanUpArchiveFiles(fileList)

        # Generierung erfolgt
        endGenerateTime = datetime.datetime.now()
        DPrint(LEVEL_NORMAL,
               _(u"ATX-Dokument aus Report [{1}] mit Generator v{0} "
                 u"erzeugt (Dauer: {2}).").format(
                   GetVersion(), reportApi.GetDbFile(),
                   str(endGenerateTime - startGenerateTime).split('.')[0]))

        # Upload zum Server
        if Config.GetSetting(reportApi, u'uploadToServer') == u'True':

            ShowInfoOnTaskManager(reportApi, _(u"Daten werden hochgeladen..."))

            # Prüfe Option nur Projekte hochladen
            optionUploadOnlyPrjs = u'uploadOnlyProjectReport'
            if Config.GetSetting(reportApi, optionUploadOnlyPrjs) == u"True" and isPackageExecution:
                DPrint(LEVEL_NORMAL,
                       _(u"ATX Upload übersprungen"),
                       _(u"Option '{0}' ist aktiviert.").format(optionUploadOnlyPrjs))
                return

            # Prüfe Verbindung
            if not hasServerConnection:
                EPrint(_(u"ATX Upload abgebrochen! Keine Verbindung zum Server möglich, bitte "
                         u"Einstellungen überprüfen."))
                return

            # Versionsabgleich -> bei Fehler abbrechen
            if not hasSameVersion:
                EPrint(_(u"ATX Upload abgebrochen! {0}").format(warnMsgNotUpToDateVer))
                return

            uploader = UploadManager(reportApi, GetVersion(), u'file-upload',
                                     zipFileNameWithExtension, zipArchive.GetZipFilePath(), u'json',
                                     url, port, useHttps=useHttps, contextPath=contextPath)
            if uploader.StartUpload():
                # Wenn alles erfolgreich war und gewünscht, dann Dateien wieder löschen
                if Config.GetSetting(reportApi, u'cleanAfterSuccessUpload') == u'True':
                    ShowInfoOnTaskManager(reportApi, _(u"Aufräumarbeiten werden durchgeführt..."))
                    shutil.rmtree(targetDir, True)
    except SameNameError as ne:
        # Exception wird ganz außen gefangen und dokumentiert
        # Die Generierung des Reports ist damit gescheitert
        errorMessage = _(u'Der Name {0} wird sowohl für eine Datei und für einen Ordner auf der '
                         u'selben Dateiebene verwendet. Dies ist für ATX-Darstellung nicht '
                         u'zulässig.'
                         u'Bitte benennen Sie den Ordner oder das Package um.').format(ne)
        with io.open(
                os.path.join(u'\\\\?\\' + reportApi.GetReportDir(), u'error.log'),
                u'w', encoding=u"utf-8") as fh:
            fh.write(errorMessage)
        EPrint(errorMessage)
    except DefectClassException as ex:
        EPrint(u'Only one defect class per review accepted. '
               u'The defect class "{0}" could not be assigned.'.format(ex.defectClass))
    except BaseException as ex:
        # Exception wird ganz außen gefangen und dokumentiert
        # Die Generierung des Reports ist damit gescheitert
        EPrint(u'Exception in process report:\r\n{0}\r\n{1}'.format(ex, traceback.format_exc()))


def __CleanUpArchiveFiles(fileList):
    '''
    Cleanup durchführen, von Dateien die zwar für den Upload erstellt wurden wie z.B. Plots, aber
    nach dem Zippen nun nicht mehr benötigt werden.
    @param fileList: Dict mit den Dateien, welche im ZIP hinterlegt wurden und nun ggf. gelöscht
                     werden können.
    @type fileList: dict
    '''
    for each in fileList:
        if each.get(u"removeFileAfterZipped", False):
            toRemove = each.get(u'file')
            try:
                if toRemove is not None and os.path.exists(toRemove):
                    os.remove(toRemove)

                    # Leere erstellte Parent-Ordner löschen (maximal zwei Ebenen nach oben!)
                    parentRemoveCounter = 0
                    tmpDir = os.path.dirname(toRemove)
                    while parentRemoveCounter < 2:
                        parentRemoveCounter += 1
                        shutil.rmtree(tmpDir, True)
                        # Nächstes Parent ermitteln
                        tmpDir = os.path.dirname(tmpDir)

            except BaseException as ex:
                EPrint(_(u"Löschen der Datei {0} nicht möglich: {1}").format(toRemove, ex))
