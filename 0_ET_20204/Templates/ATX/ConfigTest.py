# -*- coding: utf-8 -*-

'''
Created on 27.10.2014

@author: Philipp
'''

import unittest
from mockito import mock, when

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    print("could not import FakeApiModules")
    pass

from .Config import Config, SettingsFromServerMode


class ConfigTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGetUnknownSetting(self):
        '''
        Prüft das bei unbekannten Settings (auch in der config.xml) ein None zurückgegeben wird.
        '''
        # ARRANGE
        settingName = u'unknownSetting'
        reportApiMock = mock()
        when(reportApiMock).GetSetting(settingName).thenReturn(None)

        # ACT
        value = Config.GetSetting(reportApiMock, settingName)

        # ASSERT
        self.assertEqual(None, value,
                         (u"Der Settingswert sollte None lauten für unbekannt Settings."))

    def testGetValidSetting(self):
        '''
        Prüft ob bei valider Setting diese auch korrekt zurückgegeben wird.
        '''
        # ARRANGE
        settingName = u'serverPort'
        expectedValue = 8085
        reportApiMock = mock()
        when(reportApiMock).GetSetting(settingName).thenReturn(expectedValue)

        # ACT
        value = Config.GetSetting(reportApiMock, settingName)
        # ASSERT
        self.assertEqual(expectedValue, value,
                         (u"Der Settingswert sollte {0} lauten.").format(expectedValue))

    def testGetValidButUnknownReportApiSetting(self):
        '''
        Prüft das aus der config.xml der Default-Wert für eine gültige Settings in der config.xml
        aber noch nicht bekannte Settings in der ReportApi (Problem AutoUpdate) ermittelt wird.
        '''
        # ARRANGE
        settingName = u'serverURL'
        reportApiMock = mock()
        when(reportApiMock).GetSetting(settingName).thenReturn(None)

        # ACT
        value = Config.GetSetting(reportApiMock, settingName)
        # ASSERT
        self.assertEqual(u"127.0.0.1", value,
                         (u"Der Defaultwert der noch nicht bekannten Settings sollte aus der "
                          u"config.xml ausgelesen werden."))

    def testExternalSettingsOverwriteInternal(self):
        # ARRANGE
        settingName = u'maxUploadTries'
        expectedValue = 333
        reportApiMock = mock()
        when(reportApiMock).GetSetting(settingName).thenReturn(1230975)
        Config.LoadExternalSettings([{"key": settingName, "value": expectedValue}], SettingsFromServerMode.ALWAYS)

        # ACT
        value = Config.GetSetting(reportApiMock, settingName)
        Config.ClearExternalSettings()

        # ASSERT
        self.assertEqual(expectedValue, value,
                         (u"Der Settingswert sollte {0} lauten.").format(expectedValue))

    def testExternalSettingsRespectDefaultValue(self):
        # ARRANGE
        settingName = u'maxUploadTries'
        reportApiMock = mock()
        Config.LoadExternalSettings([], SettingsFromServerMode.ALWAYS)

        # ACT
        value = Config.GetSetting(reportApiMock, settingName)
        Config.ClearExternalSettings()

        # ASSERT
        self.assertEqual(u"42", value,
                         (u"Der Defaultwert der nicht gesetzten Settings sollte aus der "
                          u"config.xml ausgelesen werden."))

    def testExternalSettings_UseKeyword(self):
        # ARRANGE
        settingName = u'maxUploadTries'
        reportApiMock = mock()
        remoteConfigValue = u'RemoteConfiguration'
        keyword = u'Friendship is magic'
        when(reportApiMock).GetSetting(settingName).thenReturn(keyword)
        Config.LoadExternalSettings([{ u'key': settingName, u'value': remoteConfigValue }], SettingsFromServerMode.WHEREKEYWORD, keyword)
        
        # ACT
        value = Config.GetSetting(reportApiMock, settingName)
        Config.ClearExternalSettings()

        # ASSERT
        self.assertEqual(remoteConfigValue, value, 
                         u'Die Konfiguration vom Server sollte verwendet worden sein.')

    def testExternalSettings_UseKeyword_SkipServerSettings(self):
        # ARRANGE
        settingName = u'maxUploadTries'
        reportApiMock = mock()
        keyword = u'Friendship is magic'
        settingValue = u'anything'
        when(reportApiMock).GetSetting(settingName).thenReturn(settingValue)
        Config.LoadExternalSettings([{ u'key': settingName, u'value': u'RemoteConfiguration' }], SettingsFromServerMode.WHEREKEYWORD, keyword)

        # ACT
        value = Config.GetSetting(reportApiMock, settingName)
        Config.ClearExternalSettings()

        # ASSERT
        self.assertEqual(settingValue, value, 
                         u'Die Konfiguration vom Server sollte ignoriert worden sein.')

    def testExternalSettings_UseKeyword_UndefindedOnServerUsesDefault(self):
        # ARRANGE
        settingName = u'maxUploadTries'
        reportApiMock = mock()
        keyword = u'Friendship is magic'
        when(reportApiMock).GetSetting(settingName).thenReturn(keyword)

        Config.LoadExternalSettings([], SettingsFromServerMode.WHEREKEYWORD, keyword)

        # ACT
        value = Config.GetSetting(reportApiMock, settingName)
        Config.ClearExternalSettings()

        # ASSERT
        self.assertEqual('42', value,
                         u'Der Default-Wert aus der config.xml sollte verwendet worden sein.')

if __name__ == "__main__":
    unittest.main()
