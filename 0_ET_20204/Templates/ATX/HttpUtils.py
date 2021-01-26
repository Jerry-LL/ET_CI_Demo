# -*- coding: utf-8 -*-

'''
Created on 29.02.2016

@author: Philipp
'''
from .Config import Config


def CreateHttpUrl(useHttps, host, port, path):
    '''
    Erstellt URL
    :param useHttps: True, wenn Https-Verbindung verwendet werden soll, sonst False
    :type useHttps: bool
    :param host: Host für die Http-Verbindung
    :type host: str
    :param port: Port für die Verbindung
    :type port: int
    :param path: Pfad oder Pfadkomponenten
    :type path: str | iterable[str]
    :return: url
    :rtype: str
    '''
    return u"{protocol}://{host}:{port}/{path}".format(
        protocol=u"https" if useHttps else u"http",
        host=host,
        port=port,
        path=path
    )


def CreateRequestProxySettings(reportApi):
    '''
    Ermittelt aus den Settings die gesetzten Proxy-Einstellungen und gibt diese für einen
    Request-Aufruf zurück. Beispiel: http://user:pass@10.10.10.2:8080 für
    requests.get('http://tracetronic.de', proxies=proxies) ->
    requests.get('http://tracetronic.de', proxies=CreateRequestSettings(reportApi))
    @param reportApi: Aktuelles Objekt der ReportAPI.
    @type reportApi: ReportApi
    @return: Dict mit dem Mapping der Protokolle bei Verwendung eines Proxies oder ein leeres Dict
    @rtype: dict
    '''
    proxies = {}

    httpProxy = Config.GetSetting(reportApi, u'httpProxy')
    httpsProxy = Config.GetSetting(reportApi, u'httpsProxy')

    if httpProxy:
        proxies[u'http'] = httpProxy

    if httpsProxy:
        proxies[u'https'] = httpsProxy

    return proxies
