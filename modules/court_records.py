"""
Court Records Collector
Searches federal and state court records for litigation history

Note: Full PACER access requires an account ($0.10/page)
This module uses free sources and public court data where available
"""

import requests
import time
import re
from typing import Dict, List, Optional
from datetime import datetime


class CourtRecordsCollector:
    """Collector for court records and litigation data"""
    
    # Free court record sources
    COURTLISTENER_URL = "https://www.courtlistener.com/api/rest/v3"
    
    # State court systems that have public APIs/data
    STATE_COURT_URLS = {
        'CA': 'https://appellatecases.courtinfo.ca.gov',
        'NY': 'https://iapps.courts.state.ny.us/nyscef',
        'TX': 'https://search.txcourts.gov',
        'FL': 'https://www.flcourts.org',
        # Add more as we identify accessible APIs
    }
    
    def __init__(self, pacer_credentials: dict = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BlackWidowGlobal OSINT Research'
        })
        self.pacer_credentials = pacer_credentials
        self._rate_limit_delay = 0.5
        
    def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """Make rate-limited request"""
        time.sleep(self._rate_limit_delay)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return {'raw_text': response.text}
        except Exception as e:
            return None
    
    def search_company(self, company_name: str, state: str = None) -> List[Dict]:
        """
        Search for court cases involving a company
        
        Args:
            company_name: Company name to search
            state: Two-letter state code (optional)
            
        Returns:
            List of court cases
        """
        results = []
        
        # Search CourtListener (free federal court opinions)
        courtlistener_results = self._search_courtlistener(company_name)
        results.extend(courtlistener_results)
        
        # Search RECAP archive (free PACER documents)
        recap_results = self._search_recap(company_name)
        results.extend(recap_results)
        
        # If state specified, try state-specific search
        if state and state.upper() in self.STATE_COURT_URLS:
            state_results = self._search_state_court(company_name, state.upper())
            results.extend(state_results)
        
        return results
    
    def search_person(self, person_name: str, state: str = None) -> List[Dict]:
        """
        Search for court cases involving a person
        
        Args:
            person_name: Person's name
            state: Two-letter state code (optional)
            
        Returns:
            List of court cases
        """
        # Same search logic as company
        return self.search_company(person_name, state)
    
    def _search_courtlistener(self, query: str) -> List[Dict]:
        """Search CourtListener for federal court opinions"""
        results = []
        
        # Search opinions
        params = {
            'q': f'"{query}"',
            'order_by': 'dateFiled desc',
            'type': 'o',  # opinions
        }
        
        url = f"{self.COURTLISTENER_URL}/search/"
        data = self._make_request(url, params)
        
        if not data or 'results' not in data:
            return results
        
        for case in data.get('results', [])[:20]:
            results.append({
                'source': 'CourtListener',
                'case_name': case.get('caseName', ''),
                'case_number': case.get('docketNumber', ''),
                'court': case.get('court', ''),
                'date_filed': case.get('dateFiled', ''),
                'date_argued': case.get('dateArgued', ''),
                'status': case.get('status', ''),
                'case_type': 'federal',
                'url': f"https://www.courtlistener.com{case.get('absolute_url', '')}",
                'snippet': case.get('snippet', ''),
                'judge': case.get('judge', ''),
                'citation': case.get('citation', []),
            })
        
        return results
    
    def _search_recap(self, query: str) -> List[Dict]:
        """Search RECAP archive of PACER documents"""
        results = []
        
        # RECAP docket search
        params = {
            'q': f'"{query}"',
            'order_by': 'dateFiled desc',
            'type': 'r',  # RECAP
        }
        
        url = f"{self.COURTLISTENER_URL}/search/"
        data = self._make_request(url, params)
        
        if not data or 'results' not in data:
            return results
        
        for docket in data.get('results', [])[:20]:
            # Determine case type from court or nature of suit
            case_type = 'civil'
            nature_of_suit = docket.get('nature_of_suit', '').lower()
            if 'criminal' in nature_of_suit or docket.get('court', '').endswith('cr'):
                case_type = 'criminal'
            elif 'bankruptcy' in nature_of_suit or 'bk' in docket.get('court', '').lower():
                case_type = 'bankruptcy'
            
            results.append({
                'source': 'RECAP/PACER',
                'case_name': docket.get('caseName', ''),
                'case_number': docket.get('docketNumber', ''),
                'court': docket.get('court', ''),
                'date_filed': docket.get('dateFiled', ''),
                'date_terminated': docket.get('dateTerminated', ''),
                'case_type': case_type,
                'nature_of_suit': docket.get('nature_of_suit', ''),
                'cause': docket.get('cause', ''),
                'jury_demand': docket.get('jury_demand', ''),
                'jurisdiction': docket.get('jurisdiction_type', ''),
                'url': f"https://www.courtlistener.com{docket.get('absolute_url', '')}",
                'assigned_to': docket.get('assigned_to_str', ''),
                'referred_to': docket.get('referred_to_str', ''),
            })
        
        return results
    
    def _search_state_court(self, query: str, state: str) -> List[Dict]:
        """
        Search state court records
        Note: Most state courts don't have public APIs, 
        this is a placeholder for manual integration
        """
        results = []
        
        # For now, return guidance on how to search manually
        state_info = {
            'CA': {
                'name': 'California Courts',
                'url': 'https://www.courts.ca.gov/selfhelp-casesearch.htm',
                'notes': 'Search available for appellate cases. Superior court varies by county.'
            },
            'NY': {
                'name': 'New York State Courts',
                'url': 'https://iapps.courts.state.ny.us/webcivil/ecourtsMain',
                'notes': 'eCourts portal for civil cases. WebCrims for criminal.'
            },
            'TX': {
                'name': 'Texas Courts',
                'url': 'https://search.txcourts.gov/',
                'notes': 'Statewide search available for most courts.'
            },
            'FL': {
                'name': 'Florida Courts',
                'url': 'https://www.flcourts.org/Resources-Services/Court-Records',
                'notes': 'Each circuit has its own clerk of court portal.'
            },
            'DE': {
                'name': 'Delaware Courts',
                'url': 'https://courts.delaware.gov/',
                'notes': 'Chancery Court especially important for corporate litigation.'
            }
        }
        
        if state in state_info:
            results.append({
                'source': f"State Court ({state})",
                'case_name': f"Manual search required for {state_info[state]['name']}",
                'case_number': 'N/A',
                'court': state_info[state]['name'],
                'date_filed': '',
                'case_type': 'info',
                'url': state_info[state]['url'],
                'notes': state_info[state]['notes'],
                'search_query': query,
            })
        
        return results
    
    def get_bankruptcy_cases(self, name: str) -> List[Dict]:
        """
        Search specifically for bankruptcy filings
        
        Args:
            name: Company or person name
            
        Returns:
            List of bankruptcy cases
        """
        results = []
        
        # Search RECAP for bankruptcy
        params = {
            'q': f'"{name}"',
            'type': 'r',
            'court': 'all bankruptcy',
            'order_by': 'dateFiled desc',
        }
        
        url = f"{self.COURTLISTENER_URL}/search/"
        data = self._make_request(url, params)
        
        if not data or 'results' not in data:
            return results
        
        for case in data.get('results', [])[:20]:
            results.append({
                'source': 'RECAP/PACER Bankruptcy',
                'case_name': case.get('caseName', ''),
                'case_number': case.get('docketNumber', ''),
                'court': case.get('court', ''),
                'date_filed': case.get('dateFiled', ''),
                'date_terminated': case.get('dateTerminated', ''),
                'case_type': 'bankruptcy',
                'chapter': self._extract_chapter(case.get('caseName', '')),
                'url': f"https://www.courtlistener.com{case.get('absolute_url', '')}",
            })
        
        return results
    
    def _extract_chapter(self, case_name: str) -> str:
        """Extract bankruptcy chapter from case name"""
        chapters = ['7', '11', '12', '13', '15']
        case_lower = case_name.lower()
        
        for chapter in chapters:
            if f'chapter {chapter}' in case_lower or f'ch. {chapter}' in case_lower:
                return f"Chapter {chapter}"
        
        return 'Unknown'
    
    def analyze_litigation_pattern(self, cases: List[Dict]) -> Dict:
        """
        Analyze litigation history for patterns
        
        Args:
            cases: List of court cases from search
            
        Returns:
            Dict with litigation analysis
        """
        analysis = {
            'total_cases': len(cases),
            'by_type': {},
            'by_year': {},
            'by_court': {},
            'red_flags': [],
            'patterns': []
        }
        
        for case in cases:
            case_type = case.get('case_type', 'unknown')
            court = case.get('court', 'unknown')
            date_str = case.get('date_filed', '')
            
            # Count by type
            if case_type not in analysis['by_type']:
                analysis['by_type'][case_type] = 0
            analysis['by_type'][case_type] += 1
            
            # Count by year
            if date_str:
                try:
                    year = date_str[:4]
                    if year.isdigit():
                        if year not in analysis['by_year']:
                            analysis['by_year'][year] = 0
                        analysis['by_year'][year] += 1
                except:
                    pass
            
            # Count by court
            if court not in analysis['by_court']:
                analysis['by_court'][court] = 0
            analysis['by_court'][court] += 1
        
        # Identify red flags
        if analysis['by_type'].get('criminal', 0) > 0:
            analysis['red_flags'].append({
                'severity': 'HIGH',
                'issue': f"Criminal cases found: {analysis['by_type']['criminal']}"
            })
        
        if analysis['by_type'].get('bankruptcy', 0) > 0:
            analysis['red_flags'].append({
                'severity': 'MEDIUM',
                'issue': f"Bankruptcy filings found: {analysis['by_type']['bankruptcy']}"
            })
        
        if len(cases) > 10:
            analysis['red_flags'].append({
                'severity': 'MEDIUM',
                'issue': f"High litigation volume: {len(cases)} cases"
            })
        
        # Identify patterns
        if len(cases) >= 3:
            # Check for frequent defendant
            defendant_pattern = [c for c in cases if 'v.' in c.get('case_name', '') and 
                               c.get('case_name', '').split('v.')[1].strip().lower().startswith(
                                   cases[0].get('case_name', '').split('v.')[-1].strip().lower()[:10]
                               )]
            if len(defendant_pattern) >= 3:
                analysis['patterns'].append("Frequently named as defendant")
        
        return analysis


# For testing
if __name__ == '__main__':
    collector = CourtRecordsCollector()
    
    print("Testing Court Records collector...")
    print("\nSearching for 'Enron Corporation'...")
    
    results = collector.search_company("Enron Corporation")
    print(f"Found {len(results)} cases")
    
    for case in results[:5]:
        print(f"\n  {case['case_name']}")
        print(f"    Court: {case['court']}")
        print(f"    Filed: {case['date_filed']}")
        print(f"    Type: {case['case_type']}")
        print(f"    Source: {case['source']}")
    
    print("\n\nAnalyzing litigation pattern...")
    analysis = collector.analyze_litigation_pattern(results)
    print(f"  Total cases: {analysis['total_cases']}")
    print(f"  By type: {analysis['by_type']}")
    print(f"  Red flags: {len(analysis['red_flags'])}")
    for flag in analysis['red_flags']:
        print(f"    - [{flag['severity']}] {flag['issue']}")
