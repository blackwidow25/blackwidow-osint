import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import requests
import json
import sys
sys.path.insert(0, ".")
from modules.sec_edgar import SECEdgarCollector
from modules.fec_donations import FECDonationsCollector
from modules.court_records import CourtRecordsCollector
from modules.news_search import NewsSearchCollector
from modules.report_generator import ReportGenerator

st.set_page_config(page_title="Black Widow Global", page_icon="🕷️", layout="wide")

API_KEYS = {"opensanctions": "c94a6cd152939210791e9b7d3bda0ffd", "proxycurl": "383162556aee4a9b9c55be61b005688f", "newsapi": "46b27bebc9544e53a31f1ad25972eea2"}

CRISIS_KEYWORDS = ["bankruptcy", "layoff", "layoffs", "restructuring", "delisted", "SEC investigation", "fraud", "data breach", "hack", "cyber attack", "CEO resign", "CFO resign", "executive exodus", "stock crash", "default", "chapter 11", "chapter 7", "liquidation", "shutdown", "closing", "whistleblower", "scandal", "indictment", "arrested", "convicted", "settlement", "class action", "regulatory action", "fine", "penalty", "sanction"]

GEOPOLITICAL_RISK_KEYWORDS = ["china", "russia", "iran", "north korea", "tariff", "trade war", "export control", "sanctions", "national security", "cfius", "foreign investment", "espionage", "intellectual property theft", "forced technology transfer"]

SUPPLY_CHAIN_KEYWORDS = ["supply chain", "supplier", "shortage", "disruption", "single source", "manufacturing", "outsourced", "offshore", "vendor", "dependency"]

def check_sanctions(name):
    try:
        url = "https://api.opensanctions.org/match/default"
        headers = {"Authorization": "ApiKey " + API_KEYS["opensanctions"]}
        resp = requests.get(url, params={"schema": "Company", "properties.name": name}, headers=headers, timeout=10)
        if resp.status_code == 200:
            return {"matches": resp.json().get("results", []), "count": len(resp.json().get("results", []))}
    except:
        pass
    return {"matches": [], "count": 0}

def get_current_news(company_name):
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": f'"{company_name}"',
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": API_KEYS["newsapi"]
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            articles = resp.json().get("articles", [])
            return articles
    except:
        pass
    return []

def analyze_news_intelligence(articles, company_name):
    analysis = {
        "total_articles": len(articles),
        "crisis_signals": [],
        "geopolitical_risks": [],
        "supply_chain_risks": [],
        "sentiment_score": 50,
        "key_articles": [],
        "intelligence_summary": ""
    }
    
    crisis_count = 0
    geo_count = 0
    supply_count = 0
    
    for article in articles[:30]:
        title = (article.get("title") or "").lower()
        desc = (article.get("description") or "").lower()
        content = title + " " + desc
        
        article_info = {
            "title": article.get("title", "Unknown"),
            "source": article.get("source", {}).get("name", "Unknown"),
            "date": article.get("publishedAt", "")[:10],
            "url": article.get("url", ""),
            "flags": []
        }
        
        for keyword in CRISIS_KEYWORDS:
            if keyword in content:
                article_info["flags"].append(keyword)
                crisis_count += 1
        
        for keyword in GEOPOLITICAL_RISK_KEYWORDS:
            if keyword in content:
                article_info["flags"].append(f"GEO: {keyword}")
                geo_count += 1
        
        for keyword in SUPPLY_CHAIN_KEYWORDS:
            if keyword in content:
                article_info["flags"].append(f"SUPPLY: {keyword}")
                supply_count += 1
        
        if article_info["flags"]:
            analysis["key_articles"].append(article_info)
    
    if crisis_count > 10:
        analysis["crisis_signals"].append(f"CRITICAL: {crisis_count} crisis indicators in recent news")
        analysis["sentiment_score"] = 85
    elif crisis_count > 5:
        analysis["crisis_signals"].append(f"HIGH: {crisis_count} crisis indicators detected")
        analysis["sentiment_score"] = 70
    elif crisis_count > 2:
        analysis["crisis_signals"].append(f"ELEVATED: {crisis_count} concerning mentions")
        analysis["sentiment_score"] = 55
    
    if geo_count > 3:
        analysis["geopolitical_risks"].append(f"Significant geopolitical exposure ({geo_count} mentions)")
    
    if supply_count > 2:
        analysis["supply_chain_risks"].append(f"Supply chain concerns identified ({supply_count} mentions)")
    
    return analysis

