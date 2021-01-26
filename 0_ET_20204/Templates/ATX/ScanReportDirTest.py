# -*- coding: utf-8 -*-

"""
Created on 13.10.2014

@author: Christoph Groß <christoph.gross@tracetronic.de>
"""

from datetime import datetime
import unittest
from unittest.mock import patch
import tempfile
import os
import shutil
import zipfile

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass
from .ScanReportDir import ScanReportDir
from mockito import mock, when


class ScanReportDirTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(ScanReportDirTest, cls).setUpClass()
        try:
            cls.__tmpDir = tempfile.mkdtemp(u'_ScanReportDirTest')
        except BaseException:
            cls.tearDownClass()

    @classmethod
    def tearDownClass(cls):
        super(ScanReportDirTest, cls).tearDownClass()
        shutil.rmtree(cls.__tmpDir, True)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testEmptyPattern(self):
        # ARRANGE
        struct = {
            u'testEmptyPattern': {
                u'testReportDir': {}
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')
        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertEqual(None, path, u'Es sollte "None" zurück gegeben werden.')

    def testSimplePatternWithUmlaut(self):
        # ARRANGE
        struct = {
            u'testSimplePatternWithUmlaut': {
                u'testReportDir_ÜöÄ': {
                    u'TestFile_öÄü.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(
            u'testReportDir_ÜöÄ/TestFile_öÄü.xml')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [os.path.join(u'testReportDir_ÜöÄ/TestFile_öÄü.xml')])

    def testSimpleFileMiscNameWithPrefix(self):
        # ARRANGE
        prefix = u'MyPräfix'
        struct = {
            u'testSimpleFileMiscNameWithPräfix': {
                u'testReportDir': {
                    u'TestFile.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(
            u'testReportDir/TestFile.xml')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')
        when(reportApiMock).GetSetting(u'archiveMiscFilePrefix').thenReturn(prefix)

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive(reportApiMock.GetSetting(u'archiveMiscFilePrefix'),
                                                reportApiMock.GetReportDir())

        # ASSERT
        self.assertTrue(os.path.basename(path).startswith(prefix))

    def testSimpleFileMiscName(self):
        # ARRANGE
        struct = {
            u'testSimpleFileMiscName': {
                u'testReportDir': {
                    u'Simple.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'testReportDir/Simple.xml')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        now = datetime.now()
        with patch('{}.datetime'.format(ScanReportDir.__module__)) as mock_datetime:
            mock_datetime.now.return_value = now
            path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                                 reportApiMock.GetSetting(u'archiveMiscFiles')
                                 ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        expectedPrefix = now.strftime(u'%Y-%m-%d_%H%M%S')
        self.assertTrue(os.path.basename(path).startswith(expectedPrefix))

    def testSimpleFileExpScannedList(self):
        # ARRANGE
        struct = {
            u'testSimpleFileMiscName2': {
                u'testReportDir': {
                    u'Simpl2e.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'testReportDir/Simpl2e.xml')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        files = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                              reportApiMock.GetSetting(u'archiveMiscFiles')
                              ).GetScannedFiles()

        # ASSERT
        self.assertTrue(len(files) == 1)
        result = files.pop()
        print(result)
        self.assertTrue(result.endswith(u"Simpl2e.xml"))

    def testSimplePattern(self):
        # ARRANGE
        struct = {
            u'testSimplePattern': {
                u'testReportDir': {
                    u'Simple.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'testReportDir/Simple.xml')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [os.path.join(u'testReportDir/Simple.xml')])

    def testIgnoreATXFolderWithReportXML(self):
        # ARRANGE
        struct = {
            u'testIgnoreSpecialReportXmlFolder': {
                u'testReportDir': {
                    u'ATXUpload': {
                        u'xyz.zip': None,
                        u'report.xml': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'**/*')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertTrue(path is None,
                        u'Es keine Zip Datei erstellt wurden sein, da keine Daten vorhanden waren.')

    def testIgnoreATXFolderWithMappingXML(self):
        # ARRANGE
        struct = {
            u'testIgnoreSpecialMappingXmlFolder': {
                u'testReportDir': {
                    u'ATX-Export': {
                        u'xyz.zip': None,
                        u'mapping.xml': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)

        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'**/*')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertTrue(path is None,
                        u'Es keine Zip Datei erstellt wurden sein, da keine Daten vorhanden waren.')

    def testIgnoreATXFolderWithMappingAndReportXML(self):
        # ARRANGE
        struct = {
            u'testIgnoreSpecialMappingAndReportXmlFolder': {
                u'testReportDir': {
                    u'Neues ATX Format': {
                        u'xyz.zip': None,
                        u'report.xml': None,
                        u'mapping.xml': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'**/*')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertTrue(path is None,
                        u'Es keine Zip Datei erstellt wurden sein, da keine Daten vorhanden waren.')

    def testNotIgnoreAllWithATXFolder(self):
        # ARRANGE
        struct = {
            u'testIgnoreSpecialAllFolder': {
                u'testReportDir': {
                    u'Logs': {
                        u'xyz.zip': None,
                        u'outLog.log': None,
                        u'errLog.log': None
                    },
                    u'ATXUpload': {
                        u'xyz2.zip': None,
                        u'report.xml': None,
                        u'mapping.xml': None
                    }
                }
            }
        }

        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'**/*')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [
            u'testReportDir/Logs/xyz.zip',
            u'testReportDir/Logs/outLog.log',
            u'testReportDir/Logs/errLog.log',
        ])

    def testDoubleStarPattern(self):
        # ARRANGE
        struct = {
            u'testDoubleStarPattern': {
                u'testReportDir': {
                    u'Foo.ext': None,
                    u'Bar.ext': None,
                    u'Baz.ext': None,
                    u'SomeDir': {},
                    u'AnotherDir': {
                        u'SubDir': {},
                        u'SubFile.ext': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'**')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [
            u'testReportDir/Foo.ext',
            u'testReportDir/Bar.ext',
            u'testReportDir/Baz.ext',
            u'testReportDir/AnotherDir/SubFile.ext'
        ])

    def testFindFilesByExtension(self):
        # ARRANGE
        struct = {
            u'testFindFilesByExtension': {
                u'testReportDir': {
                    u'Foo.ext': None,
                    u'Bar.pdf': None,
                    u'Baz.doc': None,
                    u'SomeDir': {},
                    u'AnotherDir': {
                        u'SubDir': {},
                        u'SubFile.ext': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'**/*.ext')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [
            u'testReportDir/Foo.ext',
            u'testReportDir/AnotherDir/SubFile.ext'
        ])

    def testPatternBeginsWithFolder(self):
        # ARRANGE
        struct = {
            u'testPatternBeginsWithFolder': {
                u'testReportDir': {
                    u'SomeDir': {},
                    u'AnotherDir': {
                        u'SubDir1': {
                            u'SubDir2': {
                                u'SubDir3': {
                                    u'Foo.ext': None
                                },
                                u'SubFile.ext': None
                            },
                            u'Bar.pdf': None
                        },
                        u'Baz.doc': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'testReportDir/**/*.ext')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [
            u'testReportDir/AnotherDir/SubDir1/SubDir2/SubDir3/Foo.ext',
            u'testReportDir/AnotherDir/SubDir1/SubDir2/SubFile.ext'
        ])

    def testFileAnywhereWithAnyExtension(self):
        # ARRANGE
        struct = {
            u'testFileAnywhereWithAnyExtension': {
                u'testReportDir': {
                    u'Bar': {},
                    u'AnotherDir': {
                        u'SubDir1': {
                            u'SubDir2': {
                                u'SubDir3': {
                                    u'Bar.ext': None
                                },
                                u'SubFile.ext': None
                            },
                            u'Bar.pdf': None
                        },
                        u'Bar.doc': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'**/Bar.*')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [
            u'testReportDir/AnotherDir/SubDir1/SubDir2/SubDir3/Bar.ext',
            u'testReportDir/AnotherDir/SubDir1/Bar.pdf',
            u'testReportDir/AnotherDir/Bar.doc'
        ])

    def testArchiveMiscFilesOnlyInTestReportDirOptionOnInvalidDir(self):
        # ARRANGE
        struct = {
            u'testSimplePattern2': {
                u'testReportDir': {
                    u'TestFile2.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)

        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'True')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertEqual(None, path, u'Es sollte "None" zurück gegeben werden.')

    def testArchiveMiscFilesOnlyInTestReportDirOptionOnValidDir(self):
        # ARRANGE
        struct = {
            u'testSimplePattern3': {
                u'testReportDir': {
                    u'TestFil3.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(self.__tmpDir)

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)

        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(u'testReportDir/TestFil3.xml')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'True')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [os.path.join(u'testReportDir/TestFil3.xml')])

    def testArchiveMiscFilesOnlyInTestReportDirOptionOnValidNonWorkspaceDir(self):
        # ARRANGE
        struct = {
            u'testFileValidNonWorkspace': {
                u'testReportDir': {
                    u'Bar_2017-09-14_225305': {
                        u'SubDir1': {
                            u'SubDir2': {
                                u'SubFile.ext': None
                            },
                            u'SubDir1.trf': None,
                            u'SubDir1.pdf': None
                        },
                        u'Bar.trf': None,
                        u'BarFile.xml': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(os.path.join(self.__tmpDir, u"BlaBar"))

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)

        when(reportApiMock).GetDbFile().thenReturn(os.path.join(self.__tmpDir,
                                                                u"testFileValidNonWorkspace",
                                                                u"testReportDir",
                                                                u"Bar_2017-09-14_225305",
                                                                u"Bar.trf"))

        expectedFile = u'testReportDir/Bar_2017-09-14_225305/BarFile.xml'
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(expectedFile)
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'True')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [os.path.join(expectedFile)])

    def testArchiveMiscFilesOnlyInSpecialSubProjektTestReportDirOptionOnValidNonWorkspaceDir(self):
        # ARRANGE
        struct = {
            u'testFileWithSubProject': {
                u'testReportDir': {
                    u'Bar_2017-09-14_225305': {
                        u'SubSpecialNameDir': {
                            u'SubDir2': {
                                u'SubFile.ext': None
                            },
                            u'SubProject.trf': None,
                            u'Sub.pdf': None
                        },
                        u'Bar.trf': None
                    }
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(os.path.join(self.__tmpDir, u"BlaBlaBar"))

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)

        when(reportApiMock).GetDbFile().thenReturn(os.path.join(self.__tmpDir,
                                                                u"testFileWithSubProject",
                                                                u"testReportDir",
                                                                u"Bar_2017-09-14_225305",
                                                                u"SubSpecialNameDir",
                                                                u"SubProject.trf"))

        expectedFile = u'testReportDir/Bar_2017-09-14_225305/SubSpecialNameDir/Sub.pdf'
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(expectedFile)
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'True')

        # ACT
        path = ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                             reportApiMock.GetSetting(u'archiveMiscFiles')
                             ).CreateZipArchive("", reportApiMock.GetReportDir())

        # ASSERT
        self.assertZipFile(path, [os.path.join(expectedFile)])

    def testRaiseExceptionOnScanWithProblems(self):
        # ARRANGE
        struct = {
            u'testSimplePatternN': {
                u'testReportDirN': {
                    u'SimpleN.xml': None
                }
            }
        }
        apiMock = mock()
        when(apiMock).GetSetting(u"reportPath").thenReturn(u'')

        reportApiMock = self.createTestFileSystem(struct, self.__tmpDir, True)
        when(reportApiMock).GetSetting(u'archiveMiscFiles').thenReturn(
            u'testReportDirN/SimpleN.xml')
        when(reportApiMock).GetSetting(u'archiveMiscFilesOnlyInTestReportDir').thenReturn(u'False')

        # ACT +  ASSERT
        with self.assertRaises(BaseException):
            ScanReportDir(reportApiMock, apiMock, reportApiMock.GetDbDir(),
                          reportApiMock.GetSetting(u'archiveMiscFiles')
                          ).CreateZipArchive("", u"?")  # Fehler beim Zip provozieren

    # Test Utility Methoden
    def createTestFileSystem(self, structure, target, init=False):
        '''
        Erzeugt aus der übergebenen dict eine Datei und Ordnerstruktur, welche als Testumgebung
        dient.
        Ist der Parameter init mit True gesetzt, wird ein gemocktes ReportApi Element zurückgegeben,
        welches bereits die Methoden GetDbDir und GetReportDir abfängt und die erstellten Pfaden
        durchreicht.
        Das dict muss dafür einem Muster folgen: Die erste Ebene hat nur einen Key, von dessen
        Value-dict der erste Key ebenfalls ein Ordner sein muss. Ansonsten arbeitet die Funktion
        sich rekursiv durch das dict.
        @param structure: dict mit den zu erzeugenden Datei Objekten
        @type structure: Mock
        @param target: Ziel Pfad, in dem die Datei Objekte erzeugt werden sollen
        @type target: str
        @param init: Gibt an ob das gemockte Report API Objekt zurück gegeben werden soll
        @type init: Boolean
        u'''
        for key, value in structure.items():
            if value is None:
                open(os.path.join(target, key), u'ab').close()
            else:
                path = os.path.join(target, key)
                os.mkdir(path)
                self.createTestFileSystem(value, path)

        if init:
            # Wenn der key nicht initialisiert ist, dann soll auch hier ein Fehler kommen!
            reportApiMock = mock()

            when(reportApiMock).GetDbDir().thenReturn(os.path.join(self.__tmpDir, key))
            when(reportApiMock).GetReportDir().thenReturn(os.path.join(self.__tmpDir, key,
                                                                       next(iter(value.keys()))))
            return reportApiMock

    def assertZipFile(self, path, expectedContent):
        '''
        Methode zur Überprüfung der generierten Zip Datei.
        @param path: Pfad zur Zip Datei
        @type path: Path
        @param expectedContent: Liste mit relativen Pfaden, die in der Zip Datei enthalten sein
                                müssen
        @type expectedContent: list->str
        '''
        try:
            if not os.path.isfile(path):
                self.fail(u'Der Pfad ist zeigt nicht auf eine Datei: {0}'.format(path))
        except BaseException:
            self.fail(u'Kein gültiger Pfad übergeben: {0}'.format(path))

        if not os.path.exists(path):
            self.fail(u'Die Datei existiert unter dem angegeben Pfad nicht: {0}'.format(path))

        self.assertTrue(zipfile.is_zipfile(path), u'Es sollte sich um eine Zip Datei handeln.')
        self.assertZipFileContents(path, expectedContent)

    def assertZipFileContents(self, path, expectedContent):
        '''
        Methode zur Überprüfung der Inhalte der generierten Zip Datei.
        @param path: Pfad zur Zip Datei
        @type path: Path
        @param expectedContent: Liste mit relativen Pfaden, die in der Zip Datei enthalten sein
                                müssen
        @type expectedContent: list->str
        '''
        with zipfile.ZipFile(path, u'r') as zf:
            self.assertEqual(len(expectedContent),
                             len(zf.namelist()),
                             (u'Es wurden genauso viele Dateien archiviert ({0}) wie '
                              u'erwartet ({1}).').format(len(expectedContent),
                                                         len(zf.namelist())))
            for each in expectedContent:
                self.assertTrue(each in zf.namelist(),
                                u'Die Datei {0} sollte im Zip enthalten sein.'.format(each))


if __name__ == '__main__':
    unittest.main()
