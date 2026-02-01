"""
Report Generator - Creates Word document reports
"""

import os
from datetime import datetime
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class ReportGenerator:
    def __init__(self):
        self.report_date = datetime.now().strftime('%Y-%m-%d')
        self.output_dir = os.path.expanduser('~/Desktop/OSINT_Reports')
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_text_report(self, findings, output_path):
        """Generate Word document report"""
        target = findings.get('target', 'Unknown')
        target_type = findings.get('target_type', 'company')
        summary = findings.get('summary', {})
        risk = summary.get('risk_assessment', {})
        
        if DOCX_AVAILABLE:
            return self._generate_docx(findings, target)
        else:
            return self._generate_txt(findings, output_path)
    
    def _generate_docx(self, findings, target):
        """Generate a Word document"""
        doc = Document()
        
        target_type = findings.get('target_type', 'company')
        summary = findings.get('summary', {})
        risk = summary.get('risk_assessment', {})
        
        # Title
        title = doc.add_heading('BLACK WIDOW GLOBAL', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading('INTELLIGENCE DOSSIER', level=1)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        
        # Subject info
        doc.add_heading('Subject Information', level=2)
        doc.add_paragraph(f"Target: {target}")
        doc.add_paragraph(f"Type: {target_type.title()}")
        doc.add_paragraph(f"Report Date: {self.report_date}")
        
        # Risk Assessment
        doc.add_heading('Risk Assessment', level=2)
        doc.add_paragraph(f"Risk Level: {risk.get('level', 'UNKNOWN')}")
        doc.add_paragraph(f"Risk Score: {risk.get('score', 0)}/100")
        doc.add_paragraph(f"Recommendation: {risk.get('recommendation', 'N/A')}")
        
        # Executive Summary
        doc.add_heading('Executive Summary', level=2)
        doc.add_paragraph(f"Data sources queried: {summary.get('total_data_sources_queried', 0)}")
        doc.add_paragraph(f"Successful queries: {summary.get('successful_queries', 0)}")
        doc.add_paragraph(f"Related entities identified: {summary.get('related_entities_found', 0)}")
        doc.add_paragraph(f"Red flags identified: {summary.get('red_flags_count', 0)}")
        
        # Red Flags
        red_flags = findings.get('red_flags', [])
        doc.add_heading('Red Flags', level=2)
        if red_flags:
            for flag in red_flags:
                doc.add_paragraph(f"[{flag.get('severity', 'MEDIUM')}] {flag.get('category', 'General')}: {flag.get('description', '')}")
        else:
            doc.add_paragraph("No significant red flags identified.")
        
        # Related Entities
        related = findings.get('related_entities', [])
        doc.add_heading('Related Entities & Connections', level=2)
        if related:
            for rel in related:
                doc.add_paragraph(f"{rel.get('type', 'Connection')}: {rel.get('description', '')}")
        else:
            doc.add_paragraph("No significant connections identified.")
        
        # Data Sources
        doc.add_heading('Data Sources Consulted', level=2)
        for source, data in findings.get('data_sources', {}).items():
            if isinstance(data, dict) and 'error' in data:
                doc.add_paragraph(f"{source}: Error - {data['error']}")
            elif isinstance(data, list):
                doc.add_paragraph(f"{source}: {len(data)} records")
            else:
                doc.add_paragraph(f"{source}: Data retrieved")
        
        # Confidential notice
        doc.add_paragraph()
        notice = doc.add_paragraph("CONFIDENTIAL - FOR AUTHORIZED USE ONLY")
        notice.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Save to Desktop
        safe_name = target.replace(' ', '_').replace(',', '')[:30]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_{timestamp}.docx"
        filepath = os.path.join(self.output_dir, filename)
        doc.save(filepath)
        
        print(f"\n[+] Word report saved: {filepath}")
        return filepath
    
    def _generate_txt(self, findings, output_path):
        """Fallback to text if docx not available"""
        target = findings.get('target', 'Unknown')
        summary = findings.get('summary', {})
        risk = summary.get('risk_assessment', {})
        
        lines = []
        lines.append("=" * 70)
        lines.append("BLACK WIDOW GLOBAL - INTELLIGENCE DOSSIER")
        lines.append("=" * 70)
        lines.append(f"Subject: {target}")
        lines.append(f"Risk Level: {risk.get('level', 'UNKNOWN')}")
        lines.append(f"Risk Score: {risk.get('score', 0)}/100")
        lines.append("=" * 70)
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        return output_path
