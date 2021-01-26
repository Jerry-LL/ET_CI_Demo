# -*- coding: utf-8 -*-

"""
Created on 21.02.2014

:author: Christoph Groß <christoph.gross@tracetronic.de>
"""

import json
import io
import mimetypes
import datetime
import os
import sys
import time
import uuid
from json import JSONEncoder

import requests
from requests import RequestException, HTTPError

from log import EPrint, SPrint, WPrint, DPrint, LEVEL_NORMAL
from .Config import Config
from .HttpUtils import CreateRequestProxySettings, CreateHttpUrl
from .Utils import ShowInfoOnTaskManager

try:
    # ECU-TEST >= 8.0
    from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
except ImportError:
    from .multipart_encoder import MultipartEncoder, MultipartEncoderMonitor

try:
    from urllib.parse import urlencode  # Python 3+
except ImportError:
    from urllib import urlencode  # Python 2.X

try:
    from urllib.parse import quote  # Python 3+
except ImportError:
    from urllib import quote  # Python 2.X

if sys.version_info < (3,):
    str = unicode
    time.monotonic = time.clock  # time.monotonic ist erst ab Python 3.3 verfügbar


class UploadError(Exception):
    '''
    Im Falle eines Upload-Erorrs werden die Fehler hier zusammengefasst und für das Logging
    zur Verfügung gestellt.
    '''

    def __init__(self, statusCode, reason, logEntries):
        self.statusCode = statusCode
        self.reason = reason
        self.logEntries = logEntries
        super(UploadError, self).__init__(statusCode, reason, logEntries)


