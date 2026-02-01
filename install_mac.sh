#!/bin/bash
# Black Widow Global OSINT Tool - Installation Script for Mac
# ============================================================

echo "=========================================="
echo "BLACK WIDOW GLOBAL OSINT TOOL INSTALLER"
echo "=========================================="
echo ""

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "[!] Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "[✓] Homebrew found"
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 not found. Installing..."
    brew install python3
else
    echo "[✓] Python 3 found: $(python3 --version)"
fi

# Check for Node.js (required for DOCX generation)
if ! command -v node &> /dev/null; then
    echo "[!] Node.js not found. Installing..."
    brew install node
else
    echo "[✓] Node.js found: $(node --version)"
fi

# Install Node.js docx package globally
echo ""
echo "[*] Installing docx package for Word document generation..."
npm install -g docx

# Install Python dependencies
echo ""
echo "[*] Installing Python dependencies..."
pip3 install --user requests

# Create output directory
mkdir -p output

# Make main script executable
chmod +x osint_research.py

echo ""
echo "=========================================="
echo "INSTALLATION COMPLETE"
echo "=========================================="
echo ""
echo "To run the tool:"
echo ""
echo "  Research a company:"
echo "    python3 osint_research.py company \"Company Name\" --state DE"
echo ""
echo "  Research a person:"
echo "    python3 osint_research.py person \"John Smith\" --company \"Acme Corp\""
echo ""
echo "  With custom config:"
echo "    python3 osint_research.py company \"Target LLC\" --config config/my_config.json"
echo ""
echo "Reports will be saved to the 'output' directory."
echo ""
echo "=========================================="
echo "API KEYS (Optional but Recommended)"
echo "=========================================="
echo ""
echo "For enhanced results, add API keys to config/default_config.json:"
echo ""
echo "  - OpenCorporates Pro: https://opencorporates.com/api_accounts/new"
echo "    Cost: \$49/month for 5,000 requests"
echo ""
echo "  - NewsAPI: https://newsapi.org/register"  
echo "    Cost: FREE for 100 requests/day"
echo ""
echo "  - FEC API: https://api.data.gov/signup/"
echo "    Cost: FREE (higher rate limits with key)"
echo ""
echo "  - PACER: https://pacer.uscourts.gov/register-account"
echo "    Cost: \$0.10/page (first \$30/quarter free)"
echo ""
