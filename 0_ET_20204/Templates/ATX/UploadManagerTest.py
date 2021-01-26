# -*- coding: utf-8 -*-

'''
Created on 20.11.2014

@author: Philipp
'''

import json
import os
import gettext
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import datetime
import dateutil.relativedelta

from mockito import mock, when
from http import HTTPStatus

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass
from .UploadManager import UploadManager


class UploadManagerTest(unittest.TestCase):
    '''
    Tests für den UploadManager.
    '''

    def setUp(self):
        self._oldTempDir = tempfile.gettempdir()
        unittest.TestCase.setUp(self)
        gettext.NullTranslations().install()

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testUrlWithContextPath(self):
        reportApiMock = mock()
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           useHttps=True, contextPath=u"test-guide")
        self.assertEqual(um.GetTargetUrl(),
                         (u"https://127.0.0.1:8085/test-guide/api/upload-file?apiVersion=1.5.1"
                          u"&authKey=&projectId=1&async=true"))

    def testStatusUrlWithContextPath(self):
        reportApiMock = mock()
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           useHttps=True, contextPath=u"test-guide")
        self.assertEqual(um.GetStatusUrl(u"/api/upload-file/status/42"),
                         u"https://127.0.0.1:8085/test-guide/api/upload-file/status/42?authKey=")

    def testStatusUrlWithoutContextPath(self):
        reportApiMock = mock()
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           useHttps=True)
        self.assertEqual(um.GetStatusUrl(u"/api/upload-file/status/42"),
                         u"https://127.0.0.1:8085/api/upload-file/status/42?authKey=")

    def testHttpsUrl(self):
        reportApiMock = mock()
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           useHttps=True)
        self.assertEqual(um.GetTargetUrl(),
                         (u"https://127.0.0.1:8085/api/upload-file?apiVersion=1.5.1&authKey="
                          u"&projectId=1&async=true"))

    def testDefaultHttpUrl(self):
        reportApiMock = mock()
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath")
        self.assertEqual(um.GetTargetUrl(),
                         (u"http://127.0.0.1:8085/api/upload-file?apiVersion=1.5.1&authKey="
                          u"&projectId=1&async=true"))

    def testHttpAuthKeyUrl(self):
        # ARRANGE
        authKey = (u"egBnG8EOnkGttaW0yEkon%2B%2BzSh7RUCW5Id6ze8gnjrTayPKEkOhxq1pmx4Pgj8chH35ZnCniSw"
                   u"wYscK%2Boej8aqOU0zE4skvFnCtdkitP4o4zrrP2Xy%2BIm7C6XBuju7XQ8KHstUyLagzSY3QKKhbB"
                   u"lz1gPll%2FFINg%2BX%2BXjeoas2ftpI8%2FW%2FhfuQPqaFavstq1uxKeDg0U2h8cJsLvDxKj4FeQ"
                   u"CqBaPdOwDduQJgwZzW7vZc43tTp%2BmJdRqAuRveYqPo1zWpX%2FinL2JHnft2g4nV0OLpPJ0zpBUw"
                   u"k%2BKiVunww%3D")
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'uploadAuthenticationKey').thenReturn(authKey)
        # ACT
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath")
        # ASSERT
        self.assertEqual(um.GetTargetUrl(),
                         (u"http://127.0.0.1:8085/api/upload-file"
                          u"?apiVersion=1.5.1&authKey={0}&projectId=1&async=true").format(authKey))

    def testBigFileUpload(self):
        '''
        Prüfung das kein MemoryError beim Upload von großen Dateien erfolgt.
        '''
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetReportDir().thenReturn(tempfile.gettempdir())

        fileTemp = tempfile.NamedTemporaryFile(prefix=u"bigUploadFile", delete=False)
        try:
            # Beispieldatei mit > 1000MB erzeugen
            with open(fileTemp.name, u"wb") as out:
                out.seek((1024 * 1024 * 1024) - 1)
                out.write(b'\0')

            um = UploadManager(reportApiMock, u"1.5.1", u'file-upload',
                               u"BigFile.zip", fileTemp.name, url=u"localhostInvalidUrl")

            # ACT
            try:
                # ASSERT
                # Es darf kein Memory Error auftreten beim Upload.
                self.assertTrue(not um.StartUpload(),
                                u"Upload von falscher URL darf nicht möglich sein.")
            except MemoryError:
                self.fail(u"MemoryError ist aufgetreten.")

        finally:
            fileTemp.close()
            os.remove(fileTemp.name)

    def testGetConfigUploadTriesOnEmptySetting(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("")
        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath")
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 1)

    def testGetConfigUploadTriesOnInvalidSetting(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("jo10")
        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath")
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 1)

    def testGetConfigUploadTriesOnInvalidFloatSetting(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("10.05")
        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath")
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 1)

    def testGetConfigUploadTriesOnUnlimited(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("-1")
        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath")
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 9223372036854775807)

    def testHealthReadyUrlWithContextPath(self):
        reportApiMock = mock()
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           useHttps=True, contextPath=u"test-guide")
        self.assertEqual(um.GetHealthReadyUrl(),
                         u"https://127.0.0.1:8085/test-guide/api/health/ready")

    def testHealthReadyUrlWithoutContextPath(self):
        # ARRANGE
        reportApiMock = mock()
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           useHttps=True)
        # ACT + ASSERT
        self.assertEqual(um.GetHealthReadyUrl(),
                         u"https://127.0.0.1:8085/api/health/ready")

    def testParseRetryAfterInvalidValue(self):
        # ARRANGE
        # ACT + ASSERT
        self.assertEqual(UploadManager.ParseRetryAfter(None), -1)
        self.assertEqual(UploadManager.ParseRetryAfter(-10), -1)
        self.assertEqual(UploadManager.ParseRetryAfter(12), -1)
        self.assertEqual(UploadManager.ParseRetryAfter("-10"), -1)
        self.assertEqual(UploadManager.ParseRetryAfter("Blalba"), -1)

    def testParseRetryAfterWithValidSeconds(self):
        # ARRANGE
        # ACT + ASSERT
        self.assertEqual(UploadManager.ParseRetryAfter("10"), 10)
        self.assertEqual(UploadManager.ParseRetryAfter(u"11"), 11)

    def testParseRetryAfterWithOverLimitSeconds(self):
        # ARRANGE
        expected = 4 * 60 * 60  # Max 4h
        inputVal = 5 * 60 * 60  # 5h
        # ACT + ASSERT
        self.assertEqual(UploadManager.ParseRetryAfter(str(inputVal)), expected)

    def testParseRetryAfterWithValidDateValue(self):
        # ARRANGE
        # Bsp: date = u"Wed, 20 May 2020 16:00:00 GMT"
        now = datetime.datetime.now()
        now = now + dateutil.relativedelta.relativedelta(minutes=5)

        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

        # ACT + ASSERT
        self.assertGreaterEqual(UploadManager.ParseRetryAfter(date), 295,
                                u"Es sollten ~5min bis zum nächsten Retry ermittelt werden.")
        self.assertLessEqual(UploadManager.ParseRetryAfter(date), 300,
                             u"Es sollten ~5min bis zum nächsten Retry ermittelt werden.")

    def testUploadTriesOnMaintenanceStatus(self):
        # ARRANGE
        uploadTries = 2
        port = 9085
        MockMaintenanceStatusRequestHandler.POST_RETRY_AFTER_SEC = 1
        mock_server = HTTPServer(('localhost', port), MockMaintenanceStatusRequestHandler)
        mock_server_thread = Thread(target=mock_server.serve_forever)
        mock_server_thread.setDaemon(True)
        mock_server_thread.start()

        reportApiMock = mock()
        when(reportApiMock).GetReportDir().thenReturn(tempfile.gettempdir())
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn(str(uploadTries))

        with tempfile.NamedTemporaryFile(prefix=u"uploadFile", delete=False) as fileTemp:
            fileTemp.write(b'Test')
            fileTemp.flush()

        # ACT
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"File.zip",
                           fileTemp.name, port=port)

        # ASSERT
        self.assertFalse(um.StartUpload())
        self.assertEqual(um.GetCounterUploadTries(), uploadTries)
        self.assertEqual(um.GetLastRetryAfterPeriod(),
                         MockMaintenanceStatusRequestHandler.POST_RETRY_AFTER_SEC)

        os.remove(fileTemp.name)

    def testUploadErrorLogOnUploadFailedOnMaintenanceStatus(self):
        # ARRANGE
        port = 9087
        MockMaintenanceStatusRequestHandler.POST_RETRY_AFTER_SEC = 0
        mock_server = HTTPServer(('localhost', port), MockMaintenanceStatusRequestHandler)
        mock_server_thread = Thread(target=mock_server.serve_forever)
        mock_server_thread.setDaemon(True)
        mock_server_thread.start()

        reportApiMock = mock()
        when(reportApiMock).GetReportDir().thenReturn(tempfile.gettempdir())
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("1")
        errorJson = os.path.join(reportApiMock.GetReportDir(), u"error.raw.json")

        if os.path.exists(errorJson):
            os.remove(errorJson)

        with tempfile.NamedTemporaryFile(prefix=u"uploadFile", delete=False) as fileTemp:
            fileTemp.write(b'Test')
            fileTemp.flush()
        try:
            # ACT
            um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"File.zip",
                               fileTemp.name, port=port)

            # ASSERT
            self.assertFalse(um.StartUpload())
            self.assertTrue(os.path.exists(errorJson))

            with open(errorJson) as jsonFile:
                errorResponse = json.loads(jsonFile.read())
                self.assertEqual(errorResponse[u"messages"][0][u"statusCode"], 503)
        finally:
            os.remove(fileTemp.name)

    def testUploadToResourceAdapterBuffer(self):
        '''
        Prüfung für Upload über ResourceAdapter.
        '''
        # ARRANGE
        port = 44422
        mock_server = HTTPServer(('localhost', port), MockServerPostEndpoint)
        mock_server_thread = Thread(target=mock_server.serve_forever)
        mock_server_thread.setDaemon(True)
        mock_server_thread.start()
        
        reportApiMock = mock()
        when(reportApiMock).GetReportDir().thenReturn(tempfile.gettempdir())
        when(reportApiMock).GetSetting(u'projectId').thenReturn(u'123')
        when(reportApiMock).GetSetting(u'uploadAuthenticationKey').thenReturn(u'AuthKey==')
        when(reportApiMock).GetSetting(u'uploadThroughResourceAdapter').thenReturn(port)

        with tempfile.NamedTemporaryFile(prefix=u'uploadFile', delete=False) as fileTemp:
            fileTemp.write(b'Test')
            fileTemp.flush()
        try:
            um = UploadManager(reportApiMock, u'1.5.1', u'file-upload',
                               u'File.zip', fileTemp.name)

            # ACT
            result = um.StartUpload()
            
            # ASSERT
            self.assertTrue(result)

        finally:
            fileTemp.close()
            os.remove(fileTemp.name)

class MockMaintenanceStatusRequestHandler(BaseHTTPRequestHandler):
    '''
    Mock-Server für den Upload im Wartungsmodus.
    '''

    POST_STATUS_CODE = 503
    POST_RETRY_AFTER_SEC = 1

    def __Response(self):
        self.send_response(self.POST_STATUS_CODE)
        self.send_header("Retry-After", self.POST_RETRY_AFTER_SEC)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        self.__Response()

    def do_POST(self):
        # !!! Daten vorher nicht voll empfangen!!!!
        # content_length = int(self.headers['Content-Length'])
        # self.rfile.read(content_length)
        self.__Response()
        # self.wfile.write(bytes('Client: {0}\n'.format(str(self.client_address)), 'utf-8'))
        # self.wfile.write(bytes('User-agent: {0}\n'.format(str(self.headers['user-agent'])),
        #                       'utf-8'))
        # self.wfile.write(bytes('Path: {0}\n'.format(str(self.path)), 'utf-8'))

class MockServerPostEndpoint(BaseHTTPRequestHandler):
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        self.rfile.read(content_length)
        self.send_response(202)
        self.end_headers()

if __name__ == "__main__":
    unittest.main()
