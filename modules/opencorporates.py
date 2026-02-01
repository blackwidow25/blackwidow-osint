"""
OpenCorporates Data Collector
Retrieves global corporate registry data including officers, filings, and corporate network

Free tier: 50 requests/month
API documentation: https://api.opencorporates.com/documentation
"""

import requests
import time
from typing import Dict, List, Optional


class OpenCorporatesCollector:
    """Collector for OpenCorporates global company database"""
    
    BASE_URL = "https://api.opencorporates.com/v0.4"
    
    # US state jurisdiction codes
    US_JURISDICTIONS = {
        'AL': 'us_al', 'AK': 'us_ak', 'AZ': 'us_az', 'AR': 'us_ar', 'CA': 'us_ca',
        'CO': 'us_co', 'CT': 'us_ct', 'DE': 'us_de', 'FL': 'us_fl', 'GA': 'us_ga',
        'HI': 'us_hi', 'ID': 'us_id', 'IL': 'us_il', 'IN': 'us_in', 'IA': 'us_ia',
        'KS': 'us_ks', 'KY': 'us_ky', 'LA': 'us_la', 'ME': 'us_me', 'MD': 'us_md',
        'MA': 'us_ma', 'MI': 'us_mi', 'MN': 'us_mn', 'MS': 'us_ms', 'MO': 'us_mo',
        'MT': 'us_mt', 'NE': 'us_ne', 'NV': 'us_nv', 'NH': 'us_nh', 'NJ': 'us_nj',
        'NM': 'us_nm', 'NY': 'us_ny', 'NC': 'us_nc', 'ND': 'us_nd', 'OH': 'us_oh',
        'OK': 'us_ok', 'OR': 'us_or', 'PA': 'us_pa', 'RI': 'us_ri', 'SC': 'us_sc',
        'SD': 'us_sd', 'TN': 'us_tn', 'TX': 'us_tx', 'UT': 'us_ut', 'VT': 'us_vt',
        'VA': 'us_va', 'WA': 'us_wa', 'WV': 'us_wv', 'WI': 'us_wi', 'WY': 'us_wy',
        'DC': 'us_dc'
    }
    
    def __init__(self, api_key: str = ''):
        self.api_key = api_key
        self.session = requests.Session()
        self._rate_limit_delay = 1.0  # Be conservative with free tier
        
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make rate-limited request to OpenCorporates API"""
        time.sleep(self._rate_limit_delay)
        
        if params is None:
            params = {}
            
        if self.api_key:
            params['api_token'] = self.api_key
            
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("      OpenCorporates: API key required for this request")
            elif response.status_code == 403:
                print("      OpenCorporates: Rate limit exceeded or insufficient permissions")
            else:
                print(f"      OpenCorporates API Error: {e}")
            return None
        except Exception as e:
            print(f"      OpenCorporates Error: {e}")
            return None
    
    def search_company(self, company_name: str, jurisdiction: str = None) -> Dict:
        """
        Search for a company in OpenCorporates
        
        Args:
            company_name: Name of the company
            jurisdiction: Two-letter state code (e.g., 'DE', 'NY') or country code
            
        Returns:
            Dict with company matches and details
        """
        results = {
            'matches': [],
            'total_count': 0,
            'best_match': None
        }
        
        params = {
            'q': company_name,
            'per_page': 10,
            'order': 'score'
        }
        
        # Add jurisdiction filter if provided
        if jurisdiction:
            if jurisdiction.upper() in self.US_JURISDICTIONS:
                params['jurisdiction_code'] = self.US_JURISDICTIONS[jurisdiction.upper()]
            else:
                params['jurisdiction_code'] = jurisdiction.lower()
        
        data = self._make_request('companies/search', params)
        
        if not data or 'results' not in data:
            return results
            
        results['total_count'] = data['results'].get('total_count', 0)
        
        companies = data['results'].get('companies', [])
        
        for company_wrapper in companies:
            company = company_wrapper.get('company', {})
            
            company_info = {
                'name': company.get('name', ''),
                'company_number': company.get('company_number', ''),
                'jurisdiction': company.get('jurisdiction_code', ''),
                'status': company.get('current_status', ''),
                'incorporation_date': company.get('incorporation_date', ''),
                'dissolution_date': company.get('dissolution_date', ''),
                'company_type': company.get('company_type', ''),
                'registered_address': company.get('registered_address_in_full', ''),
                'agent_name': company.get('agent_name', ''),
                'agent_address': company.get('agent_address', ''),
                'opencorporates_url': company.get('opencorporates_url', ''),
                'registry_url': company.get('registry_url', ''),
                'inactive': company.get('inactive', False),
                'branch_status': company.get('branch_status', ''),
            }
            
            results['matches'].append(company_info)
        
        # Set best match
        if results['matches']:
            results['best_match'] = results['matches'][0]
            
            # Try to get more details on best match
            if results['best_match']['jurisdiction'] and results['best_match']['company_number']:
                details = self._get_company_details(
                    results['best_match']['jurisdiction'],
                    results['best_match']['company_number']
                )
                if details:
                    results['best_match'].update(details)
        
        return results
    
    def _get_company_details(self, jurisdiction: str, company_number: str) -> Optional[Dict]:
        """Get detailed information about a specific company"""
        endpoint = f"companies/{jurisdiction}/{company_number}"
        data = self._make_request(endpoint)
        
        if not data or 'results' not in data:
            return None
            
        company = data['results'].get('company', {})
        
        details = {
            'officers': [],
            'filings': [],
            'industry_codes': [],
            'previous_names': [],
            'alternative_names': [],
            'branch': company.get('branch', ''),
            'home_company': company.get('home_company', {}),
        }
        
        # Parse officers
        officers = company.get('officers', [])
        for officer_wrapper in officers:
            officer = officer_wrapper.get('officer', {})
            details['officers'].append({
                'name': officer.get('name', ''),
                'position': officer.get('position', ''),
                'start_date': officer.get('start_date', ''),
                'end_date': officer.get('end_date', ''),
                'occupation': officer.get('occupation', ''),
                'nationality': officer.get('nationality', ''),
                'address': officer.get('address', ''),
                'current': officer.get('current_status', '') != 'inactive'
            })
        
        # Parse filings
        filings = company.get('filings', [])
        for filing_wrapper in filings:
            filing = filing_wrapper.get('filing', {})
            details['filings'].append({
                'title': filing.get('title', ''),
                'date': filing.get('date', ''),
                'filing_type': filing.get('filing_type', ''),
                'url': filing.get('url', ''),
            })
        
        # Parse industry codes
        industry_codes = company.get('industry_codes', [])
        for ic in industry_codes:
            code = ic.get('industry_code', {})
            details['industry_codes'].append({
                'code': code.get('code', ''),
                'description': code.get('description', ''),
                'code_scheme': code.get('code_scheme_name', ''),
            })
        
        # Parse previous names
        previous_names = company.get('previous_names', [])
        for pn in previous_names:
            name = pn.get('company_name', {})
            details['previous_names'].append({
                'name': name.get('name', ''),
                'start_date': name.get('start_date', ''),
                'end_date': name.get('end_date', ''),
            })
        
        return details
    
    def search_officer(self, officer_name: str, jurisdiction: str = None) -> List[Dict]:
        """
        Search for an officer/director across companies
        
        Args:
            officer_name: Name of the person
            jurisdiction: Optional jurisdiction filter
            
        Returns:
            List of officer positions held
        """
        results = []
        
        params = {
            'q': officer_name,
            'per_page': 30,
            'order': 'score'
        }
        
        if jurisdiction:
            if jurisdiction.upper() in self.US_JURISDICTIONS:
                params['jurisdiction_code'] = self.US_JURISDICTIONS[jurisdiction.upper()]
        
        data = self._make_request('officers/search', params)
        
        if not data or 'results' not in data:
            return results
            
        officers = data['results'].get('officers', [])
        
        for officer_wrapper in officers:
            officer = officer_wrapper.get('officer', {})
            company = officer.get('company', {})
            
            results.append({
                'officer_name': officer.get('name', ''),
                'position': officer.get('position', ''),
                'start_date': officer.get('start_date', ''),
                'end_date': officer.get('end_date', ''),
                'occupation': officer.get('occupation', ''),
                'nationality': officer.get('nationality', ''),
                'company_name': company.get('name', ''),
                'company_jurisdiction': company.get('jurisdiction_code', ''),
                'company_number': company.get('company_number', ''),
                'company_status': company.get('current_status', ''),
                'company_inactive': company.get('inactive', False),
                'opencorporates_url': officer.get('opencorporates_url', ''),
            })
        
        return results
    
    def get_company_network(self, jurisdiction: str, company_number: str) -> Dict:
        """
        Get the corporate network for a company (related companies, subsidiaries, etc.)
        Note: This requires an API key for full results
        
        Args:
            jurisdiction: Jurisdiction code
            company_number: Company registration number
            
        Returns:
            Dict with network relationships
        """
        network = {
            'parent_company': None,
            'subsidiaries': [],
            'related_companies': [],
            'shared_officers': []
        }
        
        # Get company details first
        endpoint = f"companies/{jurisdiction}/{company_number}"
        data = self._make_request(endpoint)
        
        if not data or 'results' not in data:
            return network
            
        company = data['results'].get('company', {})
        
        # Check for parent/branch relationships
        if company.get('branch_status') == 'branch':
            network['parent_company'] = company.get('home_company', {})
        
        # Get officers to find shared connections
        officers = company.get('officers', [])
        for officer_wrapper in officers:
            officer = officer_wrapper.get('officer', {})
            officer_name = officer.get('name', '')
            
            if officer_name:
                # Search for other companies this officer is involved with
                other_positions = self.search_officer(officer_name)
                
                for pos in other_positions:
                    if pos['company_number'] != company_number:
                        network['shared_officers'].append({
                            'officer_name': officer_name,
                            'other_company': pos['company_name'],
                            'position_here': officer.get('position', ''),
                            'position_there': pos['position'],
                        })
        
        return network


# For testing
if __name__ == '__main__':
    collector = OpenCorporatesCollector()
    
    print("Testing OpenCorporates collector...")
    print("\n1. Searching for 'Blackstone Group'...")
    results = collector.search_company("Blackstone Group", jurisdiction="DE")
    
    if results['best_match']:
        print(f"   Best Match: {results['best_match']['name']}")
        print(f"   Status: {results['best_match']['status']}")
        print(f"   Incorporated: {results['best_match']['incorporation_date']}")
        print(f"   Jurisdiction: {results['best_match']['jurisdiction']}")
        
        if results['best_match'].get('officers'):
            print(f"   Officers: {len(results['best_match']['officers'])}")
            for officer in results['best_match']['officers'][:3]:
                print(f"      - {officer['name']}: {officer['position']}")
    
    print("\n2. Searching for officer 'Stephen Schwarzman'...")
    officer_results = collector.search_officer("Stephen Schwarzman")
    print(f"   Found {len(officer_results)} positions")
    for pos in officer_results[:3]:
        print(f"      - {pos['company_name']}: {pos['position']}")
