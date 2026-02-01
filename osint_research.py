#!/usr/bin/env python3
"""
Black Widow Global OSINT Research Tool
Corporate Intelligence & Due Diligence Automation

This tool performs comprehensive open-source intelligence gathering
on companies, LLCs, and individuals for corporate due diligence.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from modules.sec_edgar import SECEdgarCollector
from modules.opencorporates import OpenCorporatesCollector
from modules.fec_donations import FECDonationsCollector
from modules.court_records import CourtRecordsCollector
from modules.ucc_filings import UCCFilingsCollector
from modules.news_search import NewsSearchCollector
from modules.entity_resolver import EntityResolver
from modules.report_generator import ReportGenerator


class OSINTResearcher:
    """Main OSINT research orchestrator"""
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.collectors = self._initialize_collectors()
        self.resolver = EntityResolver()
        self.report_gen = ReportGenerator()
        
    def _load_config(self, config_path):
        """Load configuration file"""
        default_config = {
            'output_dir': 'output',
            'report_format': 'both',  # 'pdf', 'json', or 'both'
            'api_keys': {
                'opencorporates': os.environ.get('OPENCORPORATES_API_KEY', ''),
                'pacer': os.environ.get('PACER_API_KEY', ''),
            },
            'modules': {
                'sec_edgar': True,
                'opencorporates': True,
                'fec_donations': True,
                'court_records': True,
                'ucc_filings': True,
                'news_search': True,
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    def _initialize_collectors(self):
        """Initialize all data collectors"""
        collectors = {}
        
        if self.config['modules'].get('sec_edgar', True):
            collectors['sec_edgar'] = SECEdgarCollector()
            
        if self.config['modules'].get('opencorporates', True):
            collectors['opencorporates'] = OpenCorporatesCollector(
                api_key=self.config['api_keys'].get('opencorporates', '')
            )
            
        if self.config['modules'].get('fec_donations', True):
            collectors['fec_donations'] = FECDonationsCollector()
            
        if self.config['modules'].get('court_records', True):
            collectors['court_records'] = CourtRecordsCollector()
            
        if self.config['modules'].get('ucc_filings', True):
            collectors['ucc_filings'] = UCCFilingsCollector()
            
        if self.config['modules'].get('news_search', True):
            collectors['news_search'] = NewsSearchCollector()
            
        return collectors
    
    def research_company(self, company_name, state=None, additional_params=None):
        """
        Conduct comprehensive research on a company
        
        Args:
            company_name: Name of the company or LLC
            state: State of incorporation (optional, helps narrow search)
            additional_params: Dict of additional search parameters
            
        Returns:
            Dict containing all research findings
        """
        print(f"\n{'='*60}")
        print(f"BLACK WIDOW GLOBAL - OSINT RESEARCH")
        print(f"Target: {company_name}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        findings = {
            'target': company_name,
            'target_type': 'company',
            'research_date': datetime.now().isoformat(),
            'state': state,
            'data_sources': {},
            'related_entities': [],
            'red_flags': [],
            'summary': {}
        }
        
        # Run each collector
        for name, collector in self.collectors.items():
            print(f"[*] Running {name} collector...")
            try:
                if name == 'sec_edgar':
                    data = collector.search_company(company_name)
                elif name == 'opencorporates':
                    data = collector.search_company(company_name, jurisdiction=state)
                elif name == 'fec_donations':
                    data = collector.search_by_employer(company_name)
                elif name == 'court_records':
                    data = collector.search_company(company_name, state=state)
                elif name == 'ucc_filings':
                    data = collector.search_debtor(company_name, state=state)
                elif name == 'news_search':
                    data = collector.search(company_name)
                else:
                    data = {}
                    
                findings['data_sources'][name] = data
                print(f"    [+] {name}: Found {len(data) if isinstance(data, list) else 'N/A'} records")
                
            except Exception as e:
                print(f"    [-] {name}: Error - {str(e)}")
                findings['data_sources'][name] = {'error': str(e)}
        
        # Resolve entities and find connections
        print("\n[*] Analyzing relationships and connections...")
        findings['related_entities'] = self.resolver.find_connections(findings)
        
        # Identify red flags
        print("[*] Scanning for red flags...")
        findings['red_flags'] = self._identify_red_flags(findings)
        
        # Generate summary
        findings['summary'] = self._generate_summary(findings)
        
        return findings
    
    def research_person(self, person_name, company=None, state=None):
        """
        Conduct comprehensive research on an individual
        
        Args:
            person_name: Full name of the person
            company: Known company affiliation (optional)
            state: State of residence (optional)
            
        Returns:
            Dict containing all research findings
        """
        print(f"\n{'='*60}")
        print(f"BLACK WIDOW GLOBAL - OSINT RESEARCH")
        print(f"Target: {person_name}")
        print(f"Type: Individual")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        findings = {
            'target': person_name,
            'target_type': 'person',
            'research_date': datetime.now().isoformat(),
            'known_company': company,
            'state': state,
            'data_sources': {},
            'related_entities': [],
            'red_flags': [],
            'summary': {}
        }
        
        # Run collectors for person research
        for name, collector in self.collectors.items():
            print(f"[*] Running {name} collector...")
            try:
                if name == 'sec_edgar':
                    data = collector.search_person(person_name, company=company)
                elif name == 'opencorporates':
                    data = collector.search_officer(person_name)
                elif name == 'fec_donations':
                    data = collector.search_donor(person_name, state=state)
                elif name == 'court_records':
                    data = collector.search_person(person_name, state=state)
                elif name == 'ucc_filings':
                    # Skip UCC for person searches unless they're a sole proprietor
                    data = {}
                elif name == 'news_search':
                    data = collector.search(person_name)
                else:
                    data = {}
                    
                findings['data_sources'][name] = data
                print(f"    [+] {name}: Found {len(data) if isinstance(data, list) else 'N/A'} records")
                
            except Exception as e:
                print(f"    [-] {name}: Error - {str(e)}")
                findings['data_sources'][name] = {'error': str(e)}
        
        # Resolve entities and find connections
        print("\n[*] Analyzing relationships and connections...")
        findings['related_entities'] = self.resolver.find_connections(findings)
        
        # Identify red flags
        print("[*] Scanning for red flags...")
        findings['red_flags'] = self._identify_red_flags(findings)
        
        # Generate summary
        findings['summary'] = self._generate_summary(findings)
        
        return findings
    
    def _identify_red_flags(self, findings):
        """Analyze findings for potential red flags"""
        red_flags = []
        
        # Check for litigation
        court_data = findings['data_sources'].get('court_records', {})
        if isinstance(court_data, list) and len(court_data) > 0:
            criminal_cases = [c for c in court_data if c.get('case_type') == 'criminal']
            if criminal_cases:
                red_flags.append({
                    'severity': 'HIGH',
                    'category': 'Legal',
                    'description': f'Found {len(criminal_cases)} criminal case(s)',
                    'details': criminal_cases
                })
            
            civil_cases = [c for c in court_data if c.get('case_type') == 'civil']
            if len(civil_cases) > 3:
                red_flags.append({
                    'severity': 'MEDIUM',
                    'category': 'Legal',
                    'description': f'Multiple civil lawsuits ({len(civil_cases)} cases)',
                    'details': civil_cases
                })
        
        # Check for UCC liens
        ucc_data = findings['data_sources'].get('ucc_filings', {})
        if isinstance(ucc_data, list) and len(ucc_data) > 0:
            active_liens = [u for u in ucc_data if u.get('status') == 'active']
            if active_liens:
                red_flags.append({
                    'severity': 'MEDIUM',
                    'category': 'Financial',
                    'description': f'Active UCC liens ({len(active_liens)} filings)',
                    'details': active_liens
                })
        
        # Check SEC for enforcement actions
        sec_data = findings['data_sources'].get('sec_edgar', {})
        if isinstance(sec_data, dict):
            enforcement = sec_data.get('enforcement_actions', [])
            if enforcement:
                red_flags.append({
                    'severity': 'HIGH',
                    'category': 'Regulatory',
                    'description': 'SEC enforcement action(s) found',
                    'details': enforcement
                })
        
        # Check for sanctions/watchlists (placeholder for OFAC integration)
        # This would connect to OFAC SDN list
        
        return red_flags
    
    def _generate_summary(self, findings):
        """Generate executive summary of findings"""
        summary = {
            'target': findings['target'],
            'target_type': findings['target_type'],
            'research_date': findings['research_date'],
            'total_data_sources_queried': len(findings['data_sources']),
            'successful_queries': sum(1 for v in findings['data_sources'].values() 
                                     if not isinstance(v, dict) or 'error' not in v),
            'related_entities_found': len(findings['related_entities']),
            'red_flags_count': len(findings['red_flags']),
            'red_flags_by_severity': {
                'HIGH': len([f for f in findings['red_flags'] if f['severity'] == 'HIGH']),
                'MEDIUM': len([f for f in findings['red_flags'] if f['severity'] == 'MEDIUM']),
                'LOW': len([f for f in findings['red_flags'] if f['severity'] == 'LOW']),
            },
            'risk_assessment': self._calculate_risk_score(findings)
        }
        return summary
    
    def _calculate_risk_score(self, findings):
        """Calculate overall risk score based on findings"""
        score = 0
        
        for flag in findings['red_flags']:
            if flag['severity'] == 'HIGH':
                score += 30
            elif flag['severity'] == 'MEDIUM':
                score += 15
            elif flag['severity'] == 'LOW':
                score += 5
        
        # Cap at 100
        score = min(score, 100)
        
        if score >= 70:
            return {'score': score, 'level': 'HIGH RISK', 'recommendation': 'Enhanced due diligence required'}
        elif score >= 40:
            return {'score': score, 'level': 'MEDIUM RISK', 'recommendation': 'Additional investigation recommended'}
        elif score >= 20:
            return {'score': score, 'level': 'LOW RISK', 'recommendation': 'Standard due diligence sufficient'}
        else:
            return {'score': score, 'level': 'MINIMAL RISK', 'recommendation': 'No significant concerns identified'}
    
    def generate_report(self, findings, output_path=None):
        """Generate formatted report from findings"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = findings['target'].replace(' ', '_').replace(',', '')[:30]
            output_path = Path(self.config['output_dir']) / f"report_{safe_name}_{timestamp}"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate JSON report
        json_path = str(output_path) + '.json'
        with open(json_path, 'w') as f:
            json.dump(findings, f, indent=2, default=str)
        print(f"\n[+] JSON report saved: {json_path}")
        
        # Generate formatted report (text for now, can add PDF later)
        report_path = str(output_path) + '_report.txt'
        self.report_gen.generate_text_report(findings, report_path)
        print(f"[+] Text report saved: {report_path}")
        
        return json_path, report_path


