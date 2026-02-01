import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import sys
sys.path.insert(0, ".")
from modules.sec_edgar import SECEdgarCollector
from modules.fec_donations import FECDonationsCollector
from modules.court_records import CourtRecordsCollector
from modules.news_search import NewsSearchCollector
from modules.report_generator import ReportGenerator

st.set_page_config(page_title="Black Widow Global", page_icon="🕷️", layout="wide")

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
.main-header { font-size: 2.5rem; font-weight: 700; color: #1a1a2e; text-align: center; }
.risk-badge-high { background: #dc3545; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
.risk-badge-med { background: #ffc107; color: black; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
.risk-badge-low { background: #28a745; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def check_ofac_sanctions(name):
    """Check OFAC sanctions list"""
    try:
        url = f"https://api.opensanctions.org/match/default?schema=Company&properties.name={name}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"matches": data.get("results", []), "count": len(data.get("results", []))}
    except:
        pass
    return {"matches": [], "count": 0}

def get_glassdoor_info(company):
    """Get Glassdoor-style data (simulated for now - real API requires partnership)"""
    # Note: Real Glassdoor API requires business partnership
    # This provides guidance for manual lookup
    return {
        "search_url": f"https://www.glassdoor.com/Search/results.htm?keyword={company.replace(' ', '%20')}",
        "what_to_check": ["Overall rating", "CEO approval", "Recommend to friend %", "Recent review sentiment"],
        "status": "manual_search"
    }

def create_risk_heatmap(scores):
    """Create a red/yellow/green risk heatmap"""
    categories = list(scores.keys())
    values = list(scores.values())
    
    # Create color scale: green (0) -> yellow (50) -> red (100)
    colors = []
    for v in values:
        if v >= 60:
            colors.append("#dc3545")  # Red
        elif v >= 35:
            colors.append("#ffc107")  # Yellow
        else:
            colors.append("#28a745")  # Green
    
    fig = go.Figure()
    
    # Add horizontal bar chart (easier to read)
    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='#333', width=1)
        ),
        text=[f"{v}" for v in values],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Arial Black')
    ))
    
    # Add threshold lines
    fig.add_vline(x=60, line_dash="dash", line_color="red", line_width=2, annotation_text="HIGH", annotation_position="top")
    fig.add_vline(x=35, line_dash="dash", line_color="orange", line_width=2, annotation_text="MED", annotation_position="top")
    
    fig.update_layout(
        title=dict(text="RISK ASSESSMENT MATRIX", font=dict(size=20, color="#1a1a2e")),
        xaxis=dict(title="Risk Score", range=[0, 100], gridcolor='#eee'),
        yaxis=dict(title=""),
        height=400,
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Inter", size=12)
    )
    
    return fig

