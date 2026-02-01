"""
SEC EDGAR Data Collector
Retrieves SEC filings, insider transactions, and beneficial ownership data

Free API - No key required
Documentation: https://www.sec.gov/developer
"""

import requests
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SECEdgarCollector:
    """Collector for SEC EDGAR database"""
    
    BASE_URL = "https://data.sec.gov"
    EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    COMPANY_SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    
    # Required by SEC - must identify yourself
    HEADERS = {
        'User-Agent': 'BlackWidowGlobal OSINT Research contact@blackwidowglobal.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }
    
    # Important filing types for due diligence
    FILING_TYPES = {
        '10-K': 'Annual Report',
        '10-Q': 'Quarterly Report',
        '8-K': 'Current Report (Material Events)',
        'DEF 14A': 'Proxy Statement',
        'S-1': 'IPO Registration',
        'Form 3': 'Initial Beneficial Ownership',
        'Form 4': 'Changes in Beneficial Ownership',
        'Form 5': 'Annual Beneficial Ownership',
        '13F': 'Institutional Holdings',
        '13D': 'Beneficial Ownership >5%',
        '13G': 'Beneficial Ownership >5% (Passive)',
        'SC 13D': 'Schedule 13D Amendment',
        'CORRESP': 'SEC Correspondence',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._rate_limit_delay = 0.1  # SEC requests 10 requests/second max
        
    def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """Make rate-limited request to SEC API"""
        time.sleep(self._rate_limit_delay)
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return {'raw_text': response.text}
        except Exception as e:
            print(f"      SEC API Error: {e}")
            return None
    
    def search_company(self, company_name: str) -> Dict:
        """
        Search for a company and retrieve key filings
        
        Args:
            company_name: Name of the company
            
        Returns:
            Dict with company info and filings
        """
        results = {
            'company_info': {},
            'cik': None,
            'filings': [],
            'insider_transactions': [],
            'beneficial_owners': [],
            'enforcement_actions': [],
            'sec_correspondence': []
        }
        
        # First, find the company's CIK (Central Index Key)
        cik = self._find_company_cik(company_name)
        if not cik:
            return results
        
        results['cik'] = cik
        
        # Get company info and filings
        company_data = self._get_company_data(cik)
        if company_data:
            results['company_info'] = {
                'name': company_data.get('name', ''),
                'cik': cik,
                'sic': company_data.get('sic', ''),
                'sic_description': company_data.get('sicDescription', ''),
                'fiscal_year_end': company_data.get('fiscalYearEnd', ''),
                'state_of_incorporation': company_data.get('stateOfIncorporation', ''),
                'business_address': company_data.get('addresses', {}).get('business', {}),
                'mailing_address': company_data.get('addresses', {}).get('mailing', {}),
                'phone': company_data.get('phone', ''),
                'website': company_data.get('website', ''),
                'former_names': company_data.get('formerNames', []),
                'tickers': company_data.get('tickers', []),
                'exchanges': company_data.get('exchanges', []),
            }
            
            # Get recent filings
            filings = company_data.get('filings', {}).get('recent', {})
            results['filings'] = self._parse_filings(filings)
            
        # Get insider transactions (Forms 3, 4, 5)
        results['insider_transactions'] = self._get_insider_transactions(cik)
        
        # Get beneficial ownership (13D, 13G)
        results['beneficial_owners'] = self._get_beneficial_owners(cik)
        
        return results
    
    def search_person(self, person_name: str, company: str = None) -> Dict:
        """
        Search for a person in SEC filings
        
        Args:
            person_name: Name of the person
            company: Optional company affiliation
            
        Returns:
            Dict with person's SEC activity
        """
        results = {
            'insider_filings': [],
            'beneficial_ownership': [],
            'executive_compensation': [],
            'board_positions': []
        }
        
        # Search for the person in insider filings
        # The SEC full-text search API
        search_url = f"https://efts.sec.gov/LATEST/search-index"
        params = {
            'q': f'"{person_name}"',
            'dateRange': 'custom',
            'startdt': (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d'),
            'enddt': datetime.now().strftime('%Y-%m-%d'),
            'forms': 'Form 3,Form 4,Form 5,DEF 14A',
        }
        
        # Note: Full-text search requires different approach
        # For now, if we have a company, search through their filings
        if company:
            cik = self._find_company_cik(company)
            if cik:
                insider_data = self._get_insider_transactions(cik)
                # Filter for the specific person
                for txn in insider_data:
                    if person_name.lower() in txn.get('reporting_owner', '').lower():
                        results['insider_filings'].append(txn)
        
        return results
    
    def _find_company_cik(self, company_name: str) -> Optional[str]:
        """Find a company's CIK number"""
        # Get the company tickers/CIK mapping
        url = f"{self.BASE_URL}/submissions/CIK"
        
        # Clean the company name for search
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        
        # Try the company search endpoint
        search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'company': company_name,
            'type': '',
            'dateb': '',
            'owner': 'include',
            'count': '10',
            'output': 'atom'
        }
        
        try:
            response = self.session.get(search_url, params=params, timeout=30)
            # Parse the Atom feed to find CIK
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Find CIK in the feed
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                cik_elem = entry.find('.//{http://www.w3.org/2005/Atom}content')
                if cik_elem is not None:
                    cik_match = re.search(r'CIK=(\d+)', cik_elem.text or '')
                    if cik_match:
                        return cik_match.group(1).zfill(10)
                        
            # Alternative: try the company_tickers.json file
            tickers_url = f"{self.BASE_URL}/files/company_tickers.json"
            time.sleep(self._rate_limit_delay)
            response = self.session.get(tickers_url, timeout=30)
            tickers_data = response.json()
            
            for key, data in tickers_data.items():
                if clean_name in data.get('title', '').lower():
                    return str(data.get('cik_str', '')).zfill(10)
                    
        except Exception as e:
            print(f"      Error finding CIK: {e}")
            
        return None
    
    def _get_company_data(self, cik: str) -> Optional[Dict]:
        """Get full company data from SEC"""
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        return self._make_request(url)
    
    def _parse_filings(self, filings_data: Dict, limit: int = 50) -> List[Dict]:
        """Parse filings into structured format"""
        parsed = []
        
        if not filings_data:
            return parsed
            
        forms = filings_data.get('form', [])
        dates = filings_data.get('filingDate', [])
        accessions = filings_data.get('accessionNumber', [])
        descriptions = filings_data.get('primaryDocDescription', [])
        
        for i in range(min(len(forms), limit)):
            filing = {
                'form_type': forms[i] if i < len(forms) else '',
                'filing_date': dates[i] if i < len(dates) else '',
                'accession_number': accessions[i] if i < len(accessions) else '',
                'description': descriptions[i] if i < len(descriptions) else '',
                'form_description': self.FILING_TYPES.get(forms[i], 'Other') if i < len(forms) else ''
            }
            
            # Add link to filing
            if filing['accession_number']:
                clean_accession = filing['accession_number'].replace('-', '')
                filing['url'] = f"https://www.sec.gov/Archives/edgar/data/{clean_accession}/{filing['accession_number']}-index.htm"
            
            parsed.append(filing)
            
        return parsed
    
    def _get_insider_transactions(self, cik: str) -> List[Dict]:
        """Get Form 3, 4, 5 insider transaction data"""
        transactions = []
        
        company_data = self._get_company_data(cik)
        if not company_data:
            return transactions
            
        filings = company_data.get('filings', {}).get('recent', {})
        forms = filings.get('form', [])
        dates = filings.get('filingDate', [])
        accessions = filings.get('accessionNumber', [])
        
        for i, form in enumerate(forms):
            if form in ['3', '4', '5']:
                transactions.append({
                    'form_type': f'Form {form}',
                    'filing_date': dates[i] if i < len(dates) else '',
                    'accession_number': accessions[i] if i < len(accessions) else '',
                    'reporting_owner': '',  # Would need to parse the actual filing
                    'transaction_type': 'Initial' if form == '3' else 'Change' if form == '4' else 'Annual'
                })
                
        return transactions[:20]  # Limit to recent 20
    
    def _get_beneficial_owners(self, cik: str) -> List[Dict]:
        """Get 13D and 13G beneficial ownership filings"""
        owners = []
        
        company_data = self._get_company_data(cik)
        if not company_data:
            return owners
            
        filings = company_data.get('filings', {}).get('recent', {})
        forms = filings.get('form', [])
        dates = filings.get('filingDate', [])
        accessions = filings.get('accessionNumber', [])
        
        for i, form in enumerate(forms):
            if '13D' in form or '13G' in form:
                owners.append({
                    'form_type': form,
                    'filing_date': dates[i] if i < len(dates) else '',
                    'accession_number': accessions[i] if i < len(accessions) else '',
                    'filer': '',  # Would need to parse the actual filing
                    'ownership_type': 'Active' if '13D' in form else 'Passive'
                })
                
        return owners[:20]
    
    def get_filing_document(self, accession_number: str, cik: str) -> Optional[str]:
        """Retrieve the actual text of a filing"""
        clean_accession = accession_number.replace('-', '')
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{clean_accession}/{accession_number}.txt"
        
        try:
            time.sleep(self._rate_limit_delay)
            response = self.session.get(url, timeout=60)
            return response.text
        except Exception as e:
            print(f"      Error retrieving filing: {e}")
            return None


# For testing
if __name__ == '__main__':
    collector = SECEdgarCollector()
    
    # Test with a well-known company
    print("Testing SEC EDGAR collector with Apple Inc...")
    results = collector.search_company("Apple Inc")
    
    print(f"\nCompany Info:")
    print(f"  Name: {results['company_info'].get('name', 'N/A')}")
    print(f"  CIK: {results['cik']}")
    print(f"  SIC: {results['company_info'].get('sic_description', 'N/A')}")
    
    print(f"\nRecent Filings: {len(results['filings'])}")
    for filing in results['filings'][:5]:
        print(f"  - {filing['filing_date']}: {filing['form_type']} - {filing['form_description']}")
