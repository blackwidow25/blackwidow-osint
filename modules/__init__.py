"""
Black Widow Global OSINT Tool - Modules
"""

from .sec_edgar import SECEdgarCollector
from .opencorporates import OpenCorporatesCollector
from .fec_donations import FECDonationsCollector
from .court_records import CourtRecordsCollector
from .ucc_filings import UCCFilingsCollector
from .news_search import NewsSearchCollector
from .entity_resolver import EntityResolver
from .report_generator import ReportGenerator

__all__ = [
    'SECEdgarCollector',
    'OpenCorporatesCollector', 
    'FECDonationsCollector',
    'CourtRecordsCollector',
    'UCCFilingsCollector',
    'NewsSearchCollector',
    'EntityResolver',
    'ReportGenerator'
]
