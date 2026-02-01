import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
sys.path.insert(0, ".")
from modules.sec_edgar import SECEdgarCollector
from modules.fec_donations import FECDonationsCollector
from modules.court_records import CourtRecordsCollector
from modules.news_search import NewsSearchCollector
from modules.report_generator import ReportGenerator

# Page config
st.set_page_config(page_title="Black Widow Global", page_icon="🕷️", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main-header { font-size: 2.8rem; font-weight: 700; background: linear-gradient(90deg, #1B4F72, #2E86AB); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0; }
.sub-header { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem; }
.risk-high { background: #FDEDEC; border-left: 4px solid #E74C3C; padding: 1rem; border-radius: 5px; }
.risk-medium { background: #FEF9E7; border-left: 4px solid #F39C12; padding: 1rem; border-radius: 5px; }
.risk-low { background: #EAFAF1; border-left: 4px solid #27AE60; padding: 1rem; border-radius: 5px; }
.metric-container { background: #f8f9fa; border-radius: 10px; padding: 1.5rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.metric-value { font-size: 2.5rem; font-weight: 700; color: #1B4F72; }
.metric-label { font-size: 0.9rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
.stButton>button { background: linear-gradient(90deg, #1B4F72, #2E86AB); color: white; font-weight: 600; padding: 0.75rem 2rem; border-radius: 8px; border: none; width: 100%; }
.stButton>button:hover { background: linear-gradient(90deg, #2E86AB, #3498DB); }
div[data-testid="stSidebar"] { background: linear-gradient(180deg, #1B4F72 0%, #154360 100%); }
div[data-testid="stSidebar"] .stMarkdown { color: white; }
div[data-testid="stSidebar"] label { color: white !important; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🕷️ BLACK WIDOW")
    st.markdown("##### Intelligence Platform")
    st.markdown("---")
    target = st.text_input("🎯 Target Name", placeholder="Company or Person")
    search_type = st.radio("📋 Search Type", ["Company", "Person"], horizontal=True)
    state = st.selectbox("📍 State", ["", "DE", "NY", "CA", "TX", "FL", "IL", "NV", "WA", "PA", "GA", "NC", "NJ", "VA", "MA", "AZ", "CO", "OH"])
    st.markdown("---")
    run_search = st.button("🔍 RUN INTELLIGENCE SEARCH", use_container_width=True)
    st.markdown("---")
    st.markdown("##### Data Sources")
    st.markdown("✅ SEC EDGAR\n✅ FEC Political\n✅ Court Records\n✅ News Media\n✅ UCC Filings")
    st.markdown("---")
    st.markdown("##### v1.0 | Black Widow Global")

# Main content
if not run_search or not target:
    st.markdown('<p class="main-header">🕷️ BLACK WIDOW GLOBAL</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Corporate Intelligence & Investigative Due Diligence</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔍 Deep Research")
        st.markdown("Access SEC filings, court records, political donations, and global news in one search.")
    with col2:
        st.markdown("### 📊 Risk Analysis")
        st.markdown("Visual risk matrix across Legal, Financial, Regulatory, Reputational, and Political categories.")
    with col3:
        st.markdown("### 📋 Professional Reports")
        st.markdown("Generate client-ready Word documents with executive summaries and recommendations.")
    
    st.markdown("---")
    st.info("👈 Enter a target name in the sidebar and click **RUN INTELLIGENCE SEARCH** to begin.")

else:
    # Run search
    findings = {"target": target, "target_type": search_type.lower(), "data_sources": {}, "red_flags": [], "related_entities": []}
    
    progress = st.progress(0)
    status = st.empty()
    
    status.info("🔍 Searching SEC EDGAR...")
    progress.progress(20)
    try:
        sec = SECEdgarCollector()
        findings["data_sources"]["sec_edgar"] = sec.search_company(target) if search_type == "Company" else sec.search_person(target)
    except Exception as e:
        findings["data_sources"]["sec_edgar"] = {"error": str(e)}
    
    status.info("🔍 Searching FEC Political Donations...")
    progress.progress(40)
    try:
        fec = FECDonationsCollector()
        findings["data_sources"]["fec_donations"] = fec.search_by_employer(target) if search_type == "Company" else fec.search_donor(target, state=state)
    except Exception as e:
        findings["data_sources"]["fec_donations"] = {"error": str(e)}
    
    status.info("🔍 Searching Court Records...")
    progress.progress(60)
    try:
        court = CourtRecordsCollector()
        findings["data_sources"]["court_records"] = court.search_company(target, state=state) if search_type == "Company" else court.search_person(target, state=state)
    except Exception as e:
        findings["data_sources"]["court_records"] = {"error": str(e)}
    
    status.info("🔍 Searching News & Media...")
    progress.progress(80)
    try:
        news = NewsSearchCollector()
        findings["data_sources"]["news_search"] = news.search(target, days_back=365)
    except Exception as e:
        findings["data_sources"]["news_search"] = {"error": str(e)}
    
    progress.progress(100)
    status.success("✅ Intelligence search complete!")
    
    # Calculate risk scores
    scores = {"Legal": 15, "Financial": 10, "Regulatory": 10, "Reputational": 15, "Political": 10, "Operational": 5}
    
    court_data = findings["data_sources"].get("court_records", [])
    if isinstance(court_data, list):
        scores["Legal"] = min(len(court_data) * 18, 100)
    
    fec_data = findings["data_sources"].get("fec_donations", {})
    if isinstance(fec_data, dict):
        amt = fec_data.get("total_amount", 0) or 0
        if amt > 100000:
            scores["Political"] = 70
        elif amt > 50000:
            scores["Political"] = 50
        elif amt > 10000:
            scores["Political"] = 30
    
    news_data = findings["data_sources"].get("news_search", {})
    if isinstance(news_data, dict):
        adverse = len(news_data.get("adverse_media", []))
        scores["Reputational"] = min(adverse * 12, 100)
    
    overall = sum(scores.values()) / len(scores)
    risk_level = "HIGH RISK" if overall >= 50 else "MODERATE RISK" if overall >= 30 else "LOW RISK"
    risk_color = "risk-high" if overall >= 50 else "risk-medium" if overall >= 30 else "risk-low"
    
    # Display header
    st.markdown(f"## 📋 Intelligence Dossier: {target}")
    st.markdown(f"*Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    
    # Executive Summary
    st.markdown("### Executive Summary")
    summary_text = f"**{target}** has been assessed as **{risk_level}** with an overall risk score of **{overall:.0f}/100**. "
    if scores["Legal"] > 40:
        summary_text += f"Elevated legal risk detected ({scores['Legal']}/100) based on litigation history. "
    if scores["Political"] > 40:
        summary_text += f"Significant political exposure identified ({scores['Political']}/100). "
    if scores["Reputational"] > 40:
        summary_text += f"Adverse media coverage warrants attention ({scores['Reputational']}/100). "
    
    st.markdown(f'<div class="{risk_color}">{summary_text}</div>', unsafe_allow_html=True)
    
    # Metrics
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-value">{overall:.0f}</div><div class="metric-label">Risk Score</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><div class="metric-value">{risk_level.split()[0]}</div><div class="metric-label">Risk Level</div></div>', unsafe_allow_html=True)
    with col3:
        court_count = len(court_data) if isinstance(court_data, list) else 0
        st.markdown(f'<div class="metric-container"><div class="metric-value">{court_count}</div><div class="metric-label">Legal Matters</div></div>', unsafe_allow_html=True)
    with col4:
        fec_amt = fec_data.get("total_amount", 0) if isinstance(fec_data, dict) else 0
        st.markdown(f'<div class="metric-container"><div class="metric-value">${fec_amt/1000:.0f}K</div><div class="metric-label">Political $</div></div>', unsafe_allow_html=True)
    
    # Charts
    st.markdown("### Risk Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        colors = ["#E74C3C" if v >= 50 else "#F39C12" if v >= 30 else "#27AE60" for v in scores.values()]
        fig = go.Figure(data=[go.Bar(x=list(scores.keys()), y=list(scores.values()), marker_color=colors, text=list(scores.values()), textposition="outside")])
        fig.update_layout(title="Risk by Category", yaxis_range=[0, 100], yaxis_title="Score", showlegend=False, height=400)
        fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="High")
        fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="Medium")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig2 = go.Figure(data=go.Scatterpolar(r=list(scores.values()) + [list(scores.values())[0]], theta=list(scores.keys()) + [list(scores.keys())[0]], fill="toself", fillcolor="rgba(43, 108, 176, 0.3)", line=dict(color="#2B6CB0", width=2)))
        fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, title="Risk Profile", height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed tabs
    st.markdown("### Detailed Findings")
    tab1, tab2, tab3, tab4 = st.tabs(["⚖️ Legal", "💰 Political", "📰 Media", "🏢 Corporate"])
    
    with tab1:
        if isinstance(court_data, list) and court_data:
            for case in court_data[:10]:
                st.markdown(f"**{case.get('case_name', 'Unknown Case')}**")
                st.caption(f"{case.get('court', 'Unknown Court')} | {case.get('date_filed', 'Unknown Date')}")
                if case.get("url"):
                    st.markdown(f"[View Case]({case.get('url')})")
                st.markdown("---")
        else:
            st.success("No significant litigation found.")
    
    with tab2:
        if isinstance(fec_data, dict) and fec_data.get("total_amount"):
            st.metric("Total Contributions", f"${fec_data.get('total_amount', 0):,.2f}")
            st.metric("Unique Donors", fec_data.get("unique_donors", 0))
            by_party = fec_data.get("contributions_by_party", {})
            if by_party:
                st.markdown("**By Party:**")
                for party, data in by_party.items():
                    if isinstance(data, dict):
                        st.write(f"- {party}: ${data.get('amount', 0):,.2f}")
        else:
            st.info("No political contribution data found.")
    
    with tab3:
        if isinstance(news_data, dict):
            total = news_data.get("total_articles", 0)
            adverse = news_data.get("adverse_media", [])
            st.metric("Total Articles", total)
            if adverse:
                st.error(f"⚠️ {len(adverse)} adverse media mentions found")
                for article in adverse[:5]:
                    st.markdown(f"- [{article.get('title', 'Article')}]({article.get('url', '#')})")
            else:
                st.success("No adverse media identified.")
        else:
            st.info("No news data available.")
    
    with tab4:
        sec_data = findings["data_sources"].get("sec_edgar", {})
        if isinstance(sec_data, dict) and sec_data.get("company_info"):
            info = sec_data["company_info"]
            st.write(f"**Name:** {info.get('name', 'N/A')}")
            st.write(f"**CIK:** {sec_data.get('cik', 'N/A')}")
            st.write(f"**SIC:** {info.get('sic_description', 'N/A')}")
            st.write(f"**State:** {info.get('state_of_incorporation', 'N/A')}")
        else:
            st.info("No SEC data available.")
    
    # Export
    st.markdown("### Export Report")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Generate Word Report", use_container_width=True):
            findings["summary"] = {"risk_assessment": {"level": risk_level, "score": overall, "recommendation": "Review detailed findings."}, "total_data_sources_queried": 4, "successful_queries": 4, "red_flags_count": 0, "related_entities_found": 0}
            gen = ReportGenerator()
            path = gen.generate_text_report(findings, "")
            st.success(f"Report saved to Desktop/OSINT_Reports!")
    with col2:
        if st.button("📊 Export Data (JSON)", use_container_width=True):
            st.download_button("Download JSON", data=str(findings), file_name=f"{target.replace(' ', '_')}_intel.json", mime="application/json")
