import respx
import httpx

# Clean vendor — no sanctions hits
MOCK_YENTE_CLEAN = {
    "responses": {
        "vendor_check": {
            "results": []
        }
    }
}

# Flagged vendor — PEP match
MOCK_YENTE_FLAGGED = {
    "responses": {
        "vendor_check": {
            "results": [
                {
                    "id": "mock-entity-001",
                    "score": 0.85,
                    "caption": "Suspicious Corp Ltd",
                    "datasets": ["peps"],
                    "properties": {
                        "name": ["Suspicious Corp Ltd"],
                        "topics": ["role.pep"],
                        "jurisdiction": ["PK"],
                        "sanctions": []
                    }
                }
            ]
        }
    }
}

# Blocked vendor — sanctions hit
MOCK_YENTE_BLOCKED = {
    "responses": {
        "vendor_check": {
            "results": [
                {
                    "id": "mock-entity-002",
                    "score": 0.92,
                    "caption": "Blacklisted Exports LLC",
                    "datasets": ["us_ofac_sdn", "sanctions"],
                    "properties": {
                        "name": ["Blacklisted Exports LLC"],
                        "topics": ["sanction"],
                        "jurisdiction": ["IR"],
                        "sanctions": ["OFAC SDN List"]
                    }
                }
            ]
        }
    }
}