"""
FEC (Federal Election Commission) Data Collector
Retrieves political campaign contribution data

Free API - Key recommended for higher rate limits
Documentation: https://api.open.fec.gov/developers/
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class FECDonationsCollector:
    """Collector for FEC campaign contribution data"""
    
    BASE_URL = "https://api.open.fec.gov/v1"
    
    # Default API key (demo key - replace with your own for production)
    # Get your own at: https://api.data.gov/signup/
    DEFAULT_API_KEY = "qMMQ7NuG1BX8rxNsylmvLIKN19ePlem85wa1G0xa"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.session = requests.Session()
        self._rate_limit_delay = 0.5  # Be conservative
        
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make rate-limited request to FEC API"""
        time.sleep(self._rate_limit_delay)
        
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        params['per_page'] = params.get('per_page', 100)
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print("      FEC API: Rate limit exceeded. Wait and retry.")
            else:
                print(f"      FEC API Error: {e}")
            return None
        except Exception as e:
            print(f"      FEC Error: {e}")
            return None
    
    def search_donor(self, name: str, state: str = None, min_amount: float = None) -> List[Dict]:
        """
        Search for individual campaign contributions by donor name
        
        Args:
            name: Donor's name
            state: Two-letter state code (optional)
            min_amount: Minimum contribution amount (optional)
            
        Returns:
            List of contributions with details
        """
        results = []
        
        # Search for individual contributions
        params = {
            'contributor_name': name,
            'sort': '-contribution_receipt_date',
            'sort_hide_null': False,
            'sort_null_only': False,
        }
        
        if state:
            params['contributor_state'] = state.upper()
            
        if min_amount:
            params['min_amount'] = min_amount
        
        data = self._make_request('schedules/schedule_a/', params)
        
        if not data or 'results' not in data:
            return results
        
        for contribution in data.get('results', []):
            results.append({
                'contributor_name': contribution.get('contributor_name', ''),
                'contributor_city': contribution.get('contributor_city', ''),
                'contributor_state': contribution.get('contributor_state', ''),
                'contributor_zip': contribution.get('contributor_zip', ''),
                'contributor_employer': contribution.get('contributor_employer', ''),
                'contributor_occupation': contribution.get('contributor_occupation', ''),
                'contribution_date': contribution.get('contribution_receipt_date', ''),
                'contribution_amount': contribution.get('contribution_receipt_amount', 0),
                'recipient_committee_name': contribution.get('committee', {}).get('name', ''),
                'recipient_committee_id': contribution.get('committee_id', ''),
                'recipient_party': contribution.get('committee', {}).get('party', ''),
                'candidate_name': contribution.get('candidate_name', ''),
                'candidate_party': contribution.get('candidate', {}).get('party', '') if contribution.get('candidate') else '',
                'election_cycle': contribution.get('two_year_transaction_period', ''),
                'memo_text': contribution.get('memo_text', ''),
                'receipt_type': contribution.get('receipt_type_description', ''),
            })
        
        return results
    
    def search_by_employer(self, employer_name: str, min_amount: float = None) -> Dict:
        """
        Search for contributions by employer (useful for company research)
        
        Args:
            employer_name: Name of the employer/company
            min_amount: Minimum contribution amount (optional)
            
        Returns:
            Dict with contribution summary and top donors
        """
        results = {
            'total_contributions': 0,
            'total_amount': 0,
            'unique_donors': set(),
            'contributions_by_party': {},
            'top_donors': [],
            'recent_contributions': [],
            'top_recipients': {}
        }
        
        params = {
            'contributor_employer': employer_name,
            'sort': '-contribution_receipt_date',
            'per_page': 100,
        }
        
        if min_amount:
            params['min_amount'] = min_amount
        
        data = self._make_request('schedules/schedule_a/', params)
        
        if not data or 'results' not in data:
            return results
        
        donor_totals = {}
        recipient_totals = {}
        
        for contribution in data.get('results', []):
            amount = contribution.get('contribution_receipt_amount', 0) or 0
            donor_name = contribution.get('contributor_name', 'Unknown')
            party = contribution.get('committee', {}).get('party', 'Unknown')
            recipient = contribution.get('committee', {}).get('name', 'Unknown')
            
            results['total_contributions'] += 1
            results['total_amount'] += amount
            results['unique_donors'].add(donor_name)
            
            # Track by party
            if party not in results['contributions_by_party']:
                results['contributions_by_party'][party] = {'count': 0, 'amount': 0}
            results['contributions_by_party'][party]['count'] += 1
            results['contributions_by_party'][party]['amount'] += amount
            
            # Track top donors
            if donor_name not in donor_totals:
                donor_totals[donor_name] = {
                    'name': donor_name,
                    'total_amount': 0,
                    'contribution_count': 0,
                    'occupation': contribution.get('contributor_occupation', ''),
                    'city': contribution.get('contributor_city', ''),
                    'state': contribution.get('contributor_state', ''),
                }
            donor_totals[donor_name]['total_amount'] += amount
            donor_totals[donor_name]['contribution_count'] += 1
            
            # Track top recipients
            if recipient not in recipient_totals:
                recipient_totals[recipient] = {'name': recipient, 'party': party, 'total_amount': 0}
            recipient_totals[recipient]['total_amount'] += amount
        
        # Convert set to count
        results['unique_donors'] = len(results['unique_donors'])
        
        # Get top donors
        results['top_donors'] = sorted(
            donor_totals.values(), 
            key=lambda x: x['total_amount'], 
            reverse=True
        )[:10]
        
        # Get top recipients
        results['top_recipients'] = sorted(
            recipient_totals.values(),
            key=lambda x: x['total_amount'],
            reverse=True
        )[:10]
        
        # Get recent contributions
        results['recent_contributions'] = [
            {
                'donor': c.get('contributor_name', ''),
                'amount': c.get('contribution_receipt_amount', 0),
                'date': c.get('contribution_receipt_date', ''),
                'recipient': c.get('committee', {}).get('name', ''),
                'party': c.get('committee', {}).get('party', ''),
            }
            for c in data.get('results', [])[:10]
        ]
        
        return results
    
    def get_committee_details(self, committee_id: str) -> Optional[Dict]:
        """
        Get details about a specific committee (PAC, campaign, etc.)
        
        Args:
            committee_id: FEC committee ID
            
        Returns:
            Dict with committee details
        """
        data = self._make_request(f'committee/{committee_id}/')
        
        if not data or 'results' not in data or not data['results']:
            return None
        
        committee = data['results'][0]
        
        return {
            'name': committee.get('name', ''),
            'committee_id': committee.get('committee_id', ''),
            'committee_type': committee.get('committee_type_full', ''),
            'designation': committee.get('designation_full', ''),
            'party': committee.get('party_full', ''),
            'state': committee.get('state', ''),
            'treasurer_name': committee.get('treasurer_name', ''),
            'street_1': committee.get('street_1', ''),
            'street_2': committee.get('street_2', ''),
            'city': committee.get('city', ''),
            'zip': committee.get('zip', ''),
            'filing_frequency': committee.get('filing_frequency', ''),
            'candidate_ids': committee.get('candidate_ids', []),
            'cycles': committee.get('cycles', []),
            'first_file_date': committee.get('first_file_date', ''),
            'last_file_date': committee.get('last_file_date', ''),
        }
    
    def get_candidate_contributions(self, candidate_name: str) -> Dict:
        """
        Get contributions to a specific candidate
        
        Args:
            candidate_name: Name of the candidate
            
        Returns:
            Dict with contribution summary
        """
        results = {
            'candidate_info': None,
            'total_raised': 0,
            'contribution_count': 0,
            'top_contributors': [],
            'contributions_by_employer': {}
        }
        
        # First, find the candidate
        params = {'q': candidate_name, 'per_page': 5}
        candidate_data = self._make_request('candidates/search/', params)
        
        if not candidate_data or not candidate_data.get('results'):
            return results
        
        candidate = candidate_data['results'][0]
        results['candidate_info'] = {
            'name': candidate.get('name', ''),
            'candidate_id': candidate.get('candidate_id', ''),
            'party': candidate.get('party_full', ''),
            'office': candidate.get('office_full', ''),
            'state': candidate.get('state', ''),
            'district': candidate.get('district', ''),
            'election_years': candidate.get('election_years', []),
        }
        
        # Get their committee IDs and fetch contributions
        committee_ids = candidate.get('principal_committees', [])
        
        for committee in committee_ids:
            committee_id = committee.get('committee_id')
            if committee_id:
                params = {
                    'committee_id': committee_id,
                    'sort': '-contribution_receipt_amount',
                    'per_page': 100,
                }
                contrib_data = self._make_request('schedules/schedule_a/', params)
                
                if contrib_data and 'results' in contrib_data:
                    for contribution in contrib_data['results']:
                        amount = contribution.get('contribution_receipt_amount', 0) or 0
                        employer = contribution.get('contributor_employer', 'Not Reported')
                        
                        results['total_raised'] += amount
                        results['contribution_count'] += 1
                        
                        if employer not in results['contributions_by_employer']:
                            results['contributions_by_employer'][employer] = 0
                        results['contributions_by_employer'][employer] += amount
        
        # Sort employers by total contribution
        results['contributions_by_employer'] = dict(
            sorted(
                results['contributions_by_employer'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
        )
        
        return results


# For testing
if __name__ == '__main__':
    collector = FECDonationsCollector()
    
    print("Testing FEC Donations collector...")
    
    print("\n1. Searching for donations by employer 'Goldman Sachs'...")
    results = collector.search_by_employer("Goldman Sachs")
    print(f"   Total contributions: {results['total_contributions']}")
    print(f"   Total amount: ${results['total_amount']:,.2f}")
    print(f"   Unique donors: {results['unique_donors']}")
    
    print("\n   By Party:")
    for party, data in results['contributions_by_party'].items():
        print(f"      {party}: ${data['amount']:,.2f} ({data['count']} contributions)")
    
    print("\n   Top Recipients:")
    for recipient in results['top_recipients'][:5]:
        print(f"      {recipient['name']} ({recipient['party']}): ${recipient['total_amount']:,.2f}")