def main():
    parser = argparse.ArgumentParser(
        description='Black Widow Global OSINT Research Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Research a company:
    python osint_research.py company "Acme Corporation" --state DE
    
  Research a person:
    python osint_research.py person "John Smith" --company "Acme Corp" --state NY
    
  Use custom config:
    python osint_research.py company "Target LLC" --config config.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Research type')
    
    # Company research subcommand
    company_parser = subparsers.add_parser('company', help='Research a company or LLC')
    company_parser.add_argument('name', help='Company or LLC name')
    company_parser.add_argument('--state', '-s', help='State of incorporation')
    company_parser.add_argument('--config', '-c', help='Path to config file')
    company_parser.add_argument('--output', '-o', help='Output path for reports')
    
    # Person research subcommand
    person_parser = subparsers.add_parser('person', help='Research an individual')
    person_parser.add_argument('name', help='Person\'s full name')
    person_parser.add_argument('--company', help='Known company affiliation')
    person_parser.add_argument('--state', '-s', help='State of residence')
    person_parser.add_argument('--config', '-c', help='Path to config file')
    person_parser.add_argument('--output', '-o', help='Output path for reports')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize researcher
    config_path = getattr(args, 'config', None)
    researcher = OSINTResearcher(config_path=config_path)
    
    # Run research
    if args.command == 'company':
        findings = researcher.research_company(args.name, state=args.state)
    elif args.command == 'person':
        findings = researcher.research_person(
            args.name, 
            company=getattr(args, 'company', None),
            state=args.state
        )
    
    # Generate reports
    output_path = getattr(args, 'output', None)
    researcher.generate_report(findings, output_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print("RESEARCH COMPLETE - SUMMARY")
    print(f"{'='*60}")
    print(f"Target: {findings['summary']['target']}")
    print(f"Risk Level: {findings['summary']['risk_assessment']['level']}")
    print(f"Risk Score: {findings['summary']['risk_assessment']['score']}/100")
    print(f"Red Flags: {findings['summary']['red_flags_count']}")
    print(f"Recommendation: {findings['summary']['risk_assessment']['recommendation']}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