def generate_intelligence_assessment(findings, target):
    assessment = {
        "overall_narrative": "",
        "key_concerns": [],
        "risk_factors": [],
        "opportunities": [],
        "recommendation": "",
        "confidence": "MEDIUM"
    }
    
    news_intel = findings.get("data_sources", {}).get("news_intelligence", {})
    court_data = findings.get("data_sources", {}).get("court_records", [])
    fec_data = findings.get("data_sources", {}).get("fec_donations", {})
    sanctions = findings.get("data_sources", {}).get("sanctions", {})
    
    crisis_signals = news_intel.get("crisis_signals", [])
    geo_risks = news_intel.get("geopolitical_risks", [])
    supply_risks = news_intel.get("supply_chain_risks", [])
    key_articles = news_intel.get("key_articles", [])
    
    narrative_parts = []
    
    if sanctions.get("count", 0) > 0:
        narrative_parts.append(f"CRITICAL: {target} has potential matches on global sanctions lists. All engagement must cease pending legal review.")
        assessment["key_concerns"].append("Sanctions exposure - potential criminal liability")
        assessment["confidence"] = "HIGH"
    
    if crisis_signals:
        narrative_parts.append(f"Current media analysis indicates {target} is experiencing significant operational distress. {crisis_signals[0]}.")
        assessment["key_concerns"].extend(crisis_signals)
    
    if key_articles:
        crisis_keywords_found = set()
        for article in key_articles:
            for flag in article.get("flags", []):
                if not flag.startswith("GEO:") and not flag.startswith("SUPPLY:"):
                    crisis_keywords_found.add(flag)
        
        if "bankruptcy" in crisis_keywords_found or "chapter 11" in crisis_keywords_found:
            narrative_parts.append("CRITICAL: Bankruptcy indicators detected in recent news coverage. Company may be insolvent or approaching insolvency.")
            assessment["key_concerns"].append("Bankruptcy/insolvency risk")
        
        if "data breach" in crisis_keywords_found or "hack" in crisis_keywords_found:
            narrative_parts.append("ELEVATED RISK: Cybersecurity incident detected. Potential regulatory fines, litigation, and reputational damage.")
            assessment["key_concerns"].append("Cybersecurity/data breach exposure")
        
        if "layoff" in crisis_keywords_found or "layoffs" in crisis_keywords_found:
            narrative_parts.append("Company is undergoing workforce reduction, indicating financial pressure or strategic restructuring.")
            assessment["risk_factors"].append("Workforce instability")
        
        if "SEC investigation" in crisis_keywords_found or "fraud" in crisis_keywords_found:
            narrative_parts.append("CRITICAL: Regulatory investigation or fraud allegations detected. Significant legal and financial exposure.")
            assessment["key_concerns"].append("Regulatory/fraud investigation")
        
        if "CEO resign" in crisis_keywords_found or "executive exodus" in crisis_keywords_found:
            narrative_parts.append("Leadership instability detected. Executive departures often precede or indicate deeper organizational issues.")
            assessment["key_concerns"].append("Leadership instability")
    
    if geo_risks:
        narrative_parts.append(f"Geopolitical exposure identified: {', '.join(geo_risks)}. Consider regulatory and market access risks.")
        assessment["risk_factors"].extend(geo_risks)
    
    if supply_risks:
        narrative_parts.append(f"Supply chain vulnerabilities noted: {', '.join(supply_risks)}. Assess concentration and disruption risk.")
        assessment["risk_factors"].extend(supply_risks)
    
    if isinstance(court_data, list) and len(court_data) > 5:
        narrative_parts.append(f"Significant litigation history with {len(court_data)} court records identified. Pattern analysis recommended.")
        assessment["risk_factors"].append(f"Litigation exposure ({len(court_data)} cases)")
    
    if isinstance(fec_data, dict) and (fec_data.get("total_amount") or 0) > 100000:
        amt = fec_data.get("total_amount", 0)
        narrative_parts.append(f"Substantial political activity (${amt:,.0f} in contributions) indicates regulatory relationships and potential policy exposure.")
        assessment["risk_factors"].append("Political/regulatory exposure")
    
    if not narrative_parts:
        narrative_parts.append(f"No significant adverse indicators identified for {target} in current analysis. Standard due diligence procedures recommended.")
        assessment["confidence"] = "MEDIUM"
    
    assessment["overall_narrative"] = " ".join(narrative_parts)
    
    return assessment

