# -*- coding: utf-8 -*-

'''
Created on 21.02.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''


import os
import re
import zipfile
import uuid
from lxml import etree

from constantsVersionInfo import PRODUCT_NAME_VERSION
from .Config import Config
from .Utils import GetExtendedWindowsPath


class ZipArchive(object):
    '''
    Erstellt eine Zip-Datei.
    '''

    FIND_ASCII_CTRL_REG_EXP = re.compile(r'[\x00-\x1F]+')

    def __init__(self, reportApi, fileName, atxFilePath, files, reviews):
        '''
        Konstruktor.
        @param reportApi: Aktuelles Objekt der ReportAPI.
        @type reportApi: ReportApi
        @param fileName: Name der Ziel ZIP Datei
        @type fileName: str
        @param atxFilePath: Pfad zur ATX XML.
        @type atxFilePath: str
        @param files: Liste von Dateien, die in ein gemeinsames Zip Archiv gepackt werden sollen.
        @type files: list[->str]
        @param reviews: Liste von Reviews.
        @type reviews: list[->Review]
        '''
        self.__reportApi = reportApi
        self.__mappingFile = GetExtendedWindowsPath(os.path.join(reportApi.GetReportDir(),
                                                                 u'mapping.xml'))
        self.__reviewsFile = GetExtendedWindowsPath(os.path.join(reportApi.GetReportDir(),
                                                                 u'reviews.xml'))

        self.__atxFilePath = atxFilePath
        self.__archiveEnabled = Config.GetSetting(reportApi, u'enableArchive') == u'True'
        self.__compressUpload = Config.GetSetting(reportApi, u'compressUpload') == u'True'
        self.__zipFilePath = GetExtendedWindowsPath(os.path.join(reportApi.GetReportDir(),
                                                                 fileName))
        self.__zipPartFilePath = u'{0}.part'.format(self.__zipFilePath)

        self.__files = self.__CreateMappedFiles(files)

        self.__CreateReviewsFile(reviews)

    def Make(self):
        '''
        Führt die Erstellung des Archivs aus.
        @return: True bei erfolgreicher Erstellung, sonst False.
        @rtype: boolean
        '''
        try:
            compressType = zipfile.ZIP_DEFLATED if self.__compressUpload else zipfile.ZIP_STORED
            with zipfile.ZipFile(self.__zipPartFilePath, u'w',
                                 compressType, True) as zipHandler:
                # ATX XML in die ZIP schreiben
                zipHandler.write(self.__atxFilePath, os.path.basename(self.__atxFilePath))

                # Mapping XML schreiben, selbst wenn diese leer ist
                zipHandler.write(self.__mappingFile, os.path.basename(self.__mappingFile))

                # Reviews XML schreiben, selbst wenn diese leer ist
                zipHandler.write(self.__reviewsFile, os.path.basename(self.__reviewsFile))

                if self.__archiveEnabled:
                    # sonstige Dateien in die ZIP schreiben
                    for key, val in self.__files.items():
                        if os.path.isfile(GetExtendedWindowsPath(key)):
                            zipHandler.write(key, u'{0}/{1}'.format(val, os.path.basename(key)))

            # Wenn Ziel bereits vorhanden ist, dann löschen für das rename
            # kann durch One-Click-Upload bei der Nachbewertung geschehen.
            if os.path.exists(self.__zipFilePath):
                os.remove(self.__zipFilePath)

            os.rename(self.__zipPartFilePath, self.__zipFilePath)

            return True
        except BaseException as ex:
            print(ex)

        return False

    def GetZipFilePath(self):
        '''
        @return: Pfad zur Zip-Datei.
        @rtype: str
        '''
        return self.__zipFilePath

    def __CreateMappedFiles(self, files):
        '''
        Erzeugt aus den zu archiverenden Dateien eine Mapping Datei, welche anhand des Dateipfades
        Redundanz erzeugt indem jedem Pfad eine UUID zugewiesen wird, die als Ordner der Datei im
        ZIP dient.
        Ist die Archivierung deaktiviert wird trotzdem eine mapping.xml ohne Einträge erstellt.
        @param files: Dateien, die archiviert werden sollen
        @type files: list[->dict]
        @return: Mapping von Dateipfad auf UUID
        @rtype: dict
        '''
        mapPathToUuid = {}
        root = etree.Element(u'FILES')
        if self.__archiveEnabled:
            for each in files:
                if each[u'file'] not in mapPathToUuid:
                    mapPathToUuid.update({each[u'file']: u'{0}'.format(uuid.uuid1())})
                efile = etree.SubElement(root, u'FILE')
                etree.SubElement(efile, u'ATX-REF-PATH').text = each['ref']
                etree.SubElement(efile, u'FILENAME').text = os.path.basename(each['file'])
                etree.SubElement(efile, u'TEMP-DIR').text = mapPathToUuid[each['file']]
                # etree.SubElement(efile, 'CATEGORY').text = ''
                etree.SubElement(efile, u'UPLOADER').text = PRODUCT_NAME_VERSION

                comment = each.get(u'comment', u'')
                # comment kann auch direkt None sein!
                if not comment:
                    comment = u''
                comment = self.FIND_ASCII_CTRL_REG_EXP.sub(u'', comment)
                etree.SubElement(efile, u'COMMENT').text = comment

                etree.SubElement(efile, u'REF-PATH-TYPE').text = each.get(u'refPathType')

        with open(self.__mappingFile, u'wb') as fileHandler:
            fileHandler.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            fileHandler.write(etree.tostring(root, pretty_print=True, encoding=u'UTF-8'))

        return mapPathToUuid

    def __CreateReviewsFile(self, reviews):
        '''
        Erstellt und schreibt die XML Darstellung der Reviews in die reviews.xml.
        @param reviews: Liste mit Reviews
        @type reviews: list[->Review]
        '''
        root = etree.Element(u'REVIEWS')

        for review in reviews:
            root.append(review.GetXml())

        with open(self.__reviewsFile, u'wb') as fileHandler:
            fileHandler.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            fileHandler.write(etree.tostring(root, pretty_print=True, encoding=u'UTF-8'))
