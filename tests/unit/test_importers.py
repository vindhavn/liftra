"""
Unit tests for import/export functionality.
"""

import tempfile
import os
from datetime import datetime

import pytest

from liftra.plugins.importers import (
    CSVImporter, CSVExporter,
    OFXImporter, OFXExporter,
    QIFImporter, QIFExporter,
    HomeBankImporter, HomeBankExporter
)
from liftra.plugins.importers.base import (
    ImportResult, ExportResult, ImportedTransaction, ImportedAccount, FormatType
)


class TestCSVImporter:
    """Test CSV importer functionality."""
    
    def test_csv_importer_creation(self):
        """Test CSV importer can be created."""
        importer = CSVImporter()
        assert importer is not None
        assert importer.format_type == FormatType.CSV
        assert importer.name == "CSV Importer"
    
    def test_csv_import_simple(self):
        """Test importing simple CSV data."""
        csv_content = """date,description,amount,payee
2024-01-01,Test transaction,100.00,Tesco
2024-01-02,Another transaction,-50.00,Amazon
"""
        
        importer = CSVImporter()
        result = importer.import_string(csv_content)
        
        assert result.success
        assert len(result.transactions) == 2
        assert result.transactions[0].description == "Test transaction"
        assert result.transactions[0].amount == "100.00"
        assert result.transactions[0].payee == "Tesco"
        assert result.transactions[1].description == "Another transaction"
        assert result.transactions[1].amount == "-50.00"
    
    def test_csv_import_with_different_delimiter(self):
        """Test importing CSV with semicolon delimiter."""
        csv_content = """date;description;amount;payee
2024-01-01;Test transaction;100.00;Tesco
"""
        
        importer = CSVImporter()
        result = importer.import_string(csv_content, {"delimiter": ";"})
        
        assert result.success
        assert len(result.transactions) == 1
        assert result.transactions[0].description == "Test transaction"
    
    def test_csv_import_with_date_formats(self):
        """Test importing CSV with different date formats."""
        csv_content = """date,description,amount
01/01/2024,Test 1,100.00
2024-01-02,Test 2,50.00
02-01-2024,Test 3,75.00
"""
        
        importer = CSVImporter()
        result = importer.import_string(csv_content)
        
        assert result.success
        assert len(result.transactions) == 3
        # All dates should be converted to ISO format
        assert result.transactions[0].date == "2024-01-01"
        assert result.transactions[1].date == "2024-01-02"
        assert result.transactions[2].date == "2024-01-02"  # 02-01-2024 -> 2024-01-02
    
    def test_csv_detect_format(self):
        """Test CSV format detection."""
        importer = CSVImporter()
        csv_content = "date,description,amount\n2024-01-01,Test,100.00"
        
        assert importer.detect_format(content=csv_content)
        assert importer.can_handle_file("test.csv")
        assert importer.can_handle_file("test.txt")
        assert not importer.can_handle_file("test.ofx")