def calculate_risk(findings, target):
    scores = {
        "Leadership": {"score": 15, "weight": 0.15, "factors": []},
        "Financial": {"score": 15, "weight": 0.20, "factors": []},
        "Legal": {"score": 15, "weight": 0.15, "factors": []},
        "Regulatory": {"score": 10, "weight": 0.10, "factors": []},
        "Reputational": {"score": 15, "weight": 0.10, "factors": []},
        "Political": {"score": 10, "weight": 0.05, "factors": []},
        "Operational": {"score": 10, "weight": 0.10, "factors": []},
        "Geopolitical": {"score": 10, "weight": 0.10, "factors": []},
        "Supply Chain": {"score": 10, "weight": 0.05, "factors": []}
    }
    red_flags = []
    
    news_intel = findings.get("data_sources", {}).get("news_intelligence", {})
    sentiment = news_intel.get("sentiment_score", 50)
    key_articles = news_intel.get("key_articles", [])
    
    if sentiment >= 80:
        scores["Reputational"]["score"] = 90
        scores["Reputational"]["factors"].append("CRITICAL: Major crisis detected in news")
        scores["Operational"]["score"] = 75
        scores["Financial"]["score"] = 80
        red_flags.append({
            "severity": "CRITICAL",
            "category": "Corporate Crisis",
            "finding": "Multiple crisis indicators detected in current news coverage",
            "so_what": "Company appears to be in active crisis. News analysis shows bankruptcy, regulatory action, or major operational failure indicators. Investment at this time carries extreme risk of total loss.",
            "action": "HALT all investment activity. If already invested, engage crisis management and exit strategy teams immediately."
        })
    elif sentiment >= 65:
        scores["Reputational"]["score"] = 70
        scores["Reputational"]["factors"].append("HIGH: Significant negative news coverage")
        scores["Operational"]["score"] = 55
    
    crisis_keywords_found = set()
    for article in key_articles:
        for flag in article.get("flags", []):
            crisis_keywords_found.add(flag.lower())
    
    if "bankruptcy" in crisis_keywords_found or "chapter 11" in crisis_keywords_found or "chapter 7" in crisis_keywords_found:
        scores["Financial"]["score"] = 95
        scores["Financial"]["factors"].append("CRITICAL: Bankruptcy indicators")
        red_flags.append({
            "severity": "CRITICAL",
            "category": "Financial",
            "finding": "Bankruptcy or insolvency indicators in recent news",
            "so_what": "Company may be insolvent or entering bankruptcy proceedings. All unsecured investments likely to result in total loss. Secured positions may face significant impairment.",
            "action": "Do not invest. If existing exposure, engage restructuring counsel immediately."
        })
    
    if "data breach" in crisis_keywords_found or "hack" in crisis_keywords_found or "cyber attack" in crisis_keywords_found:
        scores["Operational"]["score"] = max(scores["Operational"]["score"], 75)
        scores["Regulatory"]["score"] = max(scores["Regulatory"]["score"], 65)
        scores["Operational"]["factors"].append("Cybersecurity incident detected")
        red_flags.append({
            "severity": "HIGH",
            "category": "Cybersecurity",
            "finding": "Data breach or cyber attack reported",
            "so_what": "Cybersecurity incidents typically result in: regulatory fines ($10M-$500M+ for major breaches), class action litigation, customer churn (15-25%), and long-term brand damage. GDPR/CCPA exposure if consumer data involved.",
            "action": "Request incident response report, quantify affected records, assess regulatory exposure by jurisdiction."
        })
    
    if any(k in crisis_keywords_found for k in ["ceo resign", "cfo resign", "executive exodus"]):
        scores["Leadership"]["score"] = 80
        scores["Leadership"]["factors"].append("Executive departure/instability")
        red_flags.append({
            "severity": "HIGH",
            "category": "Leadership",
            "finding": "Executive leadership changes or departures",
            "so_what": "C-suite departures often precede disclosure of material issues. 67% of sudden CEO departures are followed by negative earnings surprises within 2 quarters. Institutional knowledge loss impacts operational continuity.",
            "action": "Investigate circumstances of departure. Review D&O insurance. Assess bench strength and succession planning."
        })
    
    if any(k in crisis_keywords_found for k in ["sec investigation", "fraud", "indictment", "convicted"]):
        scores["Regulatory"]["score"] = 90
        scores["Legal"]["score"] = 85
        scores["Regulatory"]["factors"].append("CRITICAL: Regulatory/criminal investigation")
        red_flags.append({
            "severity": "CRITICAL",
            "category": "Legal/Regulatory",
            "finding": "Regulatory investigation or fraud allegations",
            "so_what": "SEC investigations result in average settlements of $50M+ for public companies. Criminal indictments can trigger immediate contract terminations, bank covenant violations, and management distraction lasting 2-4 years.",
            "action": "HALT investment. Engage securities litigation counsel for exposure assessment."
        })
    
    if any(k in crisis_keywords_found for k in ["layoff", "layoffs", "restructuring"]):
        scores["Operational"]["score"] = max(scores["Operational"]["score"], 55)
        scores["Operational"]["factors"].append("Workforce restructuring underway")
    
    geo_risks = news_intel.get("geopolitical_risks", [])
    if geo_risks:
        scores["Geopolitical"]["score"] = 65
        scores["Geopolitical"]["factors"].append("International exposure concerns")
        if any("china" in str(r).lower() for r in geo_risks):
            scores["Geopolitical"]["score"] = 75
            scores["Geopolitical"]["factors"].append("China-related risk exposure")
            red_flags.append({
                "severity": "MEDIUM",
                "category": "Geopolitical",
                "finding": "China-related business exposure identified",
                "so_what": "China exposure creates: tariff risk, IP theft concerns, CFIUS review requirements for M&A, potential sanctions/export control issues, and ESG concerns for some institutional investors.",
                "action": "Map China revenue/supply chain dependency. Assess CFIUS implications. Review export control compliance."
            })
    
    supply_risks = news_intel.get("supply_chain_risks", [])
    if supply_risks:
        scores["Supply Chain"]["score"] = 60
        scores["Supply Chain"]["factors"].append("Supply chain vulnerabilities noted")
    
    court = findings.get("data_sources", {}).get("court_records", [])
    if isinstance(court, list):
        count = len(court)
        if count > 5:
            scores["Legal"]["score"] = max(scores["Legal"]["score"], 75)
            scores["Legal"]["factors"].append(f"{count} litigation matters")
            red_flags.append({
                "severity": "HIGH",
                "category": "Legal",
                "finding": f"{count} litigation matters identified",
                "so_what": f"High litigation volume indicates potential operational issues, regulatory non-compliance, or aggressive business practices. Each active case represents legal cost of $50K-$500K+ and management distraction.",
                "action": "Request litigation schedule with exposure estimates. Identify patterns (employment, IP, contract, regulatory)."
            })
        elif count > 2:
            scores["Legal"]["score"] = max(scores["Legal"]["score"], 50)
            scores["Legal"]["factors"].append(f"{count} litigation matters")
    
    fec = findings.get("data_sources", {}).get("fec_donations", {})
    if isinstance(fec, dict):
        amt = fec.get("total_amount", 0) or 0
        if amt > 500000:
            scores["Political"]["score"] = 75
            scores["Political"]["factors"].append(f"${amt:,.0f} political contributions")
            red_flags.append({
                "severity": "MEDIUM",
                "category": "Political",
                "finding": f"${amt:,.0f} in political contributions",
                "so_what": "Heavy political spending indicates regulatory dependencies. Administration changes can impact: government contracts, regulatory approvals, tax treatment, and subsidy eligibility. Also creates PR risk if contributions become controversial.",
                "action": "Map regulatory dependencies. Stress test business model against policy change scenarios."
            })
        elif amt > 100000:
            scores["Political"]["score"] = 50
            scores["Political"]["factors"].append(f"${amt:,.0f} political contributions")
    
    sanctions = findings.get("data_sources", {}).get("sanctions", {})
    if sanctions.get("count", 0) > 0:
        scores["Regulatory"]["score"] = 100
        scores["Regulatory"]["factors"].append("SANCTIONS MATCH")
        red_flags.append({
            "severity": "CRITICAL",
            "category": "Sanctions",
            "finding": "POTENTIAL MATCH ON GLOBAL SANCTIONS LIST",
            "so_what": "IMMEDIATE STOP. Engaging with sanctioned entities creates criminal liability for all transaction parties. Penalties include: imprisonment up to 20 years, fines of $1M+ per violation, and permanent reputational damage.",
            "action": "CEASE ALL ACTIVITY. Engage OFAC counsel immediately. Do not proceed under any circumstances until cleared."
        })
    
    weighted_score = sum(scores[cat]["score"] * scores[cat]["weight"] for cat in scores)
    
    return scores, weighted_score, red_flags

