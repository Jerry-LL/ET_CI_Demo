# -*- coding: utf-8 -*-

'''
Created on 27.02.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''


import os
from datetime import tzinfo, datetime, timedelta
from copy import deepcopy
import hashlib
import re
import shutil
import sys
import zipfile
import time

from .Config import Config
from .Review import Review

from log import WPrint, EPrint, DPrint, LEVEL_VERBOSE

from application.testReportService.ShortnameConverter import PackageNameToATXTestCaseShortName

if sys.version_info < (3,):
    str = unicode

FIND_ASCII_CTRL_REG_EXP = re.compile(r'''[\x00-\x1f\x7f-\x9f]+''')


def ReplaceAsciiCtrlChars(value):
    '''
    Methode zum Entfernen von Steuerzeichen aus einem String, damit die Daten in XML korrekt
    überführt werden können.
    @param value: Object aus dessen String-Repr die Steuerzeichen entfernt werden sollen.
    @type value: obj
    @return: String-Repr ohne Steuerzeichen.
    @rtype: str
    '''
    if value:
        return FIND_ASCII_CTRL_REG_EXP.sub(u'', u"{0}".format(value))

    return value


def GetIsoDate(date):
    '''
    Erzeugt aus dem übergebenen Datum ein ATX-konformes ISO-8601 Datum ohne Angabe der
    Mikrosekunden.
    @param date: Lokales Datum UTC ohne Zeitzone, mit Mikrosekunden.
    @type date: datetime
    @return: UTC-Datum, ohne Mikrosekunden.
    @rtype: str
    '''

    class UTC(tzinfo):
        """UTC"""

        def utcoffset(self, dt):
            return timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return timedelta(0)

    # Aktuelles Offset von UTC-Timestamp (datetime.datetime.fromtimestamp) rückauflösen
    # Im übergebenen date ist der UTC-Timestamp mit der gerade lokalen UTC-Offset verbandelt
    # siehe /TTS/src/lib/report/parser/Package.py -> GetTime()
    # welches nun wieder abgezogen werden muss um auf den UTC-Timestamp zu kommen.
    if sys.version_info < (3,):
        localOffset = (datetime.now() - datetime.utcnow()).total_seconds()
    else:
        # datetime.timestamp gibt es erst mit Python 3.3
        localTimeStamp = time.mktime(date.timetuple())
        utcTime = datetime.utcfromtimestamp(localTimeStamp)
        localOffset = localTimeStamp - utcTime.timestamp()

    date = (date - timedelta(seconds=localOffset))
    return date.replace(tzinfo=UTC(), microsecond=0).isoformat()


def GetFirstValue(projectElement, lookFor):
    '''
    Durchsucht die Subelemente des übergebenen Objekts nach dem gesuchten Attribut und gibt
    dessen Wert zurück.
    @param projectElement: ReportApi Element, welches zu durchsuchen ist.
    @type projectElement: ReportApi
    @param lookFor: Attribut, welches gesucht wird.
    @type lookFor: str
    @return: der Wert des gesuchten Attributs.
    @rtype: str, datetime, ...
    '''
    for item in projectElement.IterItems():
        if item.__class__.__name__ in [u'ConfigChange', u'Configuration']:
            continue
        if hasattr(item, lookFor) and callable(getattr(item, lookFor)):
            return getattr(item, lookFor)()
        else:
            return GetFirstValue(item, lookFor)
    return datetime.now() if lookFor == u'GetTime' else u'NONE'


def FilterShortName(shortName):
    '''
    Entfernt unerlaubte Sonderzeichen aus dem übergebenen String und ersetzt diese ggf. mit
    einem Unterstrich "_".
    Anschließend werden Unterstriche am Anfang und Ende des Strings entfernt.
    @param shortName: zu filternder String.
    @type shortName: str
    @return: bereinigter String.
    @rtype: str
    '''
    converter = PackageNameToATXTestCaseShortName()
    validShortname = converter.GetValidShortName(shortName)

    # Wenn der Shortname länger ist als die erlaubten 128 Zeichen (PlannedFolder _XY Zusatz-Counter
    # bedenken), dann als Fallback versuchen den Namen zu kürzen indem mögliche Unterstriche
    # komplett entfernt werden.
    maxLength = 128 - 3
    if len(validShortname) > maxLength:
        validShortname = AutoShortnameUnderscoreCut(validShortname, maxLength)

        if len(validShortname) <= maxLength:
            WPrint(_(u"Maximale Länge von 125 Zeichen beim ATX-Name '{0}' überschritten. "
                     u"Der Name wurde automatisch gekürzt durch das Entfernen von Unterstrichen").
                   format(shortName))

    if len(validShortname) > maxLength:
        EPrint(_(u"ATX-Name '{0}' ist zu lang - erlaubt sind max. 125 Zeichen!").format(shortName))

    return validShortname


def FilterUniqueShortName(shortname, counter):
    '''
    Kombiniert den übergebenen Shortname mit einer Zahl, damit wieder ein valider Shortname mit dem
    Suffix der Zahl entsteht um z.B. PlannedTestCases eindeutig zu gestalten.
    @param shortname: valider ATX-Shortname
    @type shortname: str
    @param counter: Zahl zur Zuweisung für den Shortname um diesen eindeutig in der ATX-Struktur
                    z.B. für die PlannedTestCases zu machen.
    @type counter: integer
    @return: zusammengesetzter Shortname
    @rtype: str
    '''
    converter = PackageNameToATXTestCaseShortName()
    # GGf. doppelte Unterstriche, falls {name} mit Unterstrich endet entfernen
    return converter.GetValidShortName(u'{name}_{count}'.format(name=shortname, count=counter))


def AutoShortnameUnderscoreCut(shortName, maxLength):
    '''
    Versucht den übergebenen Shortname automatisch auf die maximale Länge zu kürzem,
    wenn dieser Unterstriche enthält, die noch entfernt werden könnne.
    Dabei werden die Unterstriche vom Shortname-Ende her Stück für Stück gekürzt.
    @param shortName:
    @type shortName: str
    @param maxLength: erlaubte Maximallänge
    @type maxLength: integer
    @return: den soweit gekürzten Shortname, wie es möglich war - ggf. aber auch direkt den Input
             Parameter, wenn z.B. keine Unterstriche enthalten waren
    @rtype: str
    '''

    lastLength = len(shortName)
    newLength = len(shortName) - 1

    while newLength < lastLength and lastLength > maxLength:
        lastLength = len(shortName)

        shortName = u''.join(shortName.rsplit(u'_', 1))

        newLength = len(shortName)

        if newLength <= maxLength:
            break

    return shortName


def FilterSUCCESS(result):
    '''
    Tauscht das SUCCESS von ECU-TEST gegen PASSED von ATX
    @param shortName: zu filterndes Result.
    @type shortName: str
    @return: gefiltertes Result.
    @rtype: str
    '''
    return u'PASSED' if result == u'SUCCESS' else result


def FindDictInList(candidateList, searchKey, searchValue):
    '''
    Findet ein Dictionary in einer Liste, das für den übergebenen Schlüssel den gesuchten Wert
    aufweist.
    @param candidateList: Liste, die durchsucht wird
    @type candidateList: list
    @param searchKey: Schlüssel im dict, dessen Wert gesucht wird.
    @type searchKey: object
    @param searchValue: gesuchter Wert des Schlüssels.
    @type searchValue: object
    @return: Position des Elements, das die Bedingung erfüllt. Wenn nichts gefunden wird -1.
    @rtype: int
    '''
    for index, item in enumerate(candidateList):
        if searchKey in item and item[searchKey] == searchValue:
            return index
    return -1


def IsSkipped(item):
    '''
    Prüft, ob das übergebene Objekt für die Reportgenerierung übersprungen werden soll.
    Wird der Report mit einer alten ECU-TEST Version ausgeführt, deren Report API dieses
    Attribut noch nicht unterstützt, wird stets False zurück gegeben.
    @param item: Objekt, das auf die Eigenschaft geprüft wird
    @type item: Report API Element: ReportItem oder PackageItem
    @return: True wenn das Item übersprungen werden soll, sonst False
    @rtype: boolean
    '''
    if hasattr(item, u'IsSkipped') and callable(getattr(item, u'IsSkipped')):
        return getattr(item, u'IsSkipped')()
    return False


def CompareGlobalConstantsLists(a, b):
    '''
    Vergleicht zwei Listen von Dictionarys auf Gleichheit bzgl. deren Schlüssel und Werte
    (SHORT-NAME und VALUE). Weisen beide Listen die selben Dictionarys mit den selben
    Schlüsseln und Werten auf, ist Gleichheit gegeben. Unterscheiden sich die Keys oder
    deren Werte sind die Dictionarys und damit die Listen nicht gleich.
    @param a: erste Liste
    @type a: list->OrderedDict
    @param b: zweite Liste
    @type b: list->OrderedDict
    @return: True wenn beide Listen gleich sind, sonst False
    @rtype: boolean
    '''
    if len(a) is not len(b):
        return False

    for const in a:
        if FindDictInList(b, u'SHORT-NAME', const[u'SHORT-NAME']) is -1:
            return False

        if FindDictInList(b, u'VALUE', const[u'VALUE']) is -1:
            return False
    return True


def DetectConditionBlock(candidateList):
    '''
    @param candidateList: Liste der TestSteps
    @type candidateList: list
    @return: Dictionary mit Aussage ob ein Pre- bzw. Postcondition Block
             vorhanden ist. Falls ein Postcondition Block vorhanden ist
             gibt es zusätzliche einen Key, der die Position des Blocks
             spezifiziert.
    @return: dict
    '''
    if len(candidateList) == 0:
        return {'pre': False, u'post': False}

    result = {
        u'pre': candidateList[0][u'LONG-NAME'][u'L-4'][u'#'] == u'Precondition',
        u'post': False
    }

    for i, step in enumerate(candidateList):
        if step[u'LONG-NAME'][u'L-4'][u'#'] == u'Postcondition':
            result[u'post'] = True
            result[u'postIndex'] = i
            break

    return result


def ConvertConditionBlocks(testStepList, reportList):
    '''
    Verschiebt die Blöcke entsprechend ihrer Condition in das jeweilige ATX Pendant:
    * Precondition -> Setup
    * Action bzw. alles zwischen Pre- und Postcondition -> Execution
    * Postcondition -> Teardown
    @param testStepList: Liste der erzeugten TestSteps
    @type testStepList: list
    @param reportList: Liste der erzeugten Result TestSteps
    @type reportList: list
    @return: Dictionary mit den assoziierten TestSteps
    @rtype: dict
    '''
    conditionBlockSettings = DetectConditionBlock(testStepList)

    if not conditionBlockSettings[u'pre'] and not conditionBlockSettings[u'post']:
        return {'setup': [], u'execution': testStepList, u'teardown': [],
                u'reportSteps': {'setup': [], u'execution': reportList, u'teardown': []}}

    length = len(testStepList)
    if length != len(reportList):
        raise RuntimeError(u'Die Listen MÜSSEN die selbe Länge aufweisen!')

    returnValue = {
        u'setup': [],
        u'execution': [],
        u'teardown': [],
        u'reportSteps': {
            u'setup': [],
            u'execution': [],
            u'teardown': []
        }
    }

    start = 0
    end = length - 1

    if conditionBlockSettings[u'pre']:
        returnValue[u'setup'].append(deepcopy(testStepList[start]))
        returnValue[u'reportSteps'][u'setup'].append(deepcopy(reportList[start]))
        start += 1
        # der Precondition Block soll immer ein TestStepFolder sein:
        if returnValue[u'setup'][0][u'LONG-NAME'][u'L-4'][u'#'] == u'Precondition' and \
                returnValue[u'setup'][0][u'@type'] == u'TEST-STEP':
            returnValue[u'setup'][0][u'@type'] = u'TEST-STEP-FOLDER'
            returnValue[u'setup'][0][u'*TEST-STEPS'] = []
            returnValue[u'reportSteps'][u'setup'][0][u'@type'] = u'TEST-STEP-FOLDER'
            returnValue[u'reportSteps'][u'setup'][0][u'*TEST-STEPS'] = []

    if conditionBlockSettings[u'post']:
        for i in range(conditionBlockSettings[u'postIndex'], length):
            returnValue[u'teardown'].append(deepcopy(testStepList[i]))
            returnValue[u'reportSteps'][u'teardown'].append(deepcopy(reportList[i]))
        end = conditionBlockSettings[u'postIndex'] - 1
        # der Postcondition Block soll immer ein TestStepFolder sein:
        if returnValue[u'teardown'][0][u'LONG-NAME'][u'L-4'][u'#'] == u'Postcondition' and \
                returnValue[u'teardown'][0][u'@type'] == u'TEST-STEP':
            returnValue[u'teardown'][0][u'@type'] = u'TEST-STEP-FOLDER'
            returnValue[u'teardown'][0][u'*TEST-STEPS'] = []
            returnValue[u'reportSteps'][u'teardown'][0][u'@type'] = u'TEST-STEP-FOLDER'
            returnValue[u'reportSteps'][u'teardown'][0][u'*TEST-STEPS'] = []

    for testStep in testStepList[start:end + 1]:
        returnValue[u'execution'].append(deepcopy(testStep))

    for reportStep in reportList[start:end + 1]:
        returnValue[u'reportSteps'][u'execution'].append(deepcopy(reportStep))

    return returnValue


def GetExtendedWindowsPath(sourcePath):
    '''
    Fügt dem übergebenen Pfad die Extension dafür an, dass Windows auch mit mehr als 255 Zeichen
    Pfadlänge umgehen kann, dabei werden UNC-Pfad explizit gesondert betrachtet.
    @param sourcePath: Pfad, welcher erweitert werden soll.
    @type sourcePath: str
    @return: Windows-Pfad mit der Erweiterung für mehr als 255 Zeichen Pfadlänge.
    @rtype: str
    '''
    if len(sourcePath) >= 2:
        if sourcePath[1] == u":":
            realPath = os.path.normpath(sourcePath)
            sourcePath = u"\\\\?\\" + realPath
        elif sourcePath.startswith(u"\\\\") and not sourcePath.startswith(u"\\\\?\\"):
            sourcePath = u"\\\\?\\UNC\\" + sourcePath.lstrip(u"\\")
            sourcePath = os.path.realpath(sourcePath)
    return sourcePath


def GetConsumedFilesFromJobItem(item):
    '''
    Filtert aus dem übergebenen TraceAnalyeJob-Element die konsumierten Dateien.
    :param item: Element, in dem gesucht wird
    :type item: ReportItem
    :return: Liste der konsumierten Dateien als Pfad
    :rtype: list[Recording]
    '''
    from lib.report.parser.Package import ReportItem
    assert isinstance(item, ReportItem)

    if not hasattr(item, u'HasEntities') or not item.HasEntities():
        return ()

    return [
        entity.GetRecording(recordingIndex)
        for entity in item.IterEntities()
        if entity.GetType() == u'recordinginfosentity'
        for recordingIndex in range(entity.GetCount())
    ]


def GetNextShortNameInList(target, name):
    '''
    Ermittelt den nächsten freien ShortName in der Liste indem der
    Namen durch einen Incrementor erweitert wird, bis er verfügbar ist.
    @param target: Liste von Dicts, die einen SHORT-NAME Key haben
    @type target: list->dict
    @param name: gesuchter ShortName
    @type name: str
    @return: nächsten freien ShortNamen für die Liste
    @rtype: str
    '''
    i = 0
    result = FilterUniqueShortName(name, i)

    while FindDictInList(target, u'SHORT-NAME', result) >= 0:
        result = FilterUniqueShortName(name, i)
        i += 1

    return result


def HashFileContents(filePath):
    '''
    Erzeugt den MD5 Hash über den Inhalt der Datei.
    @param filePath: Pfad einer Datei
    @type filePath: str
    @return: MD5 Hash des Dateiinhalts
    @rtype: str
    '''
    hasher = hashlib.md5()
    with open(GetExtendedWindowsPath(filePath), u'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()


def FindAssociatedFilesForTrace(filePath):
    """
    Suche nach zu Trace zugehörigen Dateien (z.B. Side-Car-Files)

    :param filePath: Tracedatei.
    :type filePath: str
    :return: Liste mit Dateien
    :rtype: List[str]
    """
    possibleFiles = [filePath + ".recscf"]

    # CARMAKER
    if filePath.endswith(".erg"):
        possibleFiles.append(filePath + ".info")

    return list(filter(os.path.exists, possibleFiles))


def CopyFile(source, target):
    '''
    Kopiert die Source Datei in die Target-Datei. Dabei werden die Ordner-Strukturen für die
    Target-Datei angelegt, wenn diese noch nciht
    @param source: zu kopierende Datei
    @type source: str
    @param target: Datei, welche angelegt werden soll.
    @type target: str
    @return: True, wenn das kopieren erfolgreich war, sonst False.
    @rtype: boolean
    '''
    try:
        # Zielverzeichnis ggf. anlegen.
        targetDir = os.path.dirname(target)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)

        shutil.copy(source, target)
        return True
    except BaseException as ex:
        print(u"CopyFile: " + str(ex))
        return False


def MakeCompressedZip(sources, target):
    '''
    Speichert die übergebene Dateien in ein eigenes komprimiertes reproduzierbares ZIP Archiv.
    @param sources: Pfad zu einer oder mehreren Dateien
    @type sources: Iterable[str]
    @param target: Pfad der erzeugten ZIP Datei
    @type target: str
    '''
    try:
        # Zielverzeichnis ggf. anlegen.
        targetDir = os.path.dirname(target)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)

        with zipfile.ZipFile(target, u'w', zipfile.ZIP_DEFLATED, True) as zipHandler:
            if sys.version_info < (3,):
                for source in sources:
                    zipHandler.write(source, os.path.basename(source))
            else:
                for source in sources:
                    # ZIP reproduzierbar machen
                    zinfo = zipfile.ZipInfo(os.path.basename(source))
                    zinfo.external_attr = 0o600 << 16  # ?rw-------
                    zinfo.file_size = os.stat(source).st_size
                    zinfo.compress_type = zipfile.ZIP_DEFLATED

                    with open(source, "rb") as src, zipHandler.open(zinfo, 'w') as dest:
                        shutil.copyfileobj(src, dest, 1024 * 8)

    except BaseException as ex:
        print(u"MakeCompressedZip: " + str(ex))
        raise ex


def GetReviewsForPackage(report, pkg):
    '''
    Ermittelt alle direkten Nachbewertungen auf den Package und erzeugt für jede ein Review Objekt.
    @param report: Durchgereichtes ReportApi Objekt
    @type report: tts.core.report.parser.ReportApi
    @param pkg: Package zu dem Nachbewertungen erfasst werden
    @type pkg: Package
    @return Reviews aus Nachbewertungen
    @rtype: list->Review
    '''
    result = []
    for comment in list(report.IterUserComments(pkg.GetReportItemId())):
        if comment.GetAuthor():
            # Custom Verdict auf Packages wird im Moment nicht untertützt
            result.append(Review(comment, u"TA", -1, -1, None))
    return result


def GetReviewsForReportItem(report, reportItem):
    '''
    Ermittelt alle Nachbewertungen zu dem ReportItem und erzeugt für jede ein Review Objekt.
    @param report: Durchgereichtes ReportApi Objekt
    @type report: ReportApi
    @param reportItem: ReportItem, zu dem Nachbewertungen erfasst werden
    @type reportItem: ReportItem
    @return Reviews aus Nachbewertungen
    @rtype: list->Review
    '''
    result = []
    name = u'#{0} {1} ({2})'.format(reportItem.GetSrcIndex(), reportItem.GetName(),
                                    reportItem.GetActivity())
    
    for comment in list(report.IterUserComments(reportItem.GetId())):
        if comment.GetAuthor():
            abortCode = None
            if Config.GetSetting(report, u'reviewUseAbortCodeAsCustomEvaluation') == u"True":
                abortCode = reportItem.GetAbortCode()
                if abortCode:
                    abortCode = abortCode.strip("'")

            review = Review(comment,
                            name, 
                            reportItem.GetExecLevel(), 
                            reportItem.GetSrcIndex(), 
                            abortCode)

            detectTags = Config.GetSetting(report, u'detectReviewTags')
            for tag in __FindInReviewComment(comment.GetText(), detectTags, u'#'):
                review.AddReviewTag(tag)
            detectDefects = Config.GetSetting(report, u'detectReviewDefects')
            for i, defect in enumerate(__FindInReviewComment(comment.GetText(), detectDefects, u'|')):
                if i > 0:
                    raise DefectClassException(defect)
                review.SetDefectClass(defect)
            
            result.append(review)

    return result

def __FindInReviewComment(haystack, configParameter, circumfix):
    '''
    :param str haystack: Text der durchsucht wird
    :param str configParameter: Wert der Konfiguration
    :param str circumfix: umschließendes Zeichen
    :yield: ermittelte Werte
    '''
    for each in configParameter.strip().strip(u';').split(u';'):
        needle = each.strip()
        if needle:
            needle = u'{0}{1}{0}'.format(circumfix, needle)
            if haystack.find(needle) > -1:
                yield each

def UpdateRefOnReviews(reviews, reportRefPath):
    '''
    Aktuelle die übergebenen Reviews, anhand des passenden REF-Pfades zum Report TestCase.
    @param reviews: Liste der Reviews, welche aktualisiert werden sollen.
    @type reviews: List->Review
    @param reportRefPath: REF Pfad zum Report TestCase
    @type reportRefPath: str
    @return: Liste der Reviews in der korrekten Reihenfolge
    @rtype: List->Review
    '''
    for review in reviews:
        review.SetTestCaseRef(reportRefPath)

    resultList = GroupReviewsPerPackage(reviews)
    return resultList


def GroupReviewsPerPackage(reviews):
    '''
    Gruppiert die übergebenen Reviews eines Packages anhand der Reviews auf den Ebenen.
    Dabei werden Reviews unterer Ebenen dem übergeordneten Review als Kommentar-Anhang mitgeteilt.
    @param reviews: Liste der Reviews in einem Package, welche gruppiert werden sollen.
    @type reviews: list[Review]
    @return: Liste der gruppierten Reviews
    @rtype: list[Review]
    '''
    result = []

    currentLevel = 1000000
    lastReview = None
    for each in sorted(reviews):
        # Reviews auf gleicher Ebene erfassen, durch das sorted(reviews) gewinnt zeitlich
        # immer das Letzte Review -> ist dann das aktuellste
        if each.GetExecLevel() <= currentLevel:
            currentLevel = each.GetExecLevel()
            lastReview = each
            result.append(lastReview)
        elif lastReview is not None:
            lastReview.AppendReview(each)

    return result


def GetVerdictWeighting(atxVerdict):
    '''
    Ermittelt eine Gewichtung für das übergebene ATX-Verdict, damit ggf. dadurch ein
    Verdict-Ranking wie bei den Reviews vorgenommen werden kann.
    @param atxVerdict: ATX-Verdict, dessen Gewichtung ermittelt werden soll.
    @type atxVerdict: str
    @return: Gewichtung des Verdicts
    @rtype: interger
    '''
    verdicts = {}

    verdicts[u'NONE'] = 0
    verdicts[u'PASSED'] = 1
    verdicts[u'INCONCLUSIVE'] = 2
    verdicts[u'FAILED'] = 3
    verdicts[u'ERROR'] = 4

    return verdicts.get(atxVerdict)


def SplitVersionString(version):
    '''
    Ermittelt aus dem Versionsstring die einzelnen Bestandteile.
    @param version: Versionsstring, welcher in seine Bestandteile zerlegt werden soll
    @type version: str
    @return: major, minor, patch, rev Versionen als Tuple
    @rtype: str
    '''
    major = u"0"
    minor = u"0"
    patch = u"0"
    rev = u"0"

    DPrint(LEVEL_VERBOSE, u"SplitVersionString({0})".format(version))

    if version:
        tmp = version.split(u".")

        # Format 2020.1 mit Revision
        if len(tmp) == 3 and tmp[0].startswith("20"):
            major = tmp[0]
            minor = tmp[1]
            # Patch-Level gibt es nicht mehr
            # Wird aber für den Mix mit alten Versionen
            # beibeihalten und bleibt bei 0.
            patch = u"0"
            rev = tmp[2]

        # Altes Format 5.6.1 mit Revision
        if len(tmp) == 4:
            major = tmp[0]
            minor = tmp[1]
            patch = tmp[2]
            rev = tmp[3]

    return major, minor, patch, rev


def ShowInfoOnTaskManager(reportApi, message):
    '''
    Setzt im Taskmanager eine Info-Nachricht, damit die Nutzer sehen in welcher Phase sich die
    Generierung befindet.
    @param reportApi: Aktuelles Objekt der ReportAPI, die das Visual-Objekt für den Taskmanager
                      beinhaltet.
    @type reportApi: ReportApi
    @param message: Nachricht, die im TaskManager angezeigt werden soll.
    @type message: str
    @return: Interface zur Anzeige von Nachrichten im TaskManager oder None, wenn keins ermittelt
             werden konnte. Ist aus Performance-Gründen Hilfreich auf das Objekt zugreifen zu
             können.
    @rtype lib.common.workerThreads.WTCommon.IVisual
    '''
    if hasattr(reportApi, u"visual"):
        visual = reportApi.visual

        if visual and hasattr(visual, u'SetCaption'):
            visual.SetCaption(message)
            return visual

    return None


class EmptyReportException(Exception):
    '''
    Custom Exception wird verwendet um die Reportgenerierung und -übertragung abzubrechen,
    wenn keine Testcases erzeugt wurden.
    '''
    pass


class SameNameError(Exception):
    '''
    Custom Exception zeigt die doppelte Verwendung des gleichen Namens für ein Package und
    einen Ordner auf der selben Dateiebene.
    '''
    pass

class DefectClassException(Exception):
    '''
    Es darf nur eine Fehlerklassen je Review vergeben werden.
    '''
    def __init__(self, defectClass):
        self.defectClass = defectClass
