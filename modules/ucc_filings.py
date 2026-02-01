"""
UCC Filings Collector
Searches for Uniform Commercial Code filings (liens, secured creditors)

UCC filings reveal:
- Secured creditors (who has claims on company assets)
- Collateral pledged
- Financial obligations not visible on balance sheets
- Potential financial distress signals
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime


class UCCFilingsCollector:
    """Collector for UCC filing data"""
    
    # State Secretary of State UCC search URLs
    STATE_UCC_URLS = {
        'AL': 'https://www.sos.alabama.gov/business-entities/ucc-search',
        'AK': 'https://www.commerce.alaska.gov/cbp/main/search/ucc',
        'AZ': 'https://ecorp.azcc.gov/PublicSearches/UCCSearch',
        'CA': 'https://bizfileonline.sos.ca.gov/search/ucc',
        'CO': 'https://www.sos.state.co.us/biz/UCCSearchCriteria.do',
        'DE': 'https://icis.corp.delaware.gov/UCCSearch/',
        'FL': 'https://www.sunbiz.org/UCC_Search.html',
        'GA': 'https://ecorp.sos.ga.gov/UCCSearch',
        'IL': 'https://www.ilsos.gov/uccsearch/',
        'NY': 'https://appext20.dos.ny.gov/pls/ucc_public/web_search.main_frame',
        'TX': 'https://direct.sos.state.tx.us/help/help-ucc.asp',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self._rate_limit_delay = 0.5
        
    def search_debtor(self, debtor_name: str, state: str = None) -> List[Dict]:
        """
        Search for UCC filings by debtor name
        
        Args:
            debtor_name: Name of the debtor (company or person)
            state: Two-letter state code
            
        Returns:
            List of UCC filing records with search guidance
        """
        results = []
        
        if state and state.upper() in self.STATE_UCC_URLS:
            results.append({
                'state': state.upper(),
                'search_url': self.STATE_UCC_URLS[state.upper()],
                'debtor_name': debtor_name,
                'status': 'manual_search_required',
                'what_to_look_for': [
                    'Active UCC-1 filings (original financing statements)',
                    'UCC-3 amendments and continuations',
                    'Secured party names (creditors)',
                    'Collateral descriptions',
                    'Filing dates',
                    'Termination status'
                ]
            })
        else:
            # Provide guidance for common states
            results.append({
                'type': 'guidance',
                'message': 'UCC filings are maintained by each state. Specify state for targeted search.',
                'common_states': ['DE', 'NY', 'CA', 'TX', 'FL'],
                'recommendation': 'Start with state of incorporation'
            })
        
        return results
    
    def analyze_ucc_findings(self, filings: List[Dict]) -> Dict:
        """Analyze UCC filings for due diligence insights"""
        return {
            'total_filings': 0,
            'recommendations': [
                'Search state of incorporation first',
                'Also search states where company operates',
                'Look for blanket liens vs. specific collateral',
                'Check for recent filings indicating new debt'
            ],
            'red_flags_to_watch': [
                {'indicator': 'Multiple secured parties', 'severity': 'MEDIUM'},
                {'indicator': 'Blanket lien on all assets', 'severity': 'MEDIUM'},
                {'indicator': 'Recent surge in filings', 'severity': 'HIGH'},
                {'indicator': 'Tax liens', 'severity': 'HIGH'}
            ]
        }