class UploadManager(object):
    """
    Verwaltet den Upload von Dateien an den Web-Service.
    """

    TIME_BETWEEN_CAPTION_UPDATES = 0.5

    def __init__(self, reportApi, version, uploadFieldName, uploadFileName, uploadFilePath,
                 accept=u'json', url=u'127.0.0.1', port=8085,
                 path=u'api/upload-file', useHttps=False, contextPath=u''):
        """
        Konstruktor
        :param reportApi: Aktuelles Objekt der ReportAPI.
        :type reportApi: ReportApi
        :param version: Version des Generators und gleichzeitig die unterstützte API-Version.
        :type version: str
        :param uploadFieldName: Feld-Name für den Upload
        :type uploadFieldName: str
        :param uploadFileName: Dateiname für den Upload
        :type uploadFileName: str
        :param uploadFilePath: Dateipfad, also welche Datei hochgeladen werden soll.
        :type uploadFilePath: str
        :param accept: Gewünschter Content-Type der Antwort.
        :type accept: str
        :param url: Addresse des Wicket-Web-Service.
        :type url: str
        :param port: Port dess Wicket-Web-Service.
        :type port: int
        :param path: Relativer Pfad auf dem Server.
        :type path: str
        :param useHttps: True, wenn eine Https-Verbindung verwendet werden soll, sonst False.
        :type useHttps: boolean
        :param contextPath: Context-URL (kann u.U. auch leer sein)
        :type contextPath: str
        """
        self.__reportApi = reportApi
        self.__version = version
        self.__proxies = CreateRequestProxySettings(self.__reportApi)
        self.__url = url
        self.__port = port
        self.__path = u'{0}/{1}'.format(contextPath, path) if contextPath else path
        self.__uploadFieldName = uploadFieldName
        self.__uploadFileName = uploadFileName
        self.__uploadFilePath = uploadFilePath
        self.__useHttps = useHttps
        self.__contextPath = contextPath
        self.__accept = accept
        self.__boundary = uuid.uuid4().hex.encode()
        self.__serverLabel = Config.GetSetting(self.__reportApi, u'serverLabel')
        self.__projectId = Config.GetSetting(self.__reportApi, u'projectId')
        self.__uploadAsync = Config.GetSetting(self.__reportApi, u'uploadAsync') == u'True'
        self.__maxUploadTries = self.__GetConfigUploadTries()
        # Für Debug und Testzwecke
        self.__counterUploadTries = 0
        self.__lastRetryAfterPeriod = -1

    def __GetConfigUploadTries(self):
        '''
        :returns: Ermittelter Wert für die Upload-Versuche, wenn z.B. TEST-GUIDE gerade im
                 Wartungsmodus ist.
        :rtype: int
        '''

        def IsInteger(val):
            '''
            @return: True, wenn es sich bei dem übergebenen String um einen Integer handelt.
            '''
            try:
                int(val)
                return True
            except ValueError:
                return False

        result = Config.GetSetting(self.__reportApi, u'maxUploadTries')
        # Wenn Wert nicht gesetzt ist oder keine Zahl
        if not result or not IsInteger(result):
            result = 1

        result = int(result)

        # Wenn ein Wert <= 0 angegeben ist, dann heißt das unendliche Versuche
        if result <= 0:
            result = 9223372036854775807
            WPrint(_(u'ACHTUNG: ATX-Upload Versuche stehen auf unendlich!'))

        return result

    def GetMaxUploadTries(self):
        '''
        :returns: Die konfigurierten maximalen Upload-Versuche.
        :rtype: int
        '''
        return self.__maxUploadTries

    def __GetContentType(self, filename):
        """
        Bestimmt den Content-Type der Datei.
        :param filename: Zu untersuchende Datei.
        :type filename: str
        :returns: Content-Type der Datei.
        :rtype: str
        """
        return mimetypes.guess_type(filename)[0] or u'application/octet-stream'

    def GetHealthReadyUrl(self):
        """
        :returns: Gibt in Abhängigkeit ob HTTPS verwendet werden soll oder nicht die entsprechende
                  Health-Ready-URL an den ATX-Server zurück.
        :rtype: str
        """
        # Default URL Protocol wenn nix angegeben.
        urlProtocolPrefix = u'http://'

        # Wenn https gewünscht.
        if self.__useHttps:
            urlProtocolPrefix = u'https://'
        # /api/health/live
        return (u'{pro}{url}:{port}/{contextPath}api/health/ready').format(
            pro=urlProtocolPrefix,
            url=self.__url,
            port=self.__port,
            contextPath=(u'{0}/'.format(self.__contextPath)
                         if self.__contextPath else u''))

    def GetTargetUrl(self):
        """
        :returns: Gibt in Abhängigkeit ob HTTPS verwendet werden soll oder nicht die entsprechende
                  Upload-URL an den ATX-Server zurück.
        :rtype: str
        """
        # Default URL Protocol wenn nix angegeben.
        urlProtocolPrefix = u'http://'

        # Wenn https gewünscht.
        if self.__useHttps:
            urlProtocolPrefix = u'https://'

        # Authentifizierungsschlüssel für den Upload mitgeben.
        configAuthKey = Config.GetSetting(self.__reportApi, u'uploadAuthenticationKey')

        return (u'{pro}{url}:{port}/{path}'
                u'?apiVersion={version}'
                u'&authKey={authKey}'
                u'&projectId={projectId}'
                u'&async={isAsync}').format(pro=urlProtocolPrefix,
                                            url=self.__url,
                                            port=self.__port,
                                            path=self.__path,
                                            version=self.__version,
                                            authKey=configAuthKey,
                                            projectId=self.__projectId,
                                            isAsync=u'true' if self.__uploadAsync else u'false')

    def GetStatusUrl(self, statusPath):
        """
        Gibt in Abhängigkeit ob HTTPS verwendet werden soll oder nicht die entsprechende
        Status-URL des Uploads zurück.
        :param statusPath: Pfad zum aktiven Upload, den wir von TEST-GUIDE erhalten haben.
        :type statusPath: str
        :returns: Status-URL des aktiven Uploads
        :rtype: str
        """
        # Default URL Protocol wenn nix angegeben.
        urlProtocolPrefix = u'http://'

        # Wenn https gewünscht.
        if self.__useHttps:
            urlProtocolPrefix = u'https://'

        # Authentifizierungsschlüssel für den Upload mitgeben.
        configAuthKey = Config.GetSetting(self.__reportApi, u'uploadAuthenticationKey')

        return (u'{pro}{url}:{port}/{contextPath}{status}'
                u'?authKey={authKey}').format(pro=urlProtocolPrefix,
                                              url=self.__url,
                                              port=self.__port,
                                              contextPath=(u'{0}/'.format(self.__contextPath)
                                                           if self.__contextPath else u''),
                                              status=statusPath.lstrip(u'/'),
                                              authKey=configAuthKey)

    def __PostUpload(self, monitor, uploadTries):
        '''
        Lädt die Daten zu TEST-GUIDE und sorgt dafür, dass im Wartungsfall von TEST-GUIDE
        der Upload entsprechend der Einstellung versucht wird.
        :param monitor: MultipartEncoderMonitor für den Zugiff auf den Upload-Content
        :type monitor: MultipartEncoderMonitor
        :param uploadTries: Upload-Versuche
        :type uploadTries: int
        :returns: Erfolgreiche Response, Fehler Enden in einer HTTPError Exception.
        :rtype: requests.Response
        '''
        try:
            allowedRetryOnHttpStatus = (503, 429)

            self.__counterUploadTries = self.__counterUploadTries + 1

            # Vor dem Upload aller Daten an TEST-GUIDE -> unbedingt prüfen, ob der Server gerade
            # im Wartungsmodus ist, da sonst sinnlos die Daten übertragen werden!!!
            checkResponse = requests.get(url=self.GetHealthReadyUrl(), verify=False,
                                         proxies=self.__proxies)
            # Wenn die Prüfung mit einer 503 oder 429 antwortet, dann in Retry-After springen.
            # Alle anderen Servermeldungen ignorieren, die werden über HTTPError verarbeitet.
            if checkResponse.status_code in allowedRetryOnHttpStatus:
                checkResponse.raise_for_status()
            checkResponse.close()

            response = requests.post(
                url=self.GetTargetUrl(),
                data=monitor,
                headers={u'Accept': u'application/{accept}'.format(accept=self.__accept),
                         u'Content-Type': monitor.content_type},
                verify=False,
                proxies=self.__proxies)
            response.raise_for_status()
            return response
        except HTTPError as err:
            response = err.response
            # Im Wartungsfall und bei zuvielen Verbindungen,
            # erst nach Retry-After wieder versuchen.
            if (response.status_code in allowedRetryOnHttpStatus and
                    "Retry-After" in response.headers):
                retryAfterSec = self.ParseRetryAfter(response.headers["Retry-After"])

                # Wenn sinnvolles Retry-After angegeben, dann X Sekunden warten
                # Und das nur wenn Upload-Versuche noch erlaubt sind.
                if retryAfterSec >= 0 and uploadTries >= 2:

                    retryInfo = _(u'{0}. TEST-GUIDE Upload startet in {1}.').format(
                        self.__counterUploadTries, datetime.timedelta(seconds=retryAfterSec))
                    DPrint(LEVEL_NORMAL, retryInfo)
                    ShowInfoOnTaskManager(self.__reportApi, retryInfo)

                    self.__lastRetryAfterPeriod = retryAfterSec
                    time.sleep(retryAfterSec)

                    # Nächsten Upload-Versuch starten
                    uploadTries = uploadTries - 1
                    return self.__PostUpload(monitor, uploadTries)

            response.close()

            raise err

    @staticmethod
    def ParseRetryAfter(headerRetryAfterValue):
        '''
        Parst den übergebenen Retry-After Header-Wert, der in Sekunden oder
        als Datum (RFC 1123-Format) übertragen werden kann.
        :param: headerRetryAfterValue: Header aus dem die Sekunden ermittelt werden sollen.
        :type: headerRetryAfterValue: str
        :return: Sekunden die bis zum nächsten Upload gewartet werden sollen.
                 Wird ein Wert größer 4 Stunden ermittelt, werden maximal 4 Stunden zurückgegeben.
                 -1 bedeutet der Header war nicht valide.
        :rtype: int
        '''
        maxRetryAfter = 14400  # 4 Stunden

        resultSec = -1

        if isinstance(headerRetryAfterValue, str):

            if headerRetryAfterValue.isdigit():
                resultSec = int(headerRetryAfterValue)
            else:
                try:
                    # Valides RFC 1123-Format: Thu, 01 Dec 1994 16:00:00 GMT
                    dateHeader = datetime.datetime.strptime(headerRetryAfterValue,
                                                            '%a, %d %b %Y %H:%M:%S GMT')
                    dateNow = datetime.datetime.now()
                    resultSec = int(dateHeader.timestamp() - dateNow.timestamp())
                except ValueError:
                    pass

        # Sollte der Wert größer als 4 Stunden sein, dann wird er auf 4 Stunden zurückgesetzt.
        if resultSec > maxRetryAfter:
            resultSec = maxRetryAfter

        return resultSec

    def GetCounterUploadTries(self):
        '''
        :returns: Anzahl der aktuellen Upload-Versuche.
        :rtype: int
        '''
        return self.__counterUploadTries

    def GetLastRetryAfterPeriod(self):
        '''
        :returns: Anzahl der letzten übermittelten Retry-After Zeitspanne in Sekunden
        :rtype: int
        '''
        return self.__lastRetryAfterPeriod

    def StartUpload(self):
        """
        Führt den zuvor präparierten Upload aus.
        :returns: True bei Erfolg, sonst False.
        :rtype: boolean
        """
        startUploadTime = datetime.datetime.now()

        port = Config.Cast2Int(Config.GetSetting(self.__reportApi, u'uploadThroughResourceAdapter'), 0);
        if port > 0:
            DPrint(LEVEL_NORMAL, _(u'Der ATX-Report wird zum ResourceAdapter übertragen. '
                    u'Port: {0}. Proxy Einstellungen werden nicht beachtet.'.format(port)))
            
            authKey = Config.GetSetting(self.__reportApi, u'uploadAuthenticationKey')
            testGuideUrl = CreateHttpUrl(self.__useHttps, self.__url, self.__port, self.__contextPath)
            return self.__TransferThroughResourceAdapter(port, testGuideUrl, authKey, 
                                                         self.__projectId, self.__uploadFilePath)

        serverLabel = _(u'(Server: {0}-{1})').format(
            self.__serverLabel, self.__projectId) if self.__serverLabel else u''

        encoder = MultipartEncoder(
            fields={
                self.__uploadFieldName: (
                    # TEST-GUIDE (Apache-Commom-Fileupload) unterstützt im Moment nicht
                    # https://tools.ietf.org/html/rfc2231
                    # deswegen wird der Filename immer kodiert übertragen.
                    quote(self.__uploadFileName.encode('utf-8')),
                    io.open(self.__uploadFilePath, u'rb'),
                    self.__GetContentType(self.__uploadFileName))
            }
        )

        callback = self._CreateMultipartEncoderMonitorCallback(encoder)
        monitor = MultipartEncoderMonitor(encoder, callback=callback)

        logPath = os.path.join(self.__reportApi.GetReportDir(), u"error.log")
        logRawPath = os.path.join(self.__reportApi.GetReportDir(), u"error.raw.log")
        logRawJsonPath = os.path.join(self.__reportApi.GetReportDir(), u"error.raw.json")
        try:
            try:
                response = self.__PostUpload(monitor, self.__maxUploadTries)

                if self.__uploadAsync:
                    return self.__AsyncUpload(response, startUploadTime, serverLabel)

                return self.__SyncUpload(response, startUploadTime, serverLabel)

            except HTTPError as err:
                response = err.response

                # Raw Response sichern
                with io.open(logRawPath, u'w+', encoding=u'utf-8') as logFile:
                    logFile.write(u'{0}'.format(response.content))

                if isinstance(response.reason, bytes):
                    reason = response.reason.decode(u'utf-8', u'replace')
                else:
                    reason = response.reason

                try:
                    logDict = response.json()
                except:
                    # Wenn Json Object nicht vorhanden, dann Error mit Status und Reason erzeugen!
                    raise self._CreateUploadError(response.status_code, reason)

                raise UploadError(reason, response.status_code, logDict)

        except UploadError as err:

            # JSON Response sichern
            with open(logRawJsonPath, 'w') as json_file:
                json.dump(err.logEntries, json_file)

            # Error-Log Messages auswerten und aufbereiten für die Anzeige
            logMessages = u'\n'.join([
                u'Error {0}: {1}'.format(
                    eachLogEntry.get(u'statusCode'),
                    eachLogEntry.get(u'body'))
                for eachLogEntry in err.logEntries.get(u'messages', [])
            ])

            with io.open(logPath, u'w+', encoding=u'utf-8') as logFile:
                logFile.write(u'Error {code} - {reason}:\n{msg}\n'.format(
                    code=err.statusCode, reason=err.reason, msg=logMessages))

            endUploadTime = datetime.datetime.now()
            EPrint(_(u'Die ATX-Übertragung [{files}] war erfolgreich {serverLabel} '
                     u'(Generator v{version}), '
                     u'die Verarbeitung der Dateien führte jedoch zu Fehlern ({errCode}):\r\n'
                     u'{msg}'
                     u'Error-Log: {logPath}\r\n'
                     u'Uploaddauer: {duration}').format(logPath=logPath,
                                                        msg=logMessages,
                                                        errCode=err.statusCode,
                                                        files=self.__uploadFilePath,
                                                        version=self.__version,
                                                        duration=str(endUploadTime -
                                                                     startUploadTime).split(u'.',
                                                                                            1)[0],
                                                        serverLabel=serverLabel))
            return False

        except RequestException as err:
            EPrint(_(u'Die ATX-Übertragung [{files}] {serverLabel} konnte nicht statt '
                     u'finden:\r\n{reason}').format(reason=str(err),
                                                    files=self.__uploadFilePath,
                                                    serverLabel=serverLabel))
            return False

    def __TransferThroughResourceAdapter(self, port, url, authKey, projectId, filePath):
        '''
        Überträgt die Datei gemeinsam mit den Informationen für den Upload zu TEST-GUIDE 
        an den ResourceAdapter.
        :param: port: Port auf dem der ResourceAdapter Uploads entgegen nimmt
        :type: port: int
        :param: url: Url der TEST-GUIDE Instanz
        :type: url: str
        :param: authKey: Auth Key
        :type: authKey: str
        :param: projectId: Projekt Id
        :type: projectId: int
        :param: filePath: Pfad zur Datei
        :type: filePath: str
        :returns: war die Übertragung erfolgreich
        :rtype: boolean
        '''
        query = urlencode({ 'url': url, 'authKey': authKey, 'projectId': projectId })
        
        try:
            requestUrl = u'http://localhost:{port}/ResourceAdapter/Upload?{query}'.format(
                port=port, query=query)
            with open(filePath, 'rb') as file:
                req = requests.post(requestUrl, data = file, verify = False)
                if req.status_code == 202:
                    DPrint(LEVEL_NORMAL, _(u'Das ATX-Dokument wurde zum ResourceAdapter übertragen.'))
                    return True
                else:
                    WPrint(_(u'Das ATX-Dokument konnte nicht zum ResourceAdapter übertragen werden: '
                        u'{code} {reason}\r\nWeitere Details in den Logs des ResourceAdapters.'.format(
                        code=req.status_code, reason=req.text)))
        except RequestException as err:
            EPrint(_(u'Die ATX-Übertragung war nicht möglich:\r\n{reason}\r\nWeitere Details '
                u'in den Logs des ResourceAdapters.').format(reason=str(err)))
        return False

    def _CreateMultipartEncoderMonitorCallback(self, encoder):
        """
        Gibt eine Callbackfunktion für den übergebenen MultipartEncoder zurück. Diese setzt
        den aktuellen Uploadstatus im Task Manager.
        :param encoder: MultipartEncoder, für welchen die Callbackfunktion erstellt werden soll.
        :type encoder: MultipartEncoder
        :returns: Callbackfunktion für MultipartEncoderMonitor
        :rtype: method
        """
        visual = ShowInfoOnTaskManager(self.__reportApi,
                                       _(u'{0} Bytes werden hochgeladen...').format(encoder.len))

        if not visual:
            def MonitorCallback(monitor):
                pass
            return MonitorCallback

        def MonitorCallback(monitor):
            currentTime = time.monotonic()
            # Update für Caption nur alle x Sekunden aufrufen, damit Task Manager nicht einfriert
            # (TTS-13089)
            if currentTime - MonitorCallback.timeLastCaptionUpdate \
                    < self.TIME_BETWEEN_CAPTION_UPDATES:
                return

            MonitorCallback.timeLastCaptionUpdate = currentTime
            if monitor.bytes_read == encoder.len:
                visual.SetCaption(_(u'Hochgeladene Daten werden verarbeitet...'))
                return
            visual.SetCaption(_(u'{0}/{1} Bytes hochgeladen...').format(monitor.bytes_read,
                                                                        encoder.len))

        # Initialisierung für Zeitpunkt des letzten Captionupdates; Ist Attribut der Methode,
        # damit Zuordnung der Statusvariablen zur Methode klar ist und in der Callbackmethode keine
        # lokale Variable angelegt wird. Aufgrund der Kompatibilität mit Python2 kann 'nonlocal'
        # nicht verwendet werden.
        MonitorCallback.timeLastCaptionUpdate = time.monotonic()

        return MonitorCallback

    def _CreateUploadError(self, statusCode, errorText):
        """
        Erzeugt einen HTTPError mit dem angegebenen Status-Code und Fehlertext.
        :param statusCode: HTTP-Fehlercode
        :type statusCode: int
        :param errorText: Fehlermeldung
        :type errorText: str
        :returns: Uploadfehler
        :rtype: UploadError
        """
        errorDict = {u'messages': [{u'statusCode': statusCode, u'body': errorText}]}
        return UploadError(statusCode, errorText, errorDict)

    def __CreateHttpPayLoad(self, jsonPayLoad):
        """
        Erstellt aus der folgenden TEST-GUIDE Payload die entsprechende JSON-Meldung die
        bei HTTP-Antworten (auch Fehlern) verarbeitet wird.

        Beispiel-Payload:
        {
           'type' : 'reportUpload',
           'id' : 27,
           'projectId' : 1,
           'status' : 'FINISHED',
           'result' : 'FAILED',
           'initDate' : '2018-06-22T10:58:29.906+02:00',
           'endDate' : '2018-06-22T10:58:30.124+02:00',
           'lastCommand' : 'SAVE_REVIEWS',
           'fileName' : 'file-upload155204141016811453.tmp',
           'statusCode' : 400,
           'messages' : [ {
              'statusCode' : 400,
              'body' : 'XML Dokument ist bereits in der Datenbank gespeichert.'
           } ],
           'async' : true,
           'lastCommandDescription' : 'Processing reviews'
        }
        :param jsonPayLoad: TEST-GUIDE HTTP JSON payload, der ausgewertet werden soll.
        :type jsonPayLoad: Dict
        :returns: JSON Liste mit den Nachrichten die zurückgegeben werden sollen.
        :rtype: JSON string
        """
        entries = []
        for each in jsonPayLoad.get(u'messages', []):
            entries.append({u'FILE': u'',
                            u'STATUS': each.get(u'statusCode'),
                            u'TEXT': each.get(u'body')})

        return JSONEncoder().encode({u'ENTRIES': entries})

    def __SuccessUpload(self, payload, statusCode, startUploadTime, serverLabel):
        """
        Wenn der Upload erfolgreich war (Status-Code <300) kann die Methode aufgerufen werden
        um einen erfolgreichen Upload dem Benutzer mitzuteilen.
        :param payload: HTTP-Nachrichten, welche in der success.json geloggt werden sollen für eine
                        weitere Auswertung via z.B. Jenkins.
        :type payload: JSON bytes
        :param statusCode: HTTP-Status-Code der Upload-Message
        :type statusCode: integer
        :param startUploadTime: Startzeitpunkt des Uploads für die Messung und die Anzeige in der
                                Log-Anzeige.
        :type startUploadTime: datetime.datetime
        :param serverLabel: Server, der ausgewählt wurde für die Log-Anzeige.
        :type serverLabel: str
        """
        endUploadTime = datetime.datetime.now()
        SPrint(_(u'Die ATX-Übertragung [{0}] war erfolgreich (Generator v{1}) {3} '
                 u'Uploaddauer: {2} .').format(self.__uploadFilePath,
                                               self.__version,
                                               str(endUploadTime - startUploadTime).split(u'.')[0],
                                               serverLabel))

        if statusCode == 206:
            WPrint(_(u'Achtung: Die TEST-GUIDE Dateiablage '
                     u'(siehe Einstellungen/Dateiablage) ist deaktiviert! '
                     u'Alle zusätzlich übermittelten Artefakte wurden verworfen.'))

        # JSON Response sichern
        sucPath = os.path.join(self.__reportApi.GetReportDir(), u"success.json")
        with io.open(sucPath, u'wb') as successFile:
            successFile.write(payload)

    def __SyncUpload(self, response, startUploadTime, serverLabel):
        """
        Führt den synchronen Upload durch. Es erfolgt ein Upload der Daten an TEST-GUIDE und es wird
        gewartet, bis TEST-GUIDE den Upload quittiert, d.h. in der Datenbank gespeichert hat.
        :param response: HTTP-Antwort, für den verwendeten Upload.
        :type response: requests.Response
        :param startUploadTime: Startzeitpunkt des Uploads für die Messung und die Anzeige in der
                                Log-Anzeige.
        :type startUploadTime: datetime.datetime
        :param serverLabel: Server, der ausgewählt wurde für die Log-Anzeige.
        :type serverLabel: str
        :returns: True, bei erfolgreichem Upload, sonst False.
        :rtype: boolean
        """
        # Im Fehlerfall >= StatusCode 400 wird eine HTTPError-Exception geworfen
        if response.status_code >= 300:
            raise self._CreateUploadError(response.status_code, u'Unknown redirect')

        self.__SuccessUpload(response.content, response.status_code,
                             startUploadTime, serverLabel)
        return True

    def __AsyncUpload(self, response, startUploadTime, serverLabel):
        """
        Führt den asynchronen Upload durch. Es erfolgt ein Upload der Daten an TEST-GUIDE, welches
        dann die Status-URl des Uploads bereitstellt und hier direkt gepollt wird.
        :param response: HTTP-Antwort, für den verwendeten Upload.
        :type response: requests.Response
        :param startUploadTime: Startzeitpunkt des Uploads für die Messung und die Anzeige in der
                                Log-Anzeige.
        :type startUploadTime: datetime.datetime
        :param serverLabel: Server, der ausgewählt wurde für die Log-Anzeige.
        :type serverLabel: str
        :returns: True, bei erfolgreichem Upload, sonst False.
        :rtype: boolean
        """
        statusResLink = None

        visual = ShowInfoOnTaskManager(self.__reportApi,
                                       _(u'Upload wird asynchron verarbeitet...'))

        # Erwartete Rückgabe von TEST-GUIDE
        # {'ENTRIES':[{'FILE': 'file-upload6523204238481192334.tmp',
        #              'STATUS': 202,
        #              'TEXT': '/api/upload-file/status/6'}]}
        if response.status_code == 202:
            try:
                respDict = response.json()
            except Exception as err:
                # Fehler im Payload tolerieren.
                EPrint(u'Read async upload payload failed: {0}'.format(str(err)))
                respDict = {}

            responses = respDict.get(u'ENTRIES', [])
            if responses:
                statusResLink = responses.pop().get(u'TEXT')
        else:
            raise self._CreateUploadError(response.status_code, u'Upload status request failed')

        if statusResLink:
            statusUrl = self.GetStatusUrl(statusResLink)

            # Polling für die Status-Abfrage durchführen.
            constMinSleepTimeSec = 3
            constMaxWaitTimeHours = 7
            constMaxWaitTimeInSec = constMaxWaitTimeHours * 60 * 60

            waitTimeSec = 0
            while waitTimeSec < constMaxWaitTimeInSec:
                requestStat = requests.get(
                    url=statusUrl,
                    headers={
                        u'Accept': u'application/{accept}'.format(accept=self.__accept)
                    },
                    verify=False,
                    proxies=self.__proxies
                )
                requestStat.raise_for_status()

                try:
                    respDict = requestStat.json()
                except ValueError as err:
                    # Fehler im Payload tolerieren.
                    EPrint(u'Read async upload status failed: {0}'.format(str(err)))
                    respDict = {}

                status = respDict.get(u'status')
                if status == u'FINISHED':
                    statusCode = respDict.get(u'statusCode')

                    if statusCode >= 300:
                        raise UploadError(statusCode, u'Upload failed', respDict)

                    self.__SuccessUpload(requestStat.content,
                                         statusCode,
                                         startUploadTime, serverLabel)
                    return True

                statusMsg = respDict.get(u'lastCommandDescription')
                if statusMsg and visual:
                    visual.SetCaption(_(u'Uploadstatus: {0}').format(statusMsg))

                # Minimum-Wartezeit bis zur nächsten Abfrage
                time.sleep(constMinSleepTimeSec)
                waitTimeSec += constMinSleepTimeSec
        else:
            # Wenn der Statuslink nicht ermittelt werden kann!
            raise self._CreateUploadError(500, u'Unknown status link')

        return False
