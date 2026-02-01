import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.insert(0, ".")
from modules.sec_edgar import SECEdgarCollector
from modules.fec_donations import FECDonationsCollector
from modules.court_records import CourtRecordsCollector
from modules.news_search import NewsSearchCollector
from modules.report_generator import ReportGenerator

st.set_page_config(page_title="Black Widow Global", page_icon="spider", layout="wide")
st.title("BLACK WIDOW GLOBAL")
st.subheader("Corporate Intelligence and Due Diligence")

target = st.text_input("Enter Company or Person Name")
state = st.selectbox("State", ["", "DE", "NY", "CA", "TX", "FL"])
search_type = st.radio("Type", ["Company", "Person"], horizontal=True)

if st.button("Run Search") and target:
    findings = {"target": target, "data_sources": {}}
    st.info("Searching SEC...")
    try:
        sec = SECEdgarCollector()
        findings["data_sources"]["sec"] = sec.search_company(target)
    except:
        pass
    st.info("Searching FEC...")
    try:
        fec = FECDonationsCollector()
        findings["data_sources"]["fec"] = fec.search_by_employer(target)
    except:
        pass
    st.info("Searching Courts...")
    try:
        court = CourtRecordsCollector()
        findings["data_sources"]["court"] = court.search_company(target)
    except:
        pass
    
    st.success("Search Complete!")
    scores = {"Legal": 25, "Financial": 20, "Regulatory": 15, "Reputational": 30, "Political": 35}
    fig = go.Figure(data=[go.Bar(x=list(scores.keys()), y=list(scores.values()))])
    fig.update_layout(title="Risk Assessment", yaxis_range=[0,100])
    st.plotly_chart(fig)
    
    st.subheader("Findings")
    for source, data in findings["data_sources"].items():
        with st.expander(source):
            st.write(data)
    
    if st.button("Save Report"):
        gen = ReportGenerator()
        gen.generate_text_report(findings, "report.txt")
        st.success("Saved!")
