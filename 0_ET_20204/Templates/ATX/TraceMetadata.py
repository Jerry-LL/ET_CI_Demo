# -*- coding: utf-8 -*-

import os
import re
import json

from lib.report.db import Recording
from log import WPrint
from constantsVersionInfo import PRODUCT_NAME_VERSION

from .Version import GetVersion

SCHEMA_URI = "https://www.tracetronic.de/schemas/recording-1/schema.json"

# Extrahiert `<name> (<formatDetails>)`
_FORMATDETAILS_RE = re.compile(r"^(.*?) \((.*)\)$")

# Recording-Typ zu MIME-Typ
# Siehe: https://www.iana.org/assignments/media-types/media-types.xhtml
_MIME_TYPE_MAPPING = {
    "CSV": "text/csv",
    "MDF4": "application/MF4",
    "PCAP": "application/vnd.tcpdump.pcap",
    "ASC": "text/x.vector.asc",
    "BLF_VECTOR": "application/x.vector.blf",
    "TDMS": "application/x.tdms",
    "STI": "application/x.sti",
    "STZ": "application/x.stz",
    "TTL": "application/x.tttech.ttl",
    "CARMAKER": "application/x.carmaker.erg",
    "VTD_RDB": "application/x.vtd.rdb",
    "AUTOSPY": "application/x.tracetronic.autospy",  # ECU-TEST < 2020.1
    "AS3TRACE": "application/x.tracetronic.autospy",
}


def _RecordingTypeToMimeType(recordingType):
    '''
    Recordingtyp versuchen in MIME-Typ zu konvertieren
    '''
    if not recordingType:
        return None

    mimeType = _MIME_TYPE_MAPPING.get(recordingType)
    if mimeType is not None:
        return mimeType

    if recordingType.startswith("MDF_"):
        return "application/x.vector.mdf3"

    if recordingType.startswith("MAT_"):
        return "application/x.mathworks.mat"

    return None


def _ReadRecordingSignals(filePath, recording):
    '''
    Lese Signalnamen von Aufnahme.

    Benutzt Metadaten aus Report oder ließt Aufnahme neu ein.
    '''
    if hasattr(recording, "GetMetaData"):
        metadata = recording.GetMetaData()
        if metadata:
            try:
                metadataJson = json.loads(metadata)
            except json.JSONDecodeError as exp:
                # Wenn Meta-Daten für TREX nicht gelesen werden können wird das toleriert.
                WPrint("Invalid recording metadata: " + str(exp))
            else:
                if "signalNames" in metadataJson:
                    return metadataJson["signalNames"]

    return None


def SplitNameAndFormatDetails(recordingName):
    '''
    Aus Recording-Name von Report korrekten Recording-Name und Formatdetails extrahieren
    '''
    if not recordingName:
        return None, None

    match = _FORMATDETAILS_RE.match(recordingName)
    if match:
        return match.groups()
    else:
        return recordingName, ""


def GetMappingsOfRecording(recording):
    if hasattr(recording, "IterMappings"):
        return {
            mappingItem.GetName(): _GetMappingTarget(mappingItem)
            for mappingItem in recording.IterMappings()
        }
    else:
        # ECU-TEST < 8.1
        cur = recording.db.cursor()
        cur.execute(
            "SELECT name, target, type, global, used_raster, wanted_raster, forced_raster"
            " FROM mappingitem"
            " JOIN r_recording_mappingitem AS recmap"
            "   ON recmap.mappingitem_id=mappingitem.id"
            " WHERE recmap.recording_id=?",
            (recording.GetId(),))
        return {
            args[0]: _GetMappingTargetLegacy(*args) for args in cur.fetchall()
        }


