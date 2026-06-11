# import httpx
# from langchain_core.messages import AIMessage
# import os
# from state_container import AssessmentGraphState
# from dotenv import load_dotenv

# load_dotenv()

# # Yente API URL - Use environment variable or disable
# YENTE_URL = os.getenv("YENTE_BASE_URL", "")
# YENTE_ENABLED = bool(YENTE_URL and YENTE_URL != "")


# async def kyb_screening_node(state: AssessmentGraphState) -> dict:
#     """
#     KYB Screening Node - Checks vendor against sanctions and watchlists
#     """
#     if state is None:
#         state = {}
    
#     company_name = state.get("company_name", "Unknown Vendor")
#     country_iso = state.get("country_iso", "")
#     vendor_id = state.get("vendor_id", "UNKNOWN")

#     watch_list = []
#     kyb_status = "CLEAN"
    
#     # If Yente not configured, skip screening
#     if not YENTE_ENABLED:
#         print(f"⚠️ YENTE_BASE_URL not configured. Defaulting to CLEAN status.")
#         return {
#             "messages": [AIMessage(content=f"KYB Screening skipped (Yente not configured). Status: CLEAN")],
#             "kyb_status": "CLEAN",
#             "watchlist_flags": [],
#             "vendor_id": vendor_id,
#             "tenant_id": state.get("tenant_id", "1"),    
#             "company_name": company_name,
#             "country_iso": country_iso
#         }
    
#     # Fallback protection for empty or missing payload values
#     safe_name = company_name if company_name else "Unknown Vendor"
#     safe_country = country_iso.lower() if country_iso else ""

#     try:
#         print(f"🕵️‍♂️ DEBUGGING VALUES SENT TO YENTE -> Name: '{company_name}', Country: '{country_iso}'")
#         async with httpx.AsyncClient(timeout=15) as client:
#             # Target the specific endpoint
#             url = f"{YENTE_URL}/match/default"
            
#             # Payload structure - Yente requires 'queries' field
#             payload = {
#                 "schema": "Organization",
#                 "queries": [{
#                     "properties": {
#                         "name": safe_name,
#                         "jurisdiction": safe_country
#                     }
#                 }]
#             }
            
#             response = await client.post(url, json=payload)
            
#             print(f"🔍 Yente Raw Response Code: {response.status_code}")
#             print(f"🔍 Yente Raw Text: {response.text}")
            
#             response.raise_for_status()
            
#             try:
#                 data = response.json()
#             except Exception as json_err:
#                 print(f"❌ Failed to parse JSON: {json_err}")
#                 raise ValueError("Yente response body was empty or corrupt.")

#         # Extract results from response
#         results = data.get("results", []) if data else []
        
#         for match in results:
#             if match is None:
#                 continue
#             score = match.get("score", 0)
#             print(f"🎯 Found Watchlist Match: {match.get('caption')} with Score: {score}")
            
#             # If match confidence is higher than 70%, flag it
#             if score > 0.70:
#                 kyb_status = "FLAGGED"
#                 break
                
#     except Exception as e:
#         print(f"⚠️ KYV Screening Exception Handled: {str(e)}")
#         print("⚠️ Defaulting to CLEAN status to keep workflow alive.")
#         kyb_status = "CLEAN"
    
#     summary = (f"KYB screening complete for '{company_name}'. "
#                f"Status: {kyb_status}. "
#                f"Flags found: {len(watch_list)}.")
    
#     return {
#         "messages": [AIMessage(content=f"KYB Screening completed with status: {kyb_status}")],
#         "kyb_status": kyb_status,
#         "watchlist_flags": [],
#         "vendor_id": vendor_id,
#         "tenant_id": state.get("tenant_id", "1"),    
#         "company_name": company_name,
#         "country_iso": country_iso
#     }

import httpx
import json as json_lib
from langchain_core.messages import AIMessage
import os
from state_container import AssessmentGraphState
from dotenv import load_dotenv

load_dotenv()

YENTE_URL = os.getenv("YENTE_BASE_URL")

MOCK_YENTE_CLEAN = {
    "responses": {"vendor_check": {"results": []}}
}

MOCK_YENTE_FLAGGED = {
    "responses": {
        "vendor_check": {
            "results": [{
                "id": "mock-entity-001",
                "score": 0.85,
                "caption": "Suspicious Corp Ltd",
                "datasets": ["peps"],
                "properties": {"name": ["Suspicious Corp Ltd"], "topics": ["role.pep"]}
            }]
        }
    }
}

MOCK_YENTE_BLOCKED = {
    "responses": {
        "vendor_check": {
            "results": [{
                "id": "mock-entity-002",
                "score": 0.92,
                "caption": "Blacklisted Exports LLC",
                "datasets": ["us_ofac_sdn", "sanctions"],
                "properties": {"name": ["Blacklisted Exports LLC"], "topics": ["sanction"]}
            }]
        }
    }
}


def _get_mock_response(company_name: str) -> dict | None:
    """Returns mock data if KYB_MOCK=true, else None."""
    if os.getenv("KYB_MOCK", "true").lower() != "true":
        return None
    if "Suspicious" in company_name:
        return MOCK_YENTE_FLAGGED
    if "Blacklisted" in company_name:
        return MOCK_YENTE_BLOCKED
    return MOCK_YENTE_CLEAN


async def kyb_sreening_node(state: AssessmentGraphState) -> dict:
    company_name = state["company_name"]
    country_iso  = state["country_iso"]
    vendor_id    = state["vendor_id"]

    watch_list = []
    kyb_status = "CLEAN"

    try:
        mock = _get_mock_response(company_name)
        if mock is not None:
            data = mock
        else:
            payload = {
                "queries": {
                    "vendor_check": {
                        "schema": "Company",
                        "properties": {
                            "name": [str(company_name)],
                            "country": [str(country_iso)]
                        },
                        "name": str(company_name)
                    }
                }
            }
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{YENTE_URL}/match/default",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

        results = data.get("responses", {}).get("vendor_check", {}).get("results", [])

        for match in results:
            score = match.get("score", 0)
            if score >= 0.7:
                flag = {
                    "match_name": match.get("caption"),
                    "score": score,
                    "datasets": match.get("datasets", []),
                    "entity_id": match.get("id"),
                    "is_pep": "peps" in str(match.get("datasets", [])).lower(),
                    "is_sanctioned": any(
                        d in str(match.get("datasets", [])).lower()
                        for d in ["sanctions", "ofac", "eu_fsf", "un_sc_sanctions"]
                    )
                }
                watch_list.append(flag)

        if any(f["is_sanctioned"] for f in watch_list):
            kyb_status = "BLOCKED"
        elif watch_list:
            kyb_status = "FLAGGED"

    except httpx.RequestError as e:
        return {
            "kyb_status": "PENDING_RETRY",
            "watchlist_flags": [],
            "messages": [AIMessage(content=f"KYB Screening failed - Connection error: {str(e)}")]
        }
    except Exception as e:
        return {
            "kyb_status": "PENDING_RETRY",
            "watchlist_flags": [],
            "messages": [AIMessage(content=f"KYB Screening failed: {str(e)}")]
        }

    return {
        "kyb_status": kyb_status,
        "watchlist_flags": watch_list,
        "messages": [AIMessage(content=f"KYB screening complete for '{company_name}'. Status: {kyb_status}. Flags: {len(watch_list)}")]
    }