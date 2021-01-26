# -*- coding: utf-8 -*-

'''
Created on 07.02.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''

import errno
import os
import glob
import threading
import zipfile
import shutil
from pkg_resources import parse_version
import requests
import urllib3  # Python 2.7 und Python 3 kompatibel

from application.api.Api import Api
from log import EPrint, WPrint, SPrint, DPrint, LEVEL_VERBOSE

from .ProcessReport import ProcessReport
from .Version import GetServerVersion, GetVersion, GetDownloadLinkForATXMako

from .Config import Config, SettingsFromServerMode
from .HttpUtils import CreateRequestProxySettings
from .ConfigDownloader import ConfigDownloader

# Die Handshake-Warnung deaktivieren, da sonst beim allen Kunden im Betriebssystem gültige
# Intranet-Zertifiakte für jedes TEST-GUIDE hinterlegt sein müssten!
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def ReportPackage(reportName, reportApi):
    '''
    Einstiegspunkt für die Reportgenerierung eines einzeln ausgeführten Packages.
    @param reportName: Name der erzeugten Datei, siehe config.xml.
    @type reportName: str
    @param reportApi: Aktuelles Objekt der ReportAPI.
    @type reportApi: ReportApi
    '''
    __InitProcessReport(reportApi, True)


def ReportProject(reportName, reportApi):
    '''
    Einstiegspunkt für die Reportgenerierung eines Projektes.
    @param reportName: Name der erzeugten Datei, siehe config.xml.
    @type reportName: str
    @param reportApi: Aktuelles Objekt der ReportAPI.
    @type reportApi: ReportApi
    '''
    __InitProcessReport(reportApi, False)


def __InitProcessReport(reportApi, isPackageExecution):
    '''
    Initialisiert die Reportgenerierung.
    @param reportApi: Aktuelles Objekt der ReportAPI.
    @type reportApi: ReportApi
    @param isPackageExecution: Handelt es sich um ein PackageReport.
    @type isPackageExecution: bool
    '''
    # Thread Lock setzen
    if not hasattr(Api(), "atxUpdateEvent"):
        Api().atxUpdateEvent = threading.BoundedSemaphore()

    try:
        atxReportTemplateDir = os.path.join(Api().GetSetting("templatePath"), "ATX")

        # Verbindungs-Settings (können nicht durch TG überschrieben werden)
        uploadToServer = Config.GetSetting(reportApi, 'uploadToServer')
        url = Config.GetSetting(reportApi, 'serverURL')
        serverLabel = Config.GetSetting(reportApi, 'serverLabel')
        useHttps = Config.GetSetting(reportApi, 'useHttpsConnection') == 'True'
        port = Config.Cast2Int(Config.GetSetting(reportApi, 'serverPort'), 8085)
        contextPath = Config.GetSetting(reportApi, 'serverContextPath')
        authKey = Config.GetSetting(reportApi, 'uploadAuthenticationKey')
        proxies = CreateRequestProxySettings(reportApi)
        projectId = Config.GetSetting(reportApi, 'projectId')
        useSettingsFromServer = __GetSettingsFromServerMode(Config.GetSetting(reportApi, u'useSettingsFromServer'))
         
        if useSettingsFromServer in [SettingsFromServerMode.ALWAYS, SettingsFromServerMode.WHEREKEYWORD]:
            keyword = None
            if useSettingsFromServer == SettingsFromServerMode.WHEREKEYWORD:
                keyword = Config.GetSetting(reportApi, u'useSettingsFromServerKeyword')
            configDownloader = ConfigDownloader(authKey=authKey, url=url, port=port, contextPath=contextPath,
                                                proxies=proxies, projectId=projectId, useHttps=useHttps)
            serverSettings = configDownloader.DownloadConfig()
            Config.LoadExternalSettings(serverSettings, useSettingsFromServer, keyword)

        serverVersion = GetServerVersion(useHttps, url, port, contextPath, proxies)
        isAutoUpdate = Config.GetSetting(reportApi, 'autoATXGeneratorUpdate') == 'True'

        # Debugausgabe
        DPrint(LEVEL_VERBOSE, _(u"ATX-Generator für Report [{0}] wird mit folgenden "
                                u"Eigenschaften gestartet:\n"
                                u"serverLabel: {9}\n"
                                u"projectId: {10}\n"
                                u"serverURL: {1}\n"
                                u"serverPort: {2}\n"
                                u"serverContextPath: {3}\n"
                                u"autoATXGeneratorUpdate: {4}\n"
                                u"useHttpsConnection: {5}\n"
                                u"serverVersion: {6}\n"
                                u"reportGenVersion: {7}\n"
                                u"uploadToServer: {8}\n"
                                u"authKey: {11}\n").format(reportApi.GetDbFile(),
                                                           url,
                                                           port,
                                                           contextPath,
                                                           isAutoUpdate,
                                                           useHttps,
                                                           serverVersion,
                                                           GetVersion(),
                                                           uploadToServer,
                                                           serverLabel,
                                                           projectId,
                                                           u"****" if authKey else u""))

        hasServerConnection = (serverVersion != u"0.0.0")
        hasSameVersion = parse_version(serverVersion) == parse_version(GetVersion())

        # Wenn Verbindung besteht und Update notwendig und verlangt, dann durchführen.
        if hasServerConnection and isAutoUpdate and not hasSameVersion:
            # Alle ATX-Reportgeneratoren an der Stelle fürs Auto-Update synchronisieren
            Api().atxUpdateEvent.acquire()

            SPrint(_(u"ATX AutoUpdate {1} wird gestartet für Update "
                     u"auf Generator v{0} ...").format(serverVersion,
                                                       (_(u"(Server: {0})").format(serverLabel)
                                                        if serverLabel else u"")))

            # Update durchführen
            if __AutoUpdate(atxReportTemplateDir, proxies, useHttps, url, port, contextPath,
                            authKey):
                # Neuen Generator mit alter Config in dem Update-Thread anstarten
                from lib.report.handler.python.PythonHandler import PythonHandler
                handler = PythonHandler.CheckDir(PythonHandler, atxReportTemplateDir)

                # Freigeben für nächsten Thread der im folgenden 'handler' aufgerufen wird
                Api().atxUpdateEvent.release()

                # Wenn es sich um eine Liste handelt, dann sind Fehlermeldungen hinterlegt.
                if isinstance(handler, list):
                    EPrint(u"ATX PythonHandler Errors: {0}".format(handler))
                else:
                    if reportApi.IsProjectReport():
                        handler.RenderProject(reportApi)
                    else:
                        handler.RenderPackage(reportApi)
            else:
                EPrint(_(u"ATX-Generierung mit Upload war nicht möglich!"))
                # Freigeben für nächsten Thread
                Api().atxUpdateEvent.release()
        else:
            # Report normal verarbeiten
            ProcessReport(reportApi, isPackageExecution)
    except BaseException as err:
        # Exception wird ganz außen gefangen und dokumentiert
        # Die Generierung des Reports ist damit gescheitert
        EPrint(u"InitProcessReport failed: {0}".format(err))


def __AutoUpdate(atxReportTemplateDir, proxies, useHttps, hostUrl, port, contextUrl, authKey):
    '''
    Lädt die passende ATX Version vom Server und entpackt diese in Templateverzeichnis des
    Workspaces und aktualisert dann nachfolgenden Module für die Weiterverarbeitung.
    @param atxReportTemplateDir: Verzeichnis in welchem der neue ATX-Generator liegen soll.
    @type atxReportTemplateDir: str
    @param proxies: Dict mit dem Mapping der Protokolle bei Verwendung eines Proxies
    @type proxies: dict
    @param useHttps: True, wenn eine Https-Verbindung verwendet werden soll, sonst False.
    @type useHttps: boolean
    @param hostUrl: Haupt-URL
    @type hostUrl: str
    @param port: Port
    @type port: integer
    @param contextUrl: Context-URL (kann u.U. auch leer sein)
    @type contextUrl: str
    @param authKey: Authentifizierungsschlüssel für den Download
    @type authKey: str
    @return: True, wenn das AutoUpdate erfolgreich war, sonst False.
    @rtype: boolean
    '''
    # Nach erfolgreichem Download und entpacken die Module aktualisieren
    if __DownloadAndUnZipATXMakoInTemplateDir(atxReportTemplateDir, proxies, useHttps, hostUrl,
                                              port, contextUrl, authKey):
        # ReportManager aktualisieren
        from lib.report.ReportManager import ReportManager
        ReportManager().UpdateHandler()
        SPrint(_(u"ATX AutoUpdate ist erfolgt."))
        return True
    else:
        EPrint(_(u"ATX AutoUpdate fehlgeschlagen!"))
        return False


def __DownloadAndUnZipATXMakoInTemplateDir(targetZipDir, proxies, useHttps, hostUrl, port,
                                           contextUrl, authKey):
    '''
    Downloaded das passende Mako vom Server und entpackt die Version im Workspace
    Templateverzeichnis und entfernt wieder die Zip.
    @param targetZipDir: Verzeichnis in welches das Zip entpackt werden soll.
    @type targetZipDir: str
    @param proxies: Dict mit dem Mapping der Protokolle bei Verwendung eines Proxies
    @type proxies: dict
    @param useHttps: True, wenn eine Https-Verbindung verwendet werden soll, sonst False.
    @type useHttps: boolean
    @param hostUrl: Haupt-URL
    @type hostUrl: str
    @param port: Port
    @type port: integer
    @param contextUrl: Context-URL (kann u.U. auch leer sein)
    @type contextUrl: str
    @param authKey: Authentifizierungsschlüssel für den Download
    @type authKey: str
    @return: True, wenn Download erfolgreich, sonst False.
    @rtype: boolean
    '''
    try:
        # Download der aktuellen Mako in maximal 90s .
        response = requests.get(
            GetDownloadLinkForATXMako(useHttps, hostUrl, port, contextUrl, authKey),
            timeout=90,
            verify=False,
            proxies=proxies
        )

        # Download
        downloadTarget = os.path.join(Api().GetSetting(u"templatePath"), u"ATX.zip")
        
        try:
            os.makedirs(os.path.dirname(downloadTarget))
        except OSError as e:
            if errno.EEXIST != e.errno:
                raise

        with open(downloadTarget, u'wb') as output:
            output.write(response.content)

        # Bestands-Generator feststellen
        if os.path.isdir(targetZipDir):

            # Wenn Verzeichnis bereits vorhanden, dann Python-Inhalte löschen,
            # damit Templates nicht zugemüllt wird
            files = glob.glob(os.path.join(targetZipDir, "*.py*"))
            try:
                for each in files:
                    os.remove(each)

                # Python 3 File-Cache löschen
                pyCacheDir = os.path.join(targetZipDir, "__pycache__")
                if os.path.exists(pyCacheDir):
                    shutil.rmtree(pyCacheDir, ignore_errors=False)

            except BaseException as err:
                WPrint(u"ATX folder file could not removed: {0}".format(err))
                # Fallback, falls das einzelne Löschen nicht möglich ist.
                if os.path.exists(targetZipDir):
                    shutil.rmtree(targetZipDir, ignore_errors=False)

        # Unzip
        with zipfile.ZipFile(downloadTarget) as zf:
            zf.extractall(targetZipDir)

        # Remove Zip-File
        os.remove(downloadTarget)

        return True
    except BaseException as err:
        EPrint(u"ATX Zip Update failed: {0}".format(err))
        return False

def __GetSettingsFromServerMode(setting):
    '''
    Wandelt den Konfigurationsparameter in ein Objekt um.
    @param setting: Wert der Konfigurationsparameter "useSettingsFromServer"
    @type setting: str
    @return: SettingsFromServerMode oder None
    @rtype: SettingsFromServerMode
    '''
    if not setting:
        return None
    setting = setting.lower()
    setting = setting.replace(u'true', SettingsFromServerMode.ALWAYS)
    setting = setting.replace(u'false', SettingsFromServerMode.NEVER)
    return SettingsFromServerMode.of(setting)