def _GetMappingTarget(mappingItem):
    '''
    Mappinginformationen für Metadaten-JSON erzeugen
    '''
    result = {
        "type": mappingItem.GetType(),
        "targetPath": mappingItem.GetTarget(),
        "global": bool(mappingItem.IsGlobal())
    }

    usedRaster = mappingItem.GetUsedRaster()
    if usedRaster:
        result.update({
            "usedRaster": usedRaster,
            "wantedRaster": mappingItem.GetWantedRaster(),
            "forcedRaster": bool(mappingItem.IsForcedRaster()),
        })

    return result


def _GetMappingTargetLegacy(_name, target, type, isGlobal, usedRaster, wantedRaster, forcedRaster):
    '''
    Mappinginformationen für Metadaten-JSON erzeugen
    '''
    result = {
        "type": type,
        "targetPath": target,
        "global": bool(isGlobal)
    }

    if usedRaster:
        result.update({
            "usedRaster": usedRaster,
            "wantedRaster": wantedRaster,
            "forcedRaster": bool(forcedRaster),
        })

    return result


def _GetRecordingDetails(recordingDetails):
    '''
    Aufnahmeinformationen für Metadaten-JSON erzeugen

    :param recordingDetails: Von GenerateRecordingMetadata erzeugte Metadaten
    :rtype recordingDetails: Dict[str, Any]
    :return: Aufnahmeinformationen für Metadaten-JSON
    :rtype: Dict[str, Any]
    '''
    keys = [
        "mapping",
        "formatDetails",
        "recordingName",
        "recordingNumber",
        "recordingType",
        "recordingGroup",
        "signalGroup",
        "signalNames",
        "syncDeltaT"
    ]
    return {
        key: recordingDetails[key]
        for key in keys
        if recordingDetails[key] is not None
    }


def GenerateTraceMetadata(filePath, fileHash, recordings, created):
    '''
    :param filePath: Windows extended Dateipfad zu Aufnahmedatei
    :type filePath: str
    :param fileHash: MD5 Hash von Dateiinhalt
    :type fileHash: str
    :param recordings: Aufnahmemetadaten zu allen in Datei vorkommenden Aufnahmen erzeugt von
        GenerateRecordingMetadata
    :type recordings: List[Dict[str, Any]]
    :param created: Ob Aufnahme erstellt wurde
    :type created: bool
    :return: Aufnahmemetadaten für JSON Generierung
    :rtype: Dict[str, Any]
    '''
    result = {
        "$schema": SCHEMA_URI,
        "$generator": "{} (ATX-Generator {})".format(PRODUCT_NAME_VERSION, GetVersion()),
        "fileName": os.path.basename(filePath),
        "md5Hash": fileHash,
        "created": created,
        "recordings": [
            _GetRecordingDetails(recordingDetails) for recordingDetails in recordings
        ]
    }

    firstType = recordings[0]["recordingType"]
    if firstType and all(rec["recordingType"] == firstType for rec in recordings):
        mimeType = _RecordingTypeToMimeType(firstType)
        if mimeType:
            result["mimeType"] = mimeType

    return result


def _GetSyncDeltaT(recording):
    if hasattr(recording, "GetSyncDeltaT"):
        # ECU-TEST >= 2020.1
        return recording.GetSyncDeltaT()
    else:
        return None


def GenerateRecordingMetadata(filePath, recording):
    '''
    :param recording: Report-API Recording Objekt was verarbeitet werden soll
    :type recording: tts.core.report.parser.Package.Recording
    :return: Dict mit Metadaten zu Recording, die dann in die Metadaten zu Trace einfließen
    :rtype: Dict[str, Any]
    '''
    name, formatDetails = SplitNameAndFormatDetails(recording.GetName())
    metadata = {
        "recordingName": name,
        "formatDetails": formatDetails,
        "mapping": GetMappingsOfRecording(recording),
        "syncDeltaT": _GetSyncDeltaT(recording),
        "recordingNumber": recording.GetNumber(),
        "recordingType": recording.GetType(),
        "signalGroup": recording.GetSignalGroupName(),
        "recordingGroup": recording.GetGroupName(),
        "signalNames": _ReadRecordingSignals(filePath, recording)
    }
    return metadata

