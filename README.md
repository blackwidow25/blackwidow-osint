# Black Widow Global OSINT Research Tool

**Automated Corporate Intelligence & Investigative Due Diligence**

This tool performs comprehensive open-source intelligence (OSINT) research on companies, LLCs, and individuals—delivering the kind of intelligence-grade due diligence your PE and M&A clients expect.

---

## What This Tool Does

Input a company name, LLC, or person and receive a comprehensive intelligence dossier including:

### For Companies/LLCs
- **Corporate Registry Data**: Formation, registered agents, amendments, status
- **SEC Filings**: 10-K, 10-Q, 8-K, proxy statements, insider transactions
- **Beneficial Ownership**: 13D/13G filings showing 5%+ owners
- **UCC Liens**: Secured creditors and collateral pledged
- **Litigation History**: Federal and state court cases
- **Political Exposure**: Campaign contributions and PAC activity
- **Adverse Media**: News screening for red flags
- **Corporate Network**: Related entities, shared officers, hidden connections

### For Individuals
- **Corporate Affiliations**: Board seats, officer positions across companies
- **SEC Activity**: Insider transactions, beneficial ownership filings
- **Political Donations**: FEC contribution history
- **Litigation**: Civil and criminal court records
- **Adverse Media**: News screening with risk categorization
- **Social Network Guidance**: Research framework for LinkedIn, Twitter, etc.

---

## Data Sources & Costs

### FREE Sources (Included)
| Source | Data | Rate Limits |
|--------|------|-------------|
| **SEC EDGAR** | All SEC filings, insider transactions, beneficial ownership | 10 req/sec |
| **OpenCorporates** | Global corporate registry (limited) | 50 req/month |
| **FEC** | Political campaign contributions | Unlimited with free key |
| **CourtListener/RECAP** | Federal court opinions, PACER archive | Reasonable use |
| **GDELT** | Global news database | Generous limits |
| **State SOS Websites** | Corporate filings, UCC (manual guidance) | N/A |

### PAID Sources (Optional, Recommended for Production)
| Source | Data | Cost |
|--------|------|------|
| **OpenCorporates Pro** | Full global corporate data, officers, network | $49/month |
| **NewsAPI** | Real-time news from 80,000+ sources | Free tier: 100/day |
| **PACER** | Full federal court records | $0.10/page |
| **LexisNexis/Westlaw** | Comprehensive legal database | Enterprise pricing |

---

## Installation (Mac)

### Step 1: Open Terminal
Press `Cmd + Space`, type "Terminal", and press Enter.

### Step 2: Create Project Directory
```bash
# Create a folder for the tool
mkdir -p ~/BlackWidowOSINT
cd ~/BlackWidowOSINT
```

### Step 3: Download the Tool
Copy the entire `osint_tool` folder to `~/BlackWidowOSINT/`

### Step 4: Run the Installer
```bash
cd ~/BlackWidowOSINT/osint_tool
chmod +x install_mac.sh
./install_mac.sh
```

This will install:
- Homebrew (if not present)
- Python 3
- Node.js
- Required packages (docx, requests)

---

## Usage

### Basic Company Research
```bash
python3 osint_research.py company "Blackstone Group" --state DE
```

### Company Research with All States
```bash
python3 osint_research.py company "Target Corporation"
```

### Person Research
```bash
python3 osint_research.py person "Stephen Schwarzman" --company "Blackstone"
```

### Person Research with State
```bash
python3 osint_research.py person "John Smith" --state NY --company "Acme Corp"
```

### Using Custom Configuration
```bash
python3 osint_research.py company "Target LLC" --config config/my_config.json
```

### Specify Output Location
```bash
python3 osint_research.py company "Target LLC" --output /path/to/output/my_report
```

---

## Output

Reports are generated in two formats:
1. **JSON** - Raw data for programmatic use or further analysis
2. **Word Document (DOCX)** - Professional formatted report for clients

Reports are saved to the `output/` directory by default.

### Report Sections
1. **Executive Summary** - Risk assessment and key findings
2. **Subject Profile** - Basic identification data
3. **Corporate History** - Formation, amendments, status changes
4. **Officers & Directors** - Current and historical leadership
5. **Red Flags** - Risk indicators with severity ratings
6. **Related Entities** - Corporate network and connections
7. **Political Exposure** - Campaign contributions
8. **Methodology** - Data sources consulted
9. **Appendices** - Raw data extracts

---

## Configuration

Edit `config/default_config.json` to customize:

```json
{
  "api_keys": {
    "opencorporates": "YOUR_KEY_HERE",
    "newsapi": "YOUR_KEY_HERE",
    "fec": "YOUR_KEY_HERE"
  },
  "modules": {
    "sec_edgar": true,
    "opencorporates": true,
    "fec_donations": true,
    "court_records": true,
    "ucc_filings": true,
    "news_search": true
  },
  "branding": {
    "company_name": "Black Widow Global",
    "tagline": "Corporate Intelligence & Investigative Due Diligence"
  }
}
```

---

## Getting API Keys

### OpenCorporates (Recommended)
1. Go to https://opencorporates.com/api_accounts/new
2. Sign up for API access
3. Free tier: 50 requests/month
4. Pro tier ($49/month): 5,000 requests/month

### NewsAPI (Free)
1. Go to https://newsapi.org/register
2. Create free account
3. Get API key from dashboard
4. Free: 100 requests/day

### FEC API (Free)
1. Go to https://api.data.gov/signup/
2. Enter email
3. Receive API key instantly
4. Provides higher rate limits

### PACER (Federal Courts)
1. Go to https://pacer.uscourts.gov/register-account
2. Create account
3. First $30/quarter is free
4. $0.10/page after that

---

## Extending the Tool

### Adding New Data Sources
1. Create a new module in `modules/`
2. Follow the pattern of existing collectors
3. Add to `modules/__init__.py`
4. Update `osint_research.py` to call your module

### Customizing Reports
Edit `modules/report_generator.py` to modify:
- Report sections
- Formatting and styling
- Branding elements
- Risk scoring logic

---

## Troubleshooting

### "Node.js not found"
```bash
brew install node
```

### "docx module not found"
```bash
npm install -g docx
```

### "Permission denied"
```bash
chmod +x osint_research.py
chmod +x install_mac.sh
```

### SEC API Rate Limited
The SEC limits to 10 requests/second. The tool handles this automatically, but if you see errors, wait a moment and retry.

### OpenCorporates 401 Error
Free tier has very limited requests. Consider upgrading or use SEC EDGAR as primary source.

---

## Legal Notice

This tool accesses only publicly available information through official APIs and public websites. Users are responsible for ensuring their use complies with:
- Terms of service for each data source
- Fair Credit Reporting Act (FCRA) if used for employment/credit decisions
- Applicable privacy laws in your jurisdiction

This tool is designed for legitimate due diligence purposes including:
- M&A transaction support
- Investment due diligence  
- Vendor/supplier vetting
- Regulatory compliance
- Litigation support

---

## Support

For questions or customization requests, contact Black Widow Global.

---

**Version**: 1.0.0  
**Last Updated**: January 2025
