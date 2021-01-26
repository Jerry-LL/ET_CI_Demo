# -*- coding: utf-8 -*-

'''
Created on 23.09.2014

@author: Philipp
'''

import requests

from log import DPrint, LEVEL_VERBOSE
from .HttpUtils import CreateHttpUrl


def GetVersion():
    '''
    @return: Gibt die Version des Generators zurück, dies muss immer mit der Version des zu
             verwendeten Services übereinstimmen.
    @rtype: str
    '''
    return u"1.90.0"


def GetServerVersion(useHttps, host, port, contextUrl, proxySettings):
    '''
    Ermittelt anhand der übergeben URL die dort verwendete Version der App.
    @param useHttps: True, wenn eine Https-Verbindung verwendet werden soll, sonst False.
    @type useHttps: boolean
    @param host: Host
    @type host: str
    @param port: Port
    @type port: integer
    @param contextUrl: Context-URL (kann u.U. auch leer sein)
    @type contextUrl: str
    @param proxySettings: Dict mit dem Mapping der Protokolle bei Verwendung eines Proxies oder
                          ein leeres Dict
    @type proxySettings: dict
    @return: App-Version oder 0.0.0 bei Fehler, wie keine Verbindung möglich.
    @rtype: str
    '''
    path = u"api/app-version-info"
    if contextUrl:
        path = u"/".join((contextUrl, path))
    url = CreateHttpUrl(useHttps, host, port, path)

    try:
        response = requests.get(url=url, timeout=5, verify=False, proxies=proxySettings)
        response.raise_for_status()
        return response.json().get(u"info").get(u"version").split(u"#")[0]
    except BaseException as err:
        # Verbindung zum Server nicht möglich
        # Ungültige Version zur weiter Verarbeitung wird zurückgegeben.
        DPrint(LEVEL_VERBOSE, u"ATX-Mako GetServerVersion()", err)
        return u"0.0.0"


def GetDownloadLinkForATXMako(useHttps, hostUrl, port, contextUrl, authKey):
    '''
    Gibt den Download-Link für die ATX-Mako vom Server zurück.
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
    @return: Link zum Download der ATX-Mako vom Server.
    @rtype: str
    '''

    def GetClientVer():
        '''
        @return: z.B. ProducktnameSuffix__v7.2.0
        @rtype: unicode
        '''
        try:
            from constantsVersionInfo import GetFullName, GetVersionString
            return u"{0}__v{1}".format(GetFullName().replace(" ", "_"), GetVersionString())
        except ImportError:
            pass
        return u""

    path = u"api/download-file/ATXGenerator?clientVersion={0}&authKey={1}".format(GetClientVer(),
                                                                                  authKey)
    if contextUrl:
        path = u"/".join((contextUrl, path))

    DPrint(LEVEL_VERBOSE, u"GetDownloadLinkForATXMako()", path)
    return CreateHttpUrl(useHttps, hostUrl, port, path)
