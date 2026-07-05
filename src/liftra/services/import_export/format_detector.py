"""
Format detection for import/export files.
"""

import csv
import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from typing import BinaryIO


class ImportFormat(str, Enum):
    """Supported import/export formats."""

    CSV = "csv"
    OFX = "ofx"
    QIF = "qif"
    HOMEBANK = "homebank"
    UNKNOWN = "unknown"


def detect_format(file_path: str | Path) -> ImportFormat:
    """
    Detect the format of an import file.
    
    Args:
        file_path: Path to the file to detect
        
    Returns:
        The detected ImportFormat
    """
    path = Path(file_path)
    
    # Check file extension first
    extension = path.suffix.lower()
    
    if extension == ".csv":
        return ImportFormat.CSV
    elif extension == ".ofx":
        return ImportFormat.OFX
    elif extension == ".qif":
        return ImportFormat.QIF
    elif extension in (".xml", ".xhb"):
        return ImportFormat.HOMEBANK
    
    # If extension is not clear, try to detect from content
    try:
        with open(path, "rb") as f:
            content = f.read(1024)  # Read first 1KB
            content_str = content.decode("utf-8", errors="ignore")
            
            # Check for OFX signature
            if content_str.startswith("OFXHEADER:") or b"<OFX>" in content:
                return ImportFormat.OFX
            
            # Check for QIF signature
            if content_str.startswith("!Type:") or content_str.startswith("V"):
                return ImportFormat.QIF
            
            # Check for HomeBank XML
            if b"<homebank-file>" in content or b"<HBFILE>" in content:
                return ImportFormat.HOMEBANK
            
            # Check for CSV
            try:
                dialect = csv.Sniffer().sniff(content_str)
                return ImportFormat.CSV
            except csv.Error:
                pass
            
            # If it looks like CSV (has commas or tabs)
            if b"," in content or b"\t" in content:
                return ImportFormat.CSV
                
    except (IOError, OSError):
        pass
    
    return ImportFormat.UNKNOWN


def detect_format_from_content(content: str) -> ImportFormat:
    """
    Detect format from file content string.
    
    Args:
        content: The file content as a string
        
    Returns:
        The detected ImportFormat
    """
    # Check for OFX
    if content.startswith("OFXHEADER:") or "<OFX>" in content:
        return ImportFormat.OFX
    
    # Check for QIF
    if content.startswith("!Type:") or content.startswith("V"):
        return ImportFormat.QIF
    
    # Check for HomeBank
    if "<homebank-file>" in content or "<HBFILE>" in content:
        return ImportFormat.HOMEBANK
    
    # Check for CSV
    try:
        dialect = csv.Sniffer().sniff(content)
        return ImportFormat.CSV
    except csv.Error:
        pass
    
    # If it looks like CSV
    if "," in content or "\t" in content:
        return ImportFormat.CSV
    
    return ImportFormat.UNKNOWN