class TestCSVExporter:
    """Test CSV exporter functionality."""
    
    def test_csv_exporter_creation(self):
        """Test CSV exporter can be created."""
        exporter = CSVExporter()
        assert exporter is not None
        assert exporter.format_type == FormatType.CSV
        assert exporter.name == "CSV Exporter"
    
    def test_csv_export_simple(self):
        """Test exporting simple data to CSV."""
        data = {
            "transactions": [
                {"date": "2024-01-01", "description": "Test", "amount": "100.00", "payee": "Tesco"},
                {"date": "2024-01-02", "description": "Test 2", "amount": "-50.00", "payee": "Amazon"}
            ]
        }
        
        exporter = CSVExporter()
        result = exporter.export_data(data)
        
        assert result.success
        assert result.data is not None
        assert "2024-01-01" in result.data
        assert "Test" in result.data
        assert "100.00" in result.data
    
    def test_csv_export_to_file(self):
        """Test exporting CSV to a file."""
        data = {
            "transactions": [
                {"date": "2024-01-01", "description": "Test", "amount": "100.00"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            exporter = CSVExporter()
            result = exporter.export_to_file(data, temp_path)
            
            assert result.success
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            assert "Test" in content
            assert "100.00" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestOFXImporter:
    """Test OFX importer functionality."""
    
    def test_ofx_importer_creation(self):
        """Test OFX importer can be created."""
        importer = OFXImporter()
        assert importer is not None
        assert importer.format_type == FormatType.OFX
        assert importer.name == "OFX Importer"
    
    def test_ofx_import_simple(self):
        """Test importing simple OFX data."""
        ofx_content = """<?xml version="1.0" encoding="UTF-8"?>
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20240101000000</DTPOSTED>
            <TRNAMT>-100.00</TRNAMT>
            <NAME>Tesco</NAME>
            <MEMO>Test transaction</MEMO>
            <FITID>12345</FITID>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""
        
        importer = OFXImporter()
        result = importer.import_string(ofx_content)
        
        assert result.success
        assert len(result.transactions) == 1
        assert result.transactions[0].description == "Test transaction"
        assert result.transactions[0].amount == "-100.00"
        assert result.transactions[0].payee == "Tesco"
        assert result.transactions[0].date == "2024-01-01"
    
    def test_ofx_detect_format(self):
        """Test OFX format detection."""
        importer = OFXImporter()
        ofx_content = "<?xml version=\"1.0\"?><OFX><BANKMSGSRSV1></BANKMSGSRSV1></OFX>"
        
        assert importer.detect_format(content=ofx_content)
        assert importer.can_handle_file("test.ofx")
        assert importer.can_handle_file("test.qfx")
        assert not importer.can_handle_file("test.csv")


class TestQIFImporter:
    """Test QIF importer functionality."""
    
    def test_qif_importer_creation(self):
        """Test QIF importer can be created."""
        importer = QIFImporter()
        assert importer is not None
        assert importer.format_type == FormatType.QIF
        assert importer.name == "QIF Importer"
    
    def test_qif_import_simple(self):
        """Test importing simple QIF data."""
        qif_content = """!Type:Bank
D01/01/2024
T-100.00
PTesco
MTest transaction
^
"""
        
        importer = QIFImporter()
        result = importer.import_string(qif_content, {"date_format": "%d/%m/%Y"})
        
        assert result.success
        assert len(result.transactions) == 1
        assert result.transactions[0].description == "Test transaction"
        assert result.transactions[0].amount == "-100.00"
        assert result.transactions[0].payee == "Tesco"
        assert result.transactions[0].date == "2024-01-01"
    
    def test_qif_detect_format(self):
        """Test QIF format detection."""
        importer = QIFImporter()
        qif_content = "!Type:Bank\nD01/01/2024\nT100.00\n^"
        
        assert importer.detect_format(content=qif_content)
        assert importer.can_handle_file("test.qif")
        assert not importer.can_handle_file("test.csv")


class TestHomeBankImporter:
    """Test HomeBank importer functionality."""
    
    def test_homebank_importer_creation(self):
        """Test HomeBank importer can be created."""
        importer = HomeBankImporter()
        assert importer is not None
        assert importer.format_type == FormatType.HOMEBANK
        assert importer.name == "HomeBank Importer"
    
    def test_homebank_import_simple(self):
        """Test importing simple HomeBank data."""
        homebank_content = """<?xml version="1.0" encoding="UTF-8"?>
<homebank-file version="1.0">
  <prop>
    <prop key="version" value="1.0"/>
  </prop>
  <account key="1">
    <name>Test Account</name>
    <type>bank</type>
    <currency>GBP</currency>
    <balance>1000.00</balance>
  </account>
  <trans key="1">
    <date>2024-01-01</date>
    <amount>-100.00</amount>
    <currency>GBP</currency>
    <payee>Tesco</payee>
    <memo>Test transaction</memo>
    <category>Food</category>
    <type>debit</type>
  </trans>
</homebank-file>
"""
        
        importer = HomeBankImporter()
        result = importer.import_string(homebank_content)
        
        assert result.success
        assert len(result.accounts) == 1
        assert result.accounts[0].name == "Test Account"
        assert result.accounts[0].currency_code == "GBP"
        assert len(result.transactions) == 1
        assert result.transactions[0].description == "Test transaction"
        assert result.transactions[0].amount == "-100.00"
        assert result.transactions[0].payee == "Tesco"
        assert result.transactions[0].category == "Food"
    
    def test_homebank_detect_format(self):
        """Test HomeBank format detection."""
        importer = HomeBankImporter()
        homebank_content = "<?xml version=\"1.0\"?><homebank-file version=\"1.0\">"
        
        assert importer.detect_format(content=homebank_content)
        assert importer.can_handle_file("test.xhb")
        assert importer.can_handle_file("test.xml")
        assert not importer.can_handle_file("test.csv")


class TestImportExportService:
    """Test the import/export service."""
    
    def test_service_creation(self):
        """Test service can be created."""
        from liftra.services.import_export.service import ImportExportService
        
        service = ImportExportService()
        assert service is not None
        assert len(service.supported_formats) > 0
    
    def test_service_detect_format(self):
        """Test service can detect formats."""
        from liftra.services.import_export.service import ImportExportService
        
        service = ImportExportService()
        
        # Test CSV detection
        csv_content = "date,description,amount\n2024-01-01,Test,100.00"
        assert service.detect_format(content=csv_content) == FormatType.CSV
        
        # Test OFX detection
        ofx_content = "<?xml version=\"1.0\"?><OFX>"
        assert service.detect_format(content=ofx_content) == FormatType.OFX
    
    def test_service_get_format_info(self):
        """Test service can get format information."""
        from liftra.services.import_export.service import ImportExportService
        
        service = ImportExportService()
        
        csv_info = service.get_format_info(FormatType.CSV)
        assert csv_info["can_import"] is True
        assert csv_info["can_export"] is True
        assert FormatType.CSV.value in csv_info["extensions"]
    
    def test_service_get_all_format_info(self):
        """Test service can get all format information."""
        from liftra.services.import_export.service import ImportExportService
        
        service = ImportExportService()
        formats = service.get_all_format_info()
        
        assert len(formats) > 0
        format_types = [f["format_type"] for f in formats]
        assert "csv" in format_types
        assert "ofx" in format_types
        assert "qif" in format_types
        assert "homebank" in format_types
