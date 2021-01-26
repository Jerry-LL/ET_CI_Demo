# -*- coding: utf-8 -*-

'''
Created on 20.07.2020

@author Alexander Lehmann
'''

import requests

from log import EPrint, SPrint, WPrint, DPrint, LEVEL_NORMAL


class ConfigDisabledError(Exception):
    '''
    Error der geworfen wird, wenn die zentrale Config deaktiviert ist.
    '''
    pass


class ConfigDownloader:
    '''
    Lädt die Konfiguration für die ATX-Generierung von einem TEST-GUIDE Server herunter.
    '''

    def __init__(self, authKey, projectId=1, url=u'127.0.0.1', port=8085, useHttps=False,
                 contextPath=u'', proxies=None):
        '''
        Konstruktor.
        :param authKey: Auth-Key für den Download der Zentral-Config.
        :type authKey: str
        :param projectId: Project-Id
        :type projectId: int
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
        :param proxies: Dict mit dem Mapping der Protokolle bei Verwendung eines Proxies oder
                        ein leeres Dict
        :type proxies: dict
        '''
        self.__authKey = authKey
        self.__projectId = projectId
        self.__url = url
        self.__port = port
        self.__useHttps = useHttps
        self.__contextPath = contextPath
        self.__proxies = proxies

    def DownloadConfig(self):
        '''
        :return: Ermittelt die aktuellen Settings von TEST-GUIDE.
        :rtype: dict
        '''
        targetUrl = self.__GetTargetUrl()
        response = requests.get(url=targetUrl, verify=False, proxies=self.__proxies)
        if response.status_code == 204:
            raise ConfigDisabledError("Error: useSettingsFromServer is set to 'True' but "
                                      "settings are disabled in TEST-GUIDE")
        if response.status_code != 200:
            EPrint("Could not retrieve config from server")
            response.raise_for_status()
            raise IOError("Unexpected status code " + str(response.status_code) + " - " + response.reason)

        jsonDict = response.json()
        return jsonDict['settings']

    def __GetTargetUrl(self):
        """
        :returns: Gibt in Abhängigkeit ob HTTPS verwendet werden soll oder nicht die entsprechende
                  URL zu den ATX-Generator-Settings zurück.
        :rtype: str
        """
        # Default URL Protocol wenn nix angegeben.
        urlProtocolPrefix = u'http://'

        # Wenn https gewünscht.
        if self.__useHttps:
            urlProtocolPrefix = u'https://'

        contextPath = self.__contextPath
        if self.__contextPath:
            contextPath += u'/'

        return (u'{pro}{url}:{port}/{context}api/report/atx/settings'
                u'?authKey={authKey}'
                u'&projectId={projectId}').format(pro=urlProtocolPrefix,
                                                  url=self.__url,
                                                  port=self.__port,
                                                  context=contextPath,
                                                  authKey=self.__authKey,
                                                  projectId=self.__projectId)