def create_risk_gauge(score):
    """Create a gauge chart for overall risk"""
    if score >= 60:
        color = "#dc3545"
        level = "HIGH RISK"
    elif score >= 35:
        color = "#ffc107"
        level = "MODERATE"
    else:
        color = "#28a745"
        level = "LOW RISK"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={'text': f"Overall Risk<br><span style='font-size:0.8em;color:{color}'>{level}</span>"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'steps': [
                {'range': [0, 35], 'color': '#d4edda'},
                {'range': [35, 60], 'color': '#fff3cd'},
                {'range': [60, 100], 'color': '#f8d7da'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(height=300, font=dict(family="Inter"))
    return fig

def create_risk_matrix_grid(scores):
    """Create a proper risk matrix grid (Impact vs Likelihood style)"""
    import numpy as np
    
    # Create matrix data
    categories = list(scores.keys())
    n = len(categories)
    
    # Map scores to a grid (simplified 3x3 for visual clarity)
    z_data = []
    for score in scores.values():
        if score >= 60:
            z_data.append([0, 0, 1])  # High
        elif score >= 35:
            z_data.append([0, 1, 0])  # Medium
        else:
            z_data.append([1, 0, 0])  # Low
    
    # Create a simpler heatmap showing score intensity
    z = [[scores[cat]] for cat in categories]
    
    fig = go.Figure(data=go.Heatmap(
        z=[[s] for s in scores.values()],
        x=['Risk Level'],
        y=categories,
        colorscale=[
            [0, '#28a745'],      # Green at 0
            [0.35, '#28a745'],   # Green to 35
            [0.35, '#ffc107'],   # Yellow at 35
            [0.60, '#ffc107'],   # Yellow to 60
            [0.60, '#dc3545'],   # Red at 60
            [1.0, '#dc3545']     # Red to 100
        ],
        zmin=0,
        zmax=100,
        text=[[f"{s}"] for s in scores.values()],
        texttemplate="%{text}",
        textfont={"size": 16, "color": "white"},
        showscale=True,
        colorbar=dict(title="Score", tickvals=[0, 35, 60, 100], ticktext=["Low", "Med", "High", "Critical"])
    ))
    
    fig.update_layout(
        title="Risk Heat Map",
        height=400,
        font=dict(family="Inter")
    )
    
    return fig

# Sidebar
with st.sidebar:
    st.markdown("## 🕷️ BLACK WIDOW GLOBAL")
    st.caption("Corporate Intelligence Platform")
    st.markdown("---")
    
    target = st.text_input("🎯 Target Name", placeholder="Enter company or person")
    search_type = st.radio("Type", ["Company", "Person"], horizontal=True)
    state = st.selectbox("State", ["", "DE", "NY", "CA", "TX", "FL", "IL", "NV", "WA", "PA", "GA", "NC", "NJ", "VA", "MA", "AZ", "CO", "OH", "MI", "TN"])
    
    st.markdown("---")
    st.markdown("**Data Sources**")
    use_sec = st.checkbox("SEC EDGAR", value=True)
    use_fec = st.checkbox("FEC Political", value=True)
    use_court = st.checkbox("Court Records", value=True)
    use_news = st.checkbox("News/Media", value=True)
    use_sanctions = st.checkbox("OFAC/Sanctions", value=True)
    use_glassdoor = st.checkbox("Glassdoor (manual)", value=False)
    
    st.markdown("---")
    run_search = st.button("🔍 RUN SEARCH", use_container_width=True, type="primary")

# Main
if not run_search or not target:
    st.markdown('<h1 class="main-header">🕷️ BLACK WIDOW GLOBAL</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#666;'>Corporate Intelligence & Investigative Due Diligence</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 🔍")
        st.markdown("**Deep OSINT**")
        st.caption("SEC, Courts, FEC, News")
    with col2:
        st.markdown("### 🎯")
        st.markdown("**Risk Scoring**")
        st.caption("6-Category Matrix")
    with col3:
        st.markdown("### 🚨")
        st.markdown("**Sanctions**")
        st.caption("OFAC & Global Lists")
    with col4:
        st.markdown("### 📊")
        st.markdown("**Reports**")
        st.caption("Word & PDF Export")
    
    st.markdown("---")
    st.info("👈 Enter a target and click **RUN SEARCH**")

else:
    findings = {"target": target, "target_type": search_type.lower(), "data_sources": {}, "red_flags": []}
    
    progress = st.progress(0)
    status = st.empty()
    step = 0
    total_steps = sum([use_sec, use_fec, use_court, use_news, use_sanctions, use_glassdoor])
    
    if use_sec:
        status.info("🔍 SEC EDGAR...")
        step += 1
        progress.progress(step / total_steps)
        try:
            sec = SECEdgarCollector()
            findings["data_sources"]["sec_edgar"] = sec.search_company(target) if search_type == "Company" else sec.search_person(target)
        except Exception as e:
            findings["data_sources"]["sec_edgar"] = {"error": str(e)}
    
    if use_fec:
        status.info("🔍 FEC Political Donations...")
        step += 1
        progress.progress(step / total_steps)
        try:
            fec = FECDonationsCollector()
            findings["data_sources"]["fec_donations"] = fec.search_by_employer(target) if search_type == "Company" else fec.search_donor(target, state=state)
        except Exception as e:
            findings["data_sources"]["fec_donations"] = {"error": str(e)}
    
    if use_court:
        status.info("🔍 Court Records...")
        step += 1
        progress.progress(step / total_steps)
        try:
            court = CourtRecordsCollector()
            findings["data_sources"]["court_records"] = court.search_company(target, state=state) if search_type == "Company" else court.search_person(target, state=state)
        except Exception as e:
            findings["data_sources"]["court_records"] = {"error": str(e)}
    
    if use_news:
        status.info("🔍 News & Media...")
        step += 1
        progress.progress(step / total_steps)
        try:
            news = NewsSearchCollector()
            findings["data_sources"]["news_search"] = news.search(target, days_back=365)
        except Exception as e:
            findings["data_sources"]["news_search"] = {"error": str(e)}
    
    if use_sanctions:
        status.info("🔍 OFAC & Sanctions...")
        step += 1
        progress.progress(step / total_steps)
        findings["data_sources"]["sanctions"] = check_ofac_sanctions(target)
    
    if use_glassdoor:
        status.info("🔍 Glassdoor lookup...")
        step += 1
        progress.progress(step / total_steps)
        findings["data_sources"]["glassdoor"] = get_glassdoor_info(target)
    
    progress.progress(1.0)
    status.success("✅ Search complete!")
    
    # Calculate risk scores
    scores = {"Legal": 10, "Financial": 10, "Regulatory": 10, "Reputational": 10, "Political": 10, "Sanctions": 5}
    
    court_data = findings["data_sources"].get("court_records", [])
    if isinstance(court_data, list):
        scores["Legal"] = min(len(court_data) * 20, 100)
        if scores["Legal"] > 50:
            findings["red_flags"].append({"severity": "HIGH", "category": "Legal", "description": f"{len(court_data)} litigation matters found"})
    
    fec_data = findings["data_sources"].get("fec_donations", {})
    if isinstance(fec_data, dict):
        amt = fec_data.get("total_amount", 0) or 0
        if amt > 100000:
            scores["Political"] = 70
            findings["red_flags"].append({"severity": "MEDIUM", "category": "Political", "description": f"${amt:,.0f} in political contributions"})
        elif amt > 50000:
            scores["Political"] = 45
        elif amt > 10000:
            scores["Political"] = 25
    
    news_data = findings["data_sources"].get("news_search", {})
    if isinstance(news_data, dict):
        adverse = len(news_data.get("adverse_media", []))
        scores["Reputational"] = min(adverse * 15, 100)
        if adverse > 3:
            findings["red_flags"].append({"severity": "HIGH", "category": "Reputational", "description": f"{adverse} adverse media mentions"})
    
    sanctions_data = findings["data_sources"].get("sanctions", {})
    if sanctions_data.get("count", 0) > 0:
        scores["Sanctions"] = 95
        findings["red_flags"].append({"severity": "CRITICAL", "category": "Sanctions", "description": "POTENTIAL SANCTIONS MATCH - VERIFY IMMEDIATELY"})
    
    overall = sum(scores.values()) / len(scores)
    
    # Display
    st.markdown(f"## 📋 Intelligence Dossier: {target}")
    
    # Risk badges
    if overall >= 60:
        st.markdown(f'<span class="risk-badge-high">HIGH RISK - {overall:.0f}/100</span>', unsafe_allow_html=True)
    elif overall >= 35:
        st.markdown(f'<span class="risk-badge-med">MODERATE RISK - {overall:.0f}/100</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="risk-badge-low">LOW RISK - {overall:.0f}/100</span>', unsafe_allow_html=True)
    
    # Red flags alert
    if findings["red_flags"]:
        st.error(f"⚠️ {len(findings['red_flags'])} RED FLAG(S) IDENTIFIED")
        for flag in findings["red_flags"]:
            st.warning(f"**[{flag['severity']}]** {flag['category']}: {flag['description']}")
    
    # Charts
    st.markdown("### Risk Analysis")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(create_risk_heatmap(scores), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_risk_gauge(overall), use_container_width=True)
    
    # Detailed findings
    st.markdown("### Detailed Findings")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚖️ Legal", "💰 Political", "📰 Media", "🚨 Sanctions", "🏢 Corporate"])
    
    with tab1:
        if isinstance(court_data, list) and court_data:
            st.error(f"Found {len(court_data)} court record(s)")
            for case in court_data[:10]:
                st.markdown(f"**{case.get('case_name', 'Unknown')}**")
                st.caption(f"{case.get('court', '')} | {case.get('date_filed', '')}")
        else:
            st.success("✅ No litigation found")
    
    with tab2:
        if isinstance(fec_data, dict) and fec_data.get("total_amount"):
            st.metric("Total Contributions", f"${fec_data.get('total_amount', 0):,.2f}")
            by_party = fec_data.get("contributions_by_party", {})
            if by_party:
                for party, data in by_party.items():
                    if isinstance(data, dict):
                        st.write(f"**{party}**: ${data.get('amount', 0):,.0f}")
        else:
            st.info("No FEC data found")
    
    with tab3:
        if isinstance(news_data, dict):
            adverse = news_data.get("adverse_media", [])
            if adverse:
                st.error(f"⚠️ {len(adverse)} adverse mentions")
                for a in adverse[:5]:
                    st.markdown(f"- {a.get('title', 'Article')}")
            else:
                st.success("✅ No adverse media")
        else:
            st.info("No news data")
    
    with tab4:
        if sanctions_data.get("count", 0) > 0:
            st.error("🚨 POTENTIAL SANCTIONS MATCH")
            st.json(sanctions_data.get("matches", []))
        else:
            st.success("✅ No sanctions matches found")
    
    with tab5:
        sec_data = findings["data_sources"].get("sec_edgar", {})
        if isinstance(sec_data, dict) and sec_data.get("company_info"):
            st.json(sec_data["company_info"])
        else:
            st.info("No SEC data")
        
        if use_glassdoor:
            gd = findings["data_sources"].get("glassdoor", {})
            st.markdown("**Glassdoor (Manual Search)**")
            st.markdown(f"[Search Glassdoor]({gd.get('search_url', '#')})")
    
    # Export
    st.markdown("---")
    if st.button("📄 Save Report to Desktop", use_container_width=True):
        findings["summary"] = {"risk_assessment": {"level": "HIGH" if overall >= 60 else "MODERATE" if overall >= 35 else "LOW", "score": overall}, "red_flags_count": len(findings["red_flags"])}
        gen = ReportGenerator()
        path = gen.generate_text_report(findings, "")
        st.success("✅ Report saved to Desktop/OSINT_Reports/")
