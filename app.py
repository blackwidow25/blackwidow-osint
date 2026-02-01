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

API_KEYS = {"opensanctions": "c94a6cd152939210791e9b7d3bda0ffd", "proxycurl": "383162556aee4a9b9c55be61b005688f"}

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

def get_linkedin_company(company_name):
    try:
        headers = {"Authorization": "Bearer " + API_KEYS["proxycurl"]}
        search_url = "https://nubela.co/proxycurl/api/linkedin/company/resolve"
        resp = requests.get(search_url, params={"company_name": company_name}, headers=headers, timeout=15)
        if resp.status_code == 200 and resp.json().get("url"):
            detail_resp = requests.get("https://nubela.co/proxycurl/api/linkedin/company", params={"url": resp.json()["url"]}, headers=headers, timeout=15)
            if detail_resp.status_code == 200:
                return detail_resp.json()
    except:
        pass
    return None

def get_leadership_info(company_name):
    try:
        headers = {"Authorization": "Bearer " + API_KEYS["proxycurl"]}
        search_url = "https://nubela.co/proxycurl/api/linkedin/company/resolve"
        resp = requests.get(search_url, params={"company_name": company_name}, headers=headers, timeout=15)
        if resp.status_code == 200 and resp.json().get("url"):
            emp_url = "https://nubela.co/proxycurl/api/linkedin/company/employees"
            emp_resp = requests.get(emp_url, params={"url": resp.json()["url"], "role_search": "CEO|CFO|COO|President|Founder|Director"}, headers=headers, timeout=15)
            if emp_resp.status_code == 200:
                return emp_resp.json()
    except:
        pass
    return None

def assess_social_media_risk(company_name):
    risk_data = {
        "twitter_search": f"https://twitter.com/search?q={company_name.replace(' ', '%20')}%20-filter%3Areplies&f=live",
        "reddit_search": f"https://www.reddit.com/search/?q={company_name.replace(' ', '%20')}",
        "glassdoor_search": f"https://www.glassdoor.com/Search/results.htm?keyword={company_name.replace(' ', '%20')}",
        "blind_search": f"https://www.teamblind.com/search/{company_name.replace(' ', '%20')}",
        "risk_indicators": [],
        "manual_checks": [
            "Twitter: Search for company mentions, check ratio of negative replies",
            "Reddit: Search r/jobs, r/careerguidance for employee complaints",
            "Glassdoor: CEO approval, culture ratings, recent review trends",
            "Blind: Anonymous employee complaints (tech companies)",
            "TikTok: Search for employee videos exposing company",
            "LinkedIn: Employee growth/decline, recent layoffs"
        ]
    }
    return risk_data