# MAIN APP
with st.sidebar:
    st.markdown("## 🕷️ BLACK WIDOW GLOBAL")
    st.caption("Corporate Intelligence Platform")
    st.markdown("---")
    target = st.text_input("🎯 Target Company/Person")
    search_type = st.radio("Type", ["Company", "Person"], horizontal=True)
    state = st.selectbox("State", ["", "DE", "NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "NJ", "MA", "VA", "WA", "CO", "AZ"])
    st.markdown("---")
    run = st.button("🔍 RUN INTELLIGENCE SEARCH", use_container_width=True, type="primary")
    st.markdown("---")
    st.caption("v3.0 | Black Widow Global")

if not run or not target:
    st.markdown("# 🕷️ BLACK WIDOW GLOBAL")
    st.markdown("### Corporate Intelligence & Investment Due Diligence")
    st.info("Enter a target in the sidebar and click **RUN INTELLIGENCE SEARCH**")
else:
    findings = {"target": target, "target_type": search_type.lower(), "data_sources": {}, "timestamp": datetime.now().isoformat()}
    
    progress = st.progress(0)
    status = st.empty()
    
    status.text("🔍 Gathering current news intelligence...")
    progress.progress(0.15)
    news_articles = get_current_news(target)
    news_intel = analyze_news_intelligence(news_articles, target)
    findings["data_sources"]["news_intelligence"] = news_intel
    findings["data_sources"]["news_articles"] = news_articles
    
    status.text("🔍 Searching SEC EDGAR...")
    progress.progress(0.30)
    try:
        findings["data_sources"]["sec_edgar"] = SECEdgarCollector().search_company(target) if search_type == "Company" else SECEdgarCollector().search_person(target)
    except Exception as e:
        findings["data_sources"]["sec_edgar"] = {"error": str(e)}
    
    status.text("🔍 Searching Court Records...")
    progress.progress(0.45)
    try:
        findings["data_sources"]["court_records"] = CourtRecordsCollector().search_company(target, state=state) if search_type == "Company" else CourtRecordsCollector().search_person(target, state=state)
    except Exception as e:
        findings["data_sources"]["court_records"] = {"error": str(e)}
    
    status.text("🔍 Searching FEC Political Donations...")
    progress.progress(0.60)
    try:
        findings["data_sources"]["fec_donations"] = FECDonationsCollector().search_by_employer(target) if search_type == "Company" else FECDonationsCollector().search_donor(target, state=state)
    except Exception as e:
        findings["data_sources"]["fec_donations"] = {"error": str(e)}
    
    status.text("🔍 Checking Global Sanctions Lists...")
    progress.progress(0.75)
    findings["data_sources"]["sanctions"] = check_sanctions(target)
    
    status.text("🔍 Running GDELT news search...")
    progress.progress(0.85)
    try:
        findings["data_sources"]["news_search"] = NewsSearchCollector().search(target, days_back=365)
    except Exception as e:
        findings["data_sources"]["news_search"] = {"error": str(e)}
    
    status.text("🧠 Analyzing intelligence...")
    progress.progress(0.95)
    intel_assessment = generate_intelligence_assessment(findings, target)
    findings["intelligence_assessment"] = intel_assessment
    
    scores, overall, red_flags = calculate_risk(findings, target)
    
    progress.progress(1.0)
    status.empty()
    
    if overall >= 65:
        level, color, signal = "CRITICAL RISK", "#dc2626", "DO NOT PROCEED"
        rec = "⛔ WALK AWAY. Multiple critical risk factors identified. Investment not recommended under any terms."
    elif overall >= 50:
        level, color, signal = "HIGH RISK", "#ea580c", "NOT RECOMMENDED"
        rec = "🚫 HIGH CAUTION. Significant risks require mitigation or substantial price adjustment. Consider walking away."
    elif overall >= 35:
        level, color, signal = "ELEVATED RISK", "#ca8a04", "CONDITIONAL"
        rec = "⚠️ PROCEED WITH CAUTION. Address flagged items before closing. Enhanced DD required."
    elif overall >= 20:
        level, color, signal = "MODERATE RISK", "#65a30d", "PROCEED WITH MONITORING"
        rec = "📋 Acceptable risk profile. Standard DD sufficient with ongoing monitoring of noted items."
    else:
        level, color, signal = "LOW RISK", "#16a34a", "PROCEED"
        rec = "✅ No significant concerns identified. Standard due diligence sufficient."
    
    st.markdown(f"# 📋 Intelligence Dossier: {target}")
    st.caption(f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Black Widow Global | CONFIDENTIAL")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Score", f"{overall:.0f}/100")
    with col2:
        st.markdown(f"**Risk Level**")
        st.markdown(f"<span style='color:{color};font-size:1.3rem;font-weight:bold;'>{level}</span>", unsafe_allow_html=True)
    col3.metric("Red Flags", len(red_flags))
    with col4:
        st.markdown(f"**Signal**")
        st.markdown(f"<span style='color:{color};font-size:1.2rem;font-weight:bold;'>{signal}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🧠 Intelligence Assessment")
    st.markdown(f"**Analyst Narrative:**")
    st.info(intel_assessment.get("overall_narrative", "Analysis pending."))
    
    st.markdown(f"**Recommendation:** {rec}")
    
    if red_flags:
        st.markdown("### 🚨 Critical Findings")
        for flag in red_flags:
            severity_colors = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "MEDIUM": "#ca8a04", "LOW": "#65a30d"}
            with st.expander(f"🔴 [{flag['severity']}] {flag['category']}: {flag['finding']}", expanded=(flag['severity'] in ['CRITICAL', 'HIGH'])):
                st.markdown(f"**Business Impact (So What):**")
                st.warning(flag["so_what"])
                st.markdown(f"**Recommended Action:**")
                st.success(flag["action"])
    
    st.markdown("### 📊 Risk Matrix")
    col1, col2 = st.columns([3, 2])
    with col1:
        cats = list(scores.keys())
        vals = [scores[c]["score"] for c in cats]
        colors_list = ["#dc2626" if v >= 65 else "#ea580c" if v >= 50 else "#ca8a04" if v >= 35 else "#65a30d" if v >= 20 else "#16a34a" for v in vals]
        fig = go.Figure(go.Bar(y=cats, x=vals, orientation='h', marker_color=colors_list, text=vals, textposition='inside'))
        fig.update_layout(xaxis_range=[0, 100], height=450, xaxis_title="Risk Score")
        fig.add_vline(x=65, line_dash="dash", line_color="#dc2626")
        fig.add_vline(x=50, line_dash="dash", line_color="#ea580c")
        fig.add_vline(x=35, line_dash="dash", line_color="#ca8a04")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = go.Figure(go.Indicator(mode="gauge+number", value=overall, title={'text': "Overall Risk"}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}, 'steps': [{'range': [0, 20], 'color': "#dcfce7"}, {'range': [20, 35], 'color': "#fef9c3"}, {'range': [35, 50], 'color': "#fed7aa"}, {'range': [50, 65], 'color': "#fecaca"}, {'range': [65, 100], 'color': "#fca5a5"}]}))
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("### 📰 Key News Intelligence")
    key_articles = news_intel.get("key_articles", [])
    if key_articles:
        for article in key_articles[:10]:
            flags_str = ", ".join(article.get("flags", []))
            st.markdown(f"**{article.get('title', 'Unknown')}**")
            st.caption(f"{article.get('source', 'Unknown')} | {article.get('date', '')} | Flags: {flags_str}")
            if article.get("url"):
                st.markdown(f"[Read Article]({article.get('url')})")
            st.markdown("---")
    else:
        st.info("No significant news flags detected.")
    
    st.markdown("### 📋 Detailed Findings")
    tab1, tab2, tab3, tab4 = st.tabs(["⚖️ Legal", "💰 Financial", "🏛️ Political", "🚨 Sanctions"])
    
    with tab1:
        court = findings["data_sources"].get("court_records", [])
        if isinstance(court, list) and court:
            st.error(f"**{len(court)} litigation record(s) found**")
            for c in court[:10]:
                st.markdown(f"**{c.get('case_name', 'Unknown')}**")
                st.caption(f"{c.get('court', '')} | {c.get('date_filed', '')}")
        else:
            st.success("No litigation found")
    
    with tab2:
        sec = findings["data_sources"].get("sec_edgar", {})
        if isinstance(sec, dict) and sec.get("company_info"):
            st.json(sec["company_info"])
        else:
            st.info("No SEC data")
    
    with tab3:
        fec = findings["data_sources"].get("fec_donations", {})
        if isinstance(fec, dict) and fec.get("total_amount"):
            st.metric("Total Contributions", f"${fec['total_amount']:,.0f}")
        else:
            st.info("No FEC data")
    
    with tab4:
        sanctions = findings["data_sources"].get("sanctions", {})
        if sanctions.get("count", 0) > 0:
            st.error("🚨 POTENTIAL SANCTIONS MATCH")
            st.json(sanctions)
        else:
            st.success("No sanctions matches")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Generate Word Report", use_container_width=True):
            findings["summary"] = {"risk_assessment": {"level": level, "score": overall, "recommendation": rec, "invest_signal": signal}, "risk_scores": {k: v["score"] for k, v in scores.items()}, "red_flags_count": len(red_flags), "red_flags": red_flags}
            try:
                path = ReportGenerator().generate_text_report(findings, "")
                st.success(f"✅ Report saved: {path}")
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        st.download_button("📊 Download JSON", data=json.dumps(findings, indent=2, default=str), file_name=f"{target.replace(' ', '_')}_intel.json", mime="application/json")
