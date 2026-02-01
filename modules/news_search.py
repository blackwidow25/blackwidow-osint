"""
News and Media Search Collector
Comprehensive media intelligence beyond basic Google search

Covers:
- Global news sources
- Local/regional publications
- Industry-specific media
- Press releases and corporate communications
- Adverse media screening
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re


class NewsSearchCollector:
    """Collector for news and media intelligence"""
    
    # Free news APIs and sources
    GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"
    NEWSAPI_URL = "https://newsapi.org/v2"  # Free tier: 100 requests/day
    
    # Adverse media keywords for screening
    ADVERSE_KEYWORDS = [
        'fraud', 'embezzlement', 'indicted', 'arrested', 'convicted',
        'lawsuit', 'scandal', 'investigation', 'SEC', 'DOJ',
        'bribery', 'corruption', 'money laundering', 'sanctions',
        'bankruptcy', 'default', 'violation', 'penalty', 'fine',
        'whistleblower', 'misconduct', 'harassment', 'discrimination',
        'insider trading', 'securities fraud', 'tax evasion',
        'OFAC', 'terrorism', 'criminal', 'felony', 'allegations'
    ]
    
    # Positive media keywords
    POSITIVE_KEYWORDS = [
        'award', 'recognition', 'growth', 'expansion', 'partnership',
        'innovation', 'leadership', 'philanthropy', 'sustainability',
        'acquisition', 'funding', 'IPO', 'profitable', 'success'
    ]
    
    def __init__(self, newsapi_key: str = None):
        self.newsapi_key = newsapi_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BlackWidowGlobal OSINT Research'
        })
        self._rate_limit_delay = 0.5
        
    def search(self, query: str, days_back: int = 365) -> Dict:
        """
        Comprehensive news search for a subject
        
        Args:
            query: Company or person name
            days_back: How far back to search (default 1 year)
            
        Returns:
            Dict with categorized news results
        """
        results = {
            'total_articles': 0,
            'articles': [],
            'adverse_media': [],
            'positive_media': [],
            'by_source': {},
            'by_month': {},
            'sentiment_summary': {
                'adverse': 0,
                'positive': 0,
                'neutral': 0
            },
            'key_topics': [],
            'timeline': []
        }
        
        # Search GDELT (free, comprehensive global news)
        gdelt_results = self._search_gdelt(query, days_back)
        results['articles'].extend(gdelt_results)
        
        # Search NewsAPI if key available
        if self.newsapi_key:
            newsapi_results = self._search_newsapi(query, days_back)
            results['articles'].extend(newsapi_results)
        
        # Process and categorize results
        results = self._process_results(results, query)
        
        return results
    
    def _search_gdelt(self, query: str, days_back: int) -> List[Dict]:
        """Search GDELT global news database"""
        articles = []
        
        # GDELT DOC 2.0 API
        params = {
            'query': f'"{query}"',
            'mode': 'artlist',
            'maxrecords': 100,
            'format': 'json',
            'sort': 'datedesc',
            'timespan': f'{days_back}d'
        }
        
        try:
            time.sleep(self._rate_limit_delay)
            response = self.session.get(self.GDELT_API, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get('articles', []):
                    articles.append({
                        'source': 'GDELT',
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'domain': article.get('domain', ''),
                        'language': article.get('language', ''),
                        'country': article.get('sourcecountry', ''),
                        'date': article.get('seendate', '')[:10] if article.get('seendate') else '',
                        'tone': article.get('tone', 0),
                        'socialimage': article.get('socialimage', ''),
                    })
        except Exception as e:
            print(f"      GDELT search error: {e}")
        
        return articles
    
    def _search_newsapi(self, query: str, days_back: int) -> List[Dict]:
        """Search NewsAPI (requires API key)"""
        articles = []
        
        if not self.newsapi_key:
            return articles
        
        # NewsAPI only allows 30 days back on free tier
        search_days = min(days_back, 30)
        from_date = (datetime.now() - timedelta(days=search_days)).strftime('%Y-%m-%d')
        
        params = {
            'q': f'"{query}"',
            'from': from_date,
            'sortBy': 'relevancy',
            'language': 'en',
            'pageSize': 100,
            'apiKey': self.newsapi_key
        }
        
        try:
            time.sleep(self._rate_limit_delay)
            response = self.session.get(
                f"{self.NEWSAPI_URL}/everything",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get('articles', []):
                    articles.append({
                        'source': 'NewsAPI',
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'domain': article.get('source', {}).get('name', ''),
                        'author': article.get('author', ''),
                        'date': article.get('publishedAt', '')[:10] if article.get('publishedAt') else '',
                        'content': article.get('content', ''),
                    })
        except Exception as e:
            print(f"      NewsAPI search error: {e}")
        
        return articles
    
    def _process_results(self, results: Dict, query: str) -> Dict:
        """Process and categorize news results"""
        
        for article in results['articles']:
            results['total_articles'] += 1
            
            # Combine title and description for analysis
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            # Check for adverse media
            adverse_matches = [kw for kw in self.ADVERSE_KEYWORDS if kw in text]
            if adverse_matches:
                article['adverse_keywords'] = adverse_matches
                results['adverse_media'].append(article)
                results['sentiment_summary']['adverse'] += 1
            
            # Check for positive media
            elif any(kw in text for kw in self.POSITIVE_KEYWORDS):
                positive_matches = [kw for kw in self.POSITIVE_KEYWORDS if kw in text]
                article['positive_keywords'] = positive_matches
                results['positive_media'].append(article)
                results['sentiment_summary']['positive'] += 1
            else:
                results['sentiment_summary']['neutral'] += 1
            
            # Track by source
            domain = article.get('domain', 'Unknown')
            if domain not in results['by_source']:
                results['by_source'][domain] = 0
            results['by_source'][domain] += 1
            
            # Track by month
            date_str = article.get('date', '')
            if date_str and len(date_str) >= 7:
                month = date_str[:7]  # YYYY-MM
                if month not in results['by_month']:
                    results['by_month'][month] = 0
                results['by_month'][month] += 1
        
        # Sort sources by count
        results['by_source'] = dict(
            sorted(results['by_source'].items(), key=lambda x: x[1], reverse=True)[:20]
        )
        
        # Create timeline
        results['timeline'] = [
            {'month': k, 'count': v} 
            for k, v in sorted(results['by_month'].items())
        ]
        
        return results
    
    def adverse_media_screening(self, name: str) -> Dict:
        """
        Specific adverse media screening for due diligence
        
        Args:
            name: Person or company name
            
        Returns:
            Dict with adverse media findings and risk assessment
        """
        screening = {
            'subject': name,
            'screening_date': datetime.now().isoformat(),
            'adverse_findings': [],
            'risk_categories': {},
            'risk_level': 'LOW',
            'requires_review': False,
            'sources_checked': []
        }
        
        # Define risk categories
        risk_categories = {
            'criminal': ['arrested', 'convicted', 'indicted', 'criminal', 'felony', 'prison'],
            'financial_crime': ['fraud', 'embezzlement', 'money laundering', 'insider trading', 'securities fraud'],
            'regulatory': ['SEC', 'DOJ', 'FTC', 'investigation', 'penalty', 'fine', 'violation', 'sanctions'],
            'litigation': ['lawsuit', 'sued', 'litigation', 'settlement', 'plaintiff', 'defendant'],
            'reputation': ['scandal', 'misconduct', 'harassment', 'discrimination', 'allegations'],
            'financial_distress': ['bankruptcy', 'default', 'insolvent', 'liquidation', 'restructuring']
        }
        
        # Search for adverse media
        search_results = self.search(name, days_back=1095)  # 3 years
        
        # Analyze findings by risk category
        for article in search_results.get('adverse_media', []):
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            for category, keywords in risk_categories.items():
                matches = [kw for kw in keywords if kw in text]
                if matches:
                    if category not in screening['risk_categories']:
                        screening['risk_categories'][category] = []
                    screening['risk_categories'][category].append({
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'date': article.get('date', ''),
                        'keywords_found': matches
                    })
        
        # Calculate risk level
        risk_score = 0
        high_risk_categories = ['criminal', 'financial_crime', 'regulatory']
        medium_risk_categories = ['litigation', 'reputation', 'financial_distress']
        
        for category in screening['risk_categories']:
            count = len(screening['risk_categories'][category])
            if category in high_risk_categories:
                risk_score += count * 30
            elif category in medium_risk_categories:
                risk_score += count * 15
            else:
                risk_score += count * 5
        
        # Cap and categorize
        risk_score = min(risk_score, 100)
        
        if risk_score >= 60:
            screening['risk_level'] = 'HIGH'
            screening['requires_review'] = True
        elif risk_score >= 30:
            screening['risk_level'] = 'MEDIUM'
            screening['requires_review'] = True
        else:
            screening['risk_level'] = 'LOW'
        
        screening['risk_score'] = risk_score
        screening['total_adverse_articles'] = len(search_results.get('adverse_media', []))
        screening['sources_checked'] = ['GDELT Global News Database']
        
        if self.newsapi_key:
            screening['sources_checked'].append('NewsAPI')
        
        return screening
    
    def get_social_media_presence(self, name: str) -> Dict:
        """
        Guide for social media research
        Note: Direct scraping of social platforms violates ToS
        This provides research guidance
        """
        return {
            'subject': name,
            'platforms_to_check': [
                {
                    'platform': 'LinkedIn',
                    'search_url': f'https://www.linkedin.com/search/results/all/?keywords={name.replace(" ", "%20")}',
                    'what_to_look_for': [
                        'Current and past positions',
                        'Education verification',
                        'Professional connections',
                        'Recommendations and endorsements',
                        'Published articles and activity'
                    ]
                },
                {
                    'platform': 'Twitter/X',
                    'search_url': f'https://twitter.com/search?q={name.replace(" ", "%20")}&f=user',
                    'what_to_look_for': [
                        'Public statements and opinions',
                        'Interactions with controversial accounts',
                        'Sentiment and tone',
                        'Professional vs personal content'
                    ]
                },
                {
                    'platform': 'Facebook',
                    'search_url': f'https://www.facebook.com/search/top?q={name.replace(" ", "%20")}',
                    'what_to_look_for': [
                        'Personal life information',
                        'Photos and check-ins',
                        'Group memberships',
                        'Political activity'
                    ]
                },
                {
                    'platform': 'Instagram',
                    'search_url': f'https://www.instagram.com/explore/tags/{name.replace(" ", "")}',
                    'what_to_look_for': [
                        'Lifestyle indicators',
                        'Location patterns',
                        'Personal relationships',
                        'Brand associations'
                    ]
                }
            ],
            'research_notes': [
                'Document all profiles found with screenshots',
                'Note account creation dates and activity levels',
                'Look for inconsistencies with CV/resume',
                'Check for anonymous or alt accounts',
                'Review comments and interactions, not just posts'
            ]
        }


# For testing
if __name__ == '__main__':
    collector = NewsSearchCollector()
    
    print("Testing News Search collector...")
    print("\nSearching for 'Theranos'...")
    
    results = collector.search("Theranos", days_back=365)
    
    print(f"Total articles found: {results['total_articles']}")
    print(f"Adverse media: {len(results['adverse_media'])}")
    print(f"Positive media: {len(results['positive_media'])}")
    
    print("\nTop sources:")
    for source, count in list(results['by_source'].items())[:5]:
        print(f"  {source}: {count}")
    
    print("\nAdverse media screening...")
    screening = collector.adverse_media_screening("Elizabeth Holmes")
    print(f"Risk Level: {screening['risk_level']}")
    print(f"Risk Score: {screening['risk_score']}/100")
    print(f"Risk Categories: {list(screening['risk_categories'].keys())}")