def calculate_risk(findings):
    scores = {
        "Leadership": {"score": 15, "weight": 0.20, "factors": []},
        "Financial": {"score": 15, "weight": 0.20, "factors": []},
        "Legal": {"score": 15, "weight": 0.15, "factors": []},
        "Regulatory": {"score": 10, "weight": 0.10, "factors": []},
        "Reputational": {"score": 15, "weight": 0.15, "factors": []},
        "Political": {"score": 10, "weight": 0.10, "factors": []},
        "Operational": {"score": 10, "weight": 0.10, "factors": []}
    }
    red_flags = []
    
    court = findings.get("data_sources", {}).get("court_records", [])
    if isinstance(court, list) and len(court) > 0:
        count = len(court)
        if count > 5:
            scores["Legal"]["score"] = 85
            scores["Legal"]["factors"].append(f"{count} litigation matters - HIGH concern")
            red_flags.append({"severity": "HIGH", "category": "Legal", "finding": f"{count} litigation matters identified", "so_what": "Pattern of litigation indicates potential operational dysfunction, increases transaction risk, and may signal undisclosed liabilities. Budget 10-15% of deal value for legal contingencies.", "action": "Request full litigation schedule with status and exposure estimates"})
        elif count > 2:
            scores["Legal"]["score"] = 55
            scores["Legal"]["factors"].append(f"{count} litigation matters - moderate concern")
            red_flags.append({"severity": "MEDIUM", "category": "Legal", "finding": f"{count} litigation matters identified", "so_what": "Moderate litigation activity requires review to identify patterns and estimate exposure.", "action": "Review case details for materiality"})
        else:
            scores["Legal"]["score"] = 30
            scores["Legal"]["factors"].append(f"{count} litigation matter(s) - minor")
    
    fec = findings.get("data_sources", {}).get("fec_donations", {})
    if isinstance(fec, dict):
        amt = fec.get("total_amount", 0) or 0
        if amt > 500000:
            scores["Political"]["score"] = 80
            scores["Political"]["factors"].append(f"${amt:,.0f} political contributions - HIGH exposure")
            red_flags.append({"severity": "HIGH", "category": "Political", "finding": f"${amt:,.0f} in political contributions", "so_what": "Heavy political involvement creates regulatory risk under changing administrations. Government contracts, licenses, and regulatory approvals may be at risk. Potential reputational damage if contributions become public issue.", "action": "Map regulatory dependencies and assess administration change scenarios"})
        elif amt > 100000:
            scores["Political"]["score"] = 50
            scores["Political"]["factors"].append(f"${amt:,.0f} political contributions")
            red_flags.append({"severity": "MEDIUM", "category": "Political", "finding": f"${amt:,.0f} in political contributions", "so_what": "Moderate political activity may indicate regulatory relationships requiring monitoring.", "action": "Review recipient list for concentration risk"})
    
    news = findings.get("data_sources", {}).get("news_search", {})
    if isinstance(news, dict):
        adverse = news.get("adverse_media", [])
        if len(adverse) > 5:
            scores["Reputational"]["score"] = 85
            scores["Reputational"]["factors"].append(f"{len(adverse)} adverse media mentions - HIGH concern")
            red_flags.append({"severity": "HIGH", "category": "Reputational", "finding": f"{len(adverse)} adverse media mentions in past 12 months", "so_what": "Sustained negative media coverage indicates potential brand damage of 15-25%. One viral story could trigger customer/employee exodus. May affect ability to recruit talent and close B2B deals.", "action": "Commission brand sentiment analysis, review customer concentration risk"})
        elif len(adverse) > 2:
            scores["Reputational"]["score"] = 50
            scores["Reputational"]["factors"].append(f"{len(adverse)} adverse media mentions")
    
    sanctions = findings.get("data_sources", {}).get("sanctions", {})
    if sanctions.get("count", 0) > 0:
        scores["Regulatory"]["score"] = 100
        scores["Regulatory"]["factors"].append("SANCTIONS MATCH - CRITICAL")
        red_flags.append({"severity": "CRITICAL", "category": "Sanctions", "finding": "POTENTIAL MATCH ON GLOBAL SANCTIONS LIST", "so_what": "STOP ALL ACTIVITY. Proceeding with sanctioned entity creates criminal liability for all parties. Potential fines of $1M+ per violation, personal liability for executives, and reputational destruction.", "action": "IMMEDIATELY engage sanctions counsel. Do not proceed until cleared."})
    
    linkedin = findings.get("data_sources", {}).get("linkedin", {})
    if linkedin:
        headcount = linkedin.get("company_size_on_linkedin", 0)
        if headcount:
            scores["Operational"]["factors"].append(f"{headcount:,} employees on LinkedIn")
        
        follower_count = linkedin.get("follower_count", 0)
        if follower_count:
            scores["Reputational"]["factors"].append(f"{follower_count:,} LinkedIn followers")
    
    leadership = findings.get("data_sources", {}).get("leadership", {})
    if leadership and isinstance(leadership, dict):
        employees = leadership.get("employees", [])
        if employees:
            scores["Leadership"]["factors"].append(f"{len(employees)} executives identified on LinkedIn")
    
    weighted_score = sum(scores[cat]["score"] * scores[cat]["weight"] for cat in scores)
    
    return scores, weighted_score, red_flags

