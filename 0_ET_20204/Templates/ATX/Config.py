# -*- coding: utf-8 -*-

'''
Created on 27.10.2014

@author: Philipp
'''

import os
from lxml import etree

from log import EPrint, SPrint, WPrint, LEVEL_VERBOSE, DPrint


class SettingsFromServerMode(object):
    '''
    Mögliche Modi um Einstellungen vom Server zu übernhemen.
    '''
    NEVER = u'never'
    WHEREKEYWORD = u'wherekeyword'
    ALWAYS = u'always'
    
    def __init__(self):
        pass
    
    @classmethod
    def of(cls, useSettingsFromServer):
        for each in [SettingsFromServerMode.NEVER, SettingsFromServerMode.WHEREKEYWORD, SettingsFromServerMode.ALWAYS]:
            if each == useSettingsFromServer:
                return each
        return SettingsFromServerMode.NEVER

class Config(object):
    '''
    Klasse kapselt die ReportApi-Konfigurationsaufrufe.
    Dies ist notwendig, da bei einem AutoUpdate nicht
    die neuen ReportApi Konfigurationen im Moment des AutoUpdates zur Verfügung stehen und beim
    Aufruf von GetSetting kann über diesen Wrapper der Default-Wert ermittelt werden.
    '''

    # Settings, die vom TEST-GUIDE Server geladen wurden
    __externalSettings = {}
    __useExternalSettings = SettingsFromServerMode.NEVER
    __keyword = None

    def __init__(self):
        '''
        Konstruktor.
        '''
        pass

    @staticmethod
    def Cast2Int(value, default=0):
        '''
        Nimmt einen Cast von einem String zu einem Integer vor.
        Wenn ein Cast nicht möglich ist, wird der Default-Wert zurückgegeben.
        @param value: Wert der zu einem Integer gecastet werden soll.
        @type value: str
        @param default: der Default-Wert welcher zurückgegeben werden soll, wenn ein Cast nicht
                        möglich ist.
        @type default: int
        @return: ermittelter Wert
        @rtype: int
        '''
        try:
            return int(value)
        except ValueError:
            return default
        except TypeError:
            return default

    @staticmethod
    def GetSetting(reportApi, name):
        '''
        Ermittelt zunächst in der ReportApi den jeweiligen Setting-Wert, ist die Setting unbekannt,
        dann wird versucht der Default-Wert aus der aktuellen config.xml zu lesen.
        @param reportApi: ReportApi, aus welcher der Wert für die Setting zurückgegeben werden soll
        @type reportApi: tts.core.report.parser.ReportApi
        @param name: Name der Setting
        @type name: str
        @return: gefundener Default-Wert oder None
        @rtype: str, boolean, integer oder None
        '''
        reportApiValue = reportApi.GetSetting(name)
        settingsMode = Config.__useExternalSettings
        if Config.__CanBeOverwrittenByServer(name) and settingsMode is not SettingsFromServerMode.NEVER:
            DPrint(LEVEL_VERBOSE, u'Setting key: {0}, settings mode: {1}'.format(name, settingsMode))
            if settingsMode is SettingsFromServerMode.ALWAYS or \
               (settingsMode is SettingsFromServerMode.WHEREKEYWORD and reportApiValue == Config.__keyword):
                reportApiValue = Config.__externalSettings.get(name)

        # Wenn unbekannt, dann versuchen aus der aktuellen config.xml zu ermitteln.
        if reportApiValue is None:
            return Config.__GetDefaultValue(name)

        return reportApiValue

    @staticmethod
    def LoadExternalSettings(settings, settingsMode, keyword = None):
        '''
        Lädt die externen Settings.
        @param settings: Dict mit den Einstellungen
        @type settings: dict
        @param settingsMode: Konfiguration der Einstellungen
        @type settingsMode: SettingsFromServerMode
        @param keyword: magisches Schlüsselwort für das die Werte vom TG Server verwendet 
                        werden sollen 
        @type keyword: str
        '''
        Config.__externalSettings = {setting["key"]: setting["value"] for setting in settings}
        Config.__useExternalSettings = settingsMode
        Config.__keyword = keyword
        
        SPrint(u'Successfully loaded external settings: {0}'.format(Config.__externalSettings))
        SPrint(u'useExternalSettings={0}, keyword={1}'.format(Config.__useExternalSettings,  Config.__keyword))

    @staticmethod
    def ClearExternalSettings():
        '''
        Setzt die Settings zurück.
        '''
        Config.__externalSettings = {}
        Config.__useExternalSettings = SettingsFromServerMode.NEVER
        Config.__keyword = None

    @staticmethod
    def __GetDefaultValue(name):
        '''
        Ermittelt zu der übergebenen Settings (name) den Default-Wert.
        @param name: Name der Settings in der config.xml, aus welcher der Default-Wert ermittelt
                     werden soll.
        @type name: str
        @return: gefundener Default-Wert oder None
        @rtype: str, boolean, integer oder None
        '''
        # beiliegende config.xml einlesen für XPath
        atxDir = os.path.dirname(os.path.realpath(__file__))
        doc = etree.parse(os.path.join(atxDir, u'config.xml'))

        # Default-Wert der Setting via XPath ermitteln
        values = doc.xpath(u"//SETTING[@name='{0}']/attribute::default".format(name))

        # Wenn Setting unbekannt, dann None zurückgeben als Default-Wert
        if len(values) == 0:
            return None

        # Ersten gefundenen Wert zurückgeben
        return values[0]

    @staticmethod
    def __CanBeOverwrittenByServer(name):
        '''
        Ermittelt zu der übergebenen Settings (name) den Default-Wert.
        @param name: Name der Settings in der config.xml, aus welcher der Default-Wert ermittelt
                     werden soll.
        @type name: str
        @return: gefundener Default-Wert oder None
        @rtype: str, boolean, integer oder None
        '''
        # beiliegende config.xml einlesen für XPath
        atxDir = os.path.dirname(os.path.realpath(__file__))
        doc = etree.parse(os.path.join(atxDir, u'config.xml'))

        # Attribut ermitteln
        values = doc.xpath(u"//SETTING[@name='{0}']/attribute::canBeOverwrittenByServer".format(name))

        # Falls Attribut nicht gesetzt -> default: True
        if len(values) == 0:
            return True

        # Attributwert zurückgeben
        return values[0] == "true"
