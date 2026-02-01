from typing import Dict, List
from collections import defaultdict

class EntityResolver:
    def __init__(self):
        self.connections = []
    def find_connections(self, findings: Dict) -> List[Dict]:
        connections = []
        fec_data = findings.get("data_sources", {}).get("fec_donations", {})
        if isinstance(fec_data, dict) and fec_data.get("total_amount", 0) > 50000:
            connections.append({"type": "political_donor", "description": "Significant political contributions", "significance": "Political activity detected", "confidence": "HIGH"})
        return connections