with st.sidebar:
    st.markdown("## 🕷️ BLACK WIDOW GLOBAL")
    st.caption("Corporate Intelligence Platform")
    st.markdown("---")
    target = st.text_input("🎯 Target Company/Person")
    search_type = st.radio("Type", ["Company", "Person"], horizontal=True)
    state = st.selectbox("State", ["", "DE", "NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "NJ", "MA", "VA", "WA", "CO", "AZ", "MI", "TN", "NV"])
    st.markdown("---")
    st.markdown("**Data Sources**")
    use_sec = st.checkbox("SEC EDGAR", value=True)
    use_court = st.checkbox("Court Records", value=True)
    use_fec = st.checkbox("FEC Political", value=True)
    use_news = st.checkbox("News/Media", value=True)
    use_sanctions = st.checkbox("Sanctions Lists", value=True)
    use_linkedin = st.checkbox("LinkedIn Intel", value=True)
    use_leadership = st.checkbox("Leadership Check", value=True)
    st.markdown("---")
    run = st.button("🔍 RUN INTELLIGENCE SEARCH", use_container_width=True, type="primary")
    st.markdown("---")
    st.caption("v2.1 | Black Widow Global")

if not run or not target:
    st.markdown("# 🕷️ BLACK WIDOW GLOBAL")
    st.markdown("### Corporate Intelligence & Investment Due Diligence")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**🔍 Deep OSINT**")
        st.caption("SEC, Courts, FEC, Global News, Sanctions")
    with col2:
        st.markdown("**👔 Leadership Intel**")
        st.caption("Executive backgrounds, LinkedIn, social media risk")
    with col3:
        st.markdown("**📊 Risk Matrix**")
        st.caption("7-category weighted scoring with dollar-impact analysis")
    with col4:
        st.markdown("**📋 Client Reports**")
        st.caption("Professional Word documents with recommendations")
    
    st.markdown("---")
    st.info("👈 Enter a target in the sidebar and click **RUN INTELLIGENCE SEARCH**")
    
    with st.expander("📖 Our Due Diligence Framework"):
        st.markdown("""
        | Category | Weight | What We Assess |
        |----------|--------|----------------|
        | **Leadership** | 20% | Executive backgrounds, turnover, legal history, social media behavior |
        | **Financial** | 20% | SEC filings, liens, credit indicators, hidden debt |
        | **Legal** | 15% | Litigation patterns, case types, exposure estimates |
        | **Operational** | 10% | Employee satisfaction, workforce stability, supply chain |
        | **Reputational** | 15% | Media sentiment, social media risk, brand strength |
        | **Political** | 10% | Donations, lobbying, regulatory relationships |
        | **Regulatory** | 10% | Sanctions, EPA, OSHA, industry compliance |
        """)

else:
    findings = {"target": target, "target_type": search_type.lower(), "data_sources": {}, "timestamp": datetime.now().isoformat()}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_steps = sum([use_sec, use_court, use_fec, use_news, use_sanctions, use_linkedin, use_leadership])
    current_step = 0
    
    if use_sec:
        status_text.text("🔍 Searching SEC EDGAR...")
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        try:
            findings["data_sources"]["sec_edgar"] = SECEdgarCollector().search_company(target) if search_type == "Company" else SECEdgarCollector().search_person(target)
        except Exception as e:
            findings["data_sources"]["sec_edgar"] = {"error": str(e)}
    
    if use_court:
        status_text.text("🔍 Searching Court Records...")
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        try:
            findings["data_sources"]["court_records"] = CourtRecordsCollector().search_company(target, state=state) if search_type == "Company" else CourtRecordsCollector().search_person(target, state=state)
        except Exception as e:
            findings["data_sources"]["court_records"] = {"error": str(e)}
    
    if use_fec:
        status_text.text("🔍 Searching FEC Political Donations...")
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        try:
            findings["data_sources"]["fec_donations"] = FECDonationsCollector().search_by_employer(target) if search_type == "Company" else FECDonationsCollector().search_donor(target, state=state)
        except Exception as e:
            findings["data_sources"]["fec_donations"] = {"error": str(e)}
    
    if use_news:
        status_text.text("🔍 Searching News & Media...")
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        try:
            findings["data_sources"]["news_search"] = NewsSearchCollector().search(target, days_back=365)
        except Exception as e:
            findings["data_sources"]["news_search"] = {"error": str(e)}
    
    if use_sanctions:
        status_text.text("🔍 Checking Global Sanctions Lists...")
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        findings["data_sources"]["sanctions"] = check_sanctions(target)
    
    if use_linkedin:
        status_text.text("🔍 Gathering LinkedIn Intelligence...")
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        findings["data_sources"]["linkedin"] = get_linkedin_company(target)
    
    if use_leadership:
        status_text.text("🔍 Researching Leadership Team...")
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        findings["data_sources"]["leadership"] = get_leadership_info(target)
    
    findings["data_sources"]["social_media"] = assess_social_media_risk(target)
    
    progress_bar.progress(1.0)
    status_text.text("✅ Intelligence gathering complete")
    
    scores, overall, red_flags = calculate_risk(findings)
    
    if overall >= 60:
        level = "HIGH RISK"
        level_color = "#dc2626"
        recommendation = "⛔ WALK AWAY or require significant risk mitigation and price adjustment"
        invest_signal = "DO NOT PROCEED"
    elif overall >= 40:
        level = "ELEVATED RISK"
        level_color = "#ea580c"
        recommendation = "⚠️ PROCEED WITH CAUTION - Enhanced due diligence required on flagged areas"
        invest_signal = "CONDITIONAL PROCEED"
    elif overall >= 25:
        level = "MODERATE RISK"
        level_color = "#ca8a04"
        recommendation = "📋 Standard due diligence sufficient with monitoring of noted concerns"
        invest_signal = "PROCEED WITH MONITORING"
    else:
        level = "LOW RISK"
        level_color = "#16a34a"
        recommendation = "✅ PROCEED - No significant concerns identified"
        invest_signal = "PROCEED"
    
    st.markdown(f"# 📋 Intelligence Dossier: {target}")
    st.caption(f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Black Widow Global")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Risk Score", f"{overall:.0f}/100")
    with col2:
        st.markdown(f"**Risk Level**")
        st.markdown(f"<span style='color:{level_color};font-size:1.5rem;font-weight:bold;'>{level}</span>", unsafe_allow_html=True)
    with col3:
        st.metric("Red Flags", len(red_flags))
    with col4:
        st.markdown(f"**Investment Signal**")
        st.markdown(f"<span style='color:{level_color};font-size:1.2rem;font-weight:bold;'>{invest_signal}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"### 📌 Recommendation")
    st.info(recommendation)
    
    if red_flags:
        st.markdown("### 🚨 Critical Findings")
        for flag in red_flags:
            severity_colors = {"CRITICAL": "#dc2626", "HIGH": "#dc2626", "MEDIUM": "#ea580c", "LOW": "#ca8a04"}
            color = severity_colors.get(flag["severity"], "#64748b")
            
            with st.expander(f"🔴 [{flag['severity']}] {flag['category']}: {flag['finding']}", expanded=True):
                st.markdown(f"**So What (Business Impact):**")
                st.warning(flag["so_what"])
                st.markdown(f"**Recommended Action:**")
                st.success(flag["action"])
    
    st.markdown("### 📊 Risk Matrix")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        categories = list(scores.keys())
        values = [scores[cat]["score"] for cat in categories]
        colors = ["#dc2626" if v >= 60 else "#ea580c" if v >= 40 else "#ca8a04" if v >= 25 else "#16a34a" for v in values]
        
        fig = go.Figure(go.Bar(
            y=categories,
            x=values,
            orientation='h',
            marker_color=colors,
            text=[f"{v}" for v in values],
            textposition='inside',
            textfont=dict(color='white', size=14)
        ))
        fig.add_vline(x=60, line_dash="dash", line_color="#dc2626", annotation_text="High", annotation_position="top")
        fig.add_vline(x=40, line_dash="dash", line_color="#ea580c", annotation_text="Elevated", annotation_position="top")
        fig.add_vline(x=25, line_dash="dash", line_color="#ca8a04", annotation_text="Moderate", annotation_position="top")
        fig.update_layout(xaxis_range=[0, 100], height=400, xaxis_title="Risk Score", yaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall,
            title={'text': "Overall Risk"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': level_color},
                'steps': [
                    {'range': [0, 25], 'color': "#dcfce7"},
                    {'range': [25, 40], 'color': "#fef9c3"},
                    {'range': [40, 60], 'color': "#fed7aa"},
                    {'range': [60, 100], 'color': "#fecaca"}
                ],
                'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': overall}
            }
        ))
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("### 🔍 Detailed Findings")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["⚖️ Legal", "💰 Financial", "🏛️ Political", "📰 Media", "👔 Leadership", "📱 Social Media"])
    
    with tab1:
        court = findings["data_sources"].get("court_records", [])
        if isinstance(court, list) and court:
            st.error(f"**{len(court)} litigation record(s) found**")
            for c in court[:15]:
                with st.container():
                    st.markdown(f"**{c.get('case_name', 'Unknown Case')}**")
                    st.caption(f"{c.get('court', 'Unknown Court')} | Filed: {c.get('date_filed', 'Unknown')}")
                    if c.get('url'):
                        st.markdown(f"[View Case]({c.get('url')})")
                    st.markdown("---")
        else:
            st.success("✅ No litigation found in searched databases")
    
    with tab2:
        sec = findings["data_sources"].get("sec_edgar", {})
        if isinstance(sec, dict):
            if sec.get("company_info"):
                info = sec["company_info"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Company Name", info.get("name", "N/A"))
                    st.metric("CIK", sec.get("cik", "N/A"))
                with col2:
                    st.metric("Industry (SIC)", info.get("sic_description", "N/A")[:30] if info.get("sic_description") else "N/A")
                    st.metric("State of Inc.", info.get("state_of_incorporation", "N/A"))
            
            filings = sec.get("filings", [])
            if filings:
                st.markdown("**Recent SEC Filings:**")
                for f in filings[:10]:
                    st.caption(f"{f.get('filing_date', 'N/A')} | {f.get('form_type', 'N/A')}: {f.get('description', '')[:50]}")
        else:
            st.info("No SEC data available")
    
    with tab3:
        fec = findings["data_sources"].get("fec_donations", {})
        if isinstance(fec, dict) and fec.get("total_amount"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Contributions", f"${fec.get('total_amount', 0):,.2f}")
            with col2:
                st.metric("Unique Donors", fec.get("unique_donors", 0))
            
            by_party = fec.get("contributions_by_party", {})
            if by_party:
                st.markdown("**Contributions by Party:**")
                for party, data in by_party.items():
                    if isinstance(data, dict):
                        st.write(f"- **{party}**: ${data.get('amount', 0):,.0f} ({data.get('count', 0)} contributions)")
            
            top_recipients = fec.get("top_recipients", [])
            if top_recipients:
                st.markdown("**Top Recipients:**")
                for r in top_recipients[:5]:
                    st.caption(f"{r.get('name', 'Unknown')}: ${r.get('total_amount', 0):,.0f}")
        else:
            st.info("No FEC contribution data found")
    
    with tab4:
        news = findings["data_sources"].get("news_search", {})
        if isinstance(news, dict):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Articles", news.get("total_articles", 0))
            with col2:
                st.metric("Adverse Mentions", len(news.get("adverse_media", [])))
            
            adverse = news.get("adverse_media", [])
            if adverse:
                st.error("**Adverse Media Identified:**")
                for a in adverse[:10]:
                    st.markdown(f"- [{a.get('title', 'Article')}]({a.get('url', '#')})")
                    st.caption(f"Source: {a.get('domain', 'Unknown')} | {a.get('date', '')}")
            else:
                st.success("✅ No adverse media identified in past 12 months")
        else:
            st.info("No news data available")
    
    with tab5:
        linkedin = findings["data_sources"].get("linkedin")
        leadership = findings["data_sources"].get("leadership")
        
        if linkedin:
            st.markdown("**Company LinkedIn Profile:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Employees", f"{linkedin.get('company_size_on_linkedin', 'N/A'):,}" if isinstance(linkedin.get('company_size_on_linkedin'), int) else "N/A")
            with col2:
                st.metric("Followers", f"{linkedin.get('follower_count', 'N/A'):,}" if isinstance(linkedin.get('follower_count'), int) else "N/A")
            with col3:
                st.metric("Founded", linkedin.get("founded_year", "N/A"))
            
            if linkedin.get("description"):
                st.markdown("**Description:**")
                st.caption(linkedin.get("description", "")[:500])
        
        if leadership and isinstance(leadership, dict) and leadership.get("employees"):
            st.markdown("**Leadership Team Identified:**")
            for emp in leadership.get("employees", [])[:10]:
                st.markdown(f"- **{emp.get('name', 'Unknown')}** - {emp.get('title', 'Unknown Title')}")
        else:
            st.markdown("**Manual Leadership Research Required:**")
            st.markdown(f"- [Search LinkedIn](https://www.linkedin.com/search/results/people/?keywords={target.replace(' ', '%20')}%20CEO%20OR%20CFO%20OR%20COO)")
            st.markdown(f"- [Search SEC for Insiders](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={target.replace(' ', '+')}&type=4)")
    
    with tab6:
        social = findings["data_sources"].get("social_media", {})
        st.markdown("**Social Media Risk Assessment**")
        st.warning("Manual review required for comprehensive social media risk analysis")
        
        st.markdown("**Quick Search Links:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"🐦 [Twitter/X Search]({social.get('twitter_search', '#')})")
            st.markdown(f"👥 [Reddit Search]({social.get('reddit_search', '#')})")
            st.markdown(f"🏢 [Glassdoor]({social.get('glassdoor_search', '#')})")
        with col2:
            st.markdown(f"👁️ [Blind (Anonymous)]({social.get('blind_search', '#')})")
            st.markdown(f"💼 [LinkedIn](https://linkedin.com/company/{target.lower().replace(' ', '-')})")
        
        st.markdown("**What to Look For:**")
        for check in social.get("manual_checks", []):
            st.caption(f"• {check}")
    
    st.markdown("---")
    st.markdown("### 📥 Export Report")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Generate Word Report", use_container_width=True):
            findings["summary"] = {
                "risk_assessment": {"level": level, "score": overall, "recommendation": recommendation, "invest_signal": invest_signal},
                "risk_scores": {k: v["score"] for k, v in scores.items()},
                "red_flags_count": len(red_flags),
                "red_flags": red_flags
            }
            try:
                gen = ReportGenerator()
                path = gen.generate_text_report(findings, "")
                st.success(f"✅ Report saved to Desktop/OSINT_Reports/")
            except Exception as e:
                st.error(f"Error generating report: {e}")
    
    with col2:
        if st.button("📊 Download JSON Data", use_container_width=True):
            st.download_button(
                label="Download",
                data=json.dumps(findings, indent=2, default=str),
                file_name=f"{target.replace(' ', '_')}_intel_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
