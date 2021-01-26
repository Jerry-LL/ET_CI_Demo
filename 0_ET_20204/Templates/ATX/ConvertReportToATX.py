# -*- coding: utf-8 -*-

'''
Created on 21.02.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''

import json

from .GenerateAtxDataSet import GenerateAtxDataSet
from .Utils import GetFirstValue, GetIsoDate
from .dict2xml import dict2xml


class ConvertReportToATX(object):
    '''
    Erzeugt aus dem übergebenen Report-Objekt das entsprechende ATX-Objekt.
    '''
    def __init__(self, reportApi, version, isPackageExecution):
        '''
        Konstruktor.
        @param reportApi: Aktuelles Objekt der ReportAPI.
        @type reportApi: ReportApi
        @param version: Version des Generators und gleichzeitig die unterstützte API-Version.
        @type version: str
        @param isPackageExecution: Handelt es sich um ein PackageReport.
        @type isPackageExecution: bool
        '''
        self.__reportTrfFile = reportApi.GetDbFile()
        self.__json = True
        self.__version = version
        self.__data = self.__CreateAtxData(reportApi, isPackageExecution)

    def CreateATXXmlFile(self, xmlFilePath):
        '''
        Schreibt auf Grundlages des übergebenen Pfades eine ATX-XML Datei raus.
        @param xmlFilePath: Pfad wo die ATX-Datei erstellt werden soll.
        @type xmlFilePath: str
        '''
        d2x = dict2xml(self.__reportTrfFile, self.__version, self.__data[u'report'])
        d2x.CreateXmlFile(xmlFilePath)

    def GetSerialized(self, serializeFormat=u'xml'):
        '''
        Gibt das serialisierte Dokument im gewünschten Format zurück.
        Achtung: Sollen beide Repräsentationsoformes des Dokuments erzeugt werden,
                muss zu erst das JSON Dokument erzeugt werden, da die XML Erzeugung
                Teile des Dictionarys durch .pop() entfernt.
        @param serializeFormat: XML oder JSON.
        @type serializeFormat: str
        @return: das serialierte Dokument.
        @rtype: str
        '''
        if serializeFormat == u'json':
            if self.__json:
                return self.__GetJSON()

            print (u'Es wurde bereits das XML Dokument erzeugt. Die Erzeugung eines weiteren '
                   u'Dokuments ist daher nicht mehr möglich.')
            return False

        self.__json = False
        return self.__GetXML()

    def __GetXML(self):
        '''
        Erzeugt das XML Dokument als String.
        @return: XML Repräsentation des Dokuments.
        @rtype: str
        '''
        return dict2xml(self.__reportTrfFile, self.__version, self.__data[u'report']).GetXmlString()

    def __GetJSON(self):
        '''
        Erzeugt das JSON Dokument als String.
        @return: JSON Repräsentation des Dokuments.
        @rtype: str
        '''
        return json.dumps(self.__data[u'report'])

    def __CreateAtxData(self, reportApi, isPackageExecution):
        '''
        Baut das ATX Objekt als Dictionary auf.
        @param reportApi: Aktuelles Objekt der ReportAPI.
        @type reportApi: ReportApi
        @param isPackageExecution: Handelt es sich um ein PackageReport.
        @type isPackageExecution: bool
        @return: gibt die erzeugten Daten der ATX Konvertierung zurück.
        @rtype: dict(report->ATX Objekt, files->Pfade von Packages, TBC, TCF, usw.)
        '''
        return GenerateAtxDataSet(reportApi, GetFirstValue(reportApi, u'GetName'),
                                  GetIsoDate(GetFirstValue(reportApi, u'GetTime')),
                                  isPackageExecution).GetData()

    def GetFiles(self):
        '''
        Gibt die Liste der Dateien zurück, die als ZIP hochgeladen werden sollen.
        @return: Liste der Dateien.
        @rtype: list[->str]
        '''
        return self.__data[u'files']

    def GetReviews(self):
        '''
        Gibt die Liste der Review-Elemente zurück, die im ZIP mit hochgeladen werden sollen.
        @return: Liste der Reviews.
        @rtype: list[->Review]
        '''
        return self.__data[u'reviews']
