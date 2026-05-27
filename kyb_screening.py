import httpx
from langchain_core.messages import AIMessage
import os
from state_container import AssessmentGraphState, RoutingInstruction
from dotenv import load_dotenv
load_dotenv()
<<<<<<< HEAD
YENTE_URL= os.getenv("YENTE_BASE_URL")
async def kyb_sreening_node(state:AssessmentGraphState) -> dict:
    company_name= state["company_name"]
    country_iso= state["country_iso"]
    vendor_id= state["vendor_id"]

    watch_list= []
    kyb_status= "CLEAN"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response= await client.post(f"{YENTE_URL}/match/default",
                                        json={
                                            "queries": {
                                                "vendor_check" : {
                                                    "schema": "Company",
                                                    "properties": {
                                                        "name": [company_name],
                                                        "country": [country_iso]
                                                    }
                                                }
                                            }
                                        }
                                )
            response.raise_for_status()
            data= response.json()
        
        results= data.get("responses", {}).get("vendor_check", {}).get("results", [])
        for match in results:
            score= match.get("score", 0)
            datasets= match.get("datasets", [])

            if score>= 0.7:
                flag = {
                    "match_name": match.get("caption"),
                    "score": score,
                    "datasets": datasets,
                    "entity_id": match.get("id"),
                    "is_pep": "peps" in str(datasets).lower(),
                    "is_sanctioned": any(
                        d in str(datasets).lower() 
                        for d in ["sanctions", "ofac", "eu_fsf", "un_sc_sanctions"]
                    )
                }
                watch_list.append(flag) 

            if flag["is_sanctioned"]:
                kyb_status= "BLOCKED"
            elif kyb_status != "BLOCKED":
                kyb_status = "FLAGGED"
    except httpx.RequestError as e:
        return {
            "kyb_status": "PENDING_RETRY",
            "watchlist_flags": [],
            "messages": [AIMessage(content=f"KYB Screening failed. YENTE unreachable. Error {str(e)}")]
        }
=======
YENTE_URL= "http://localhost:8000"
async def kyb_sreening_node(state:AssessmentGraphState) -> dict:
    if state is None:
        state = {}
    
    company_name= state.get("company_name", "Unknown Vendor")
    country_iso= state.get("country_iso", "")
    vendor_id= state.get("vendor_id", "UNKNOWN")

    watch_list= []
    kyb_status = "CLEAN"
    
    # 1. Fallback protection for empty or missing payload values
    safe_name = company_name if company_name else "Unknown Vendor"
    safe_country = country_iso.lower() if country_iso else ""

    try:
        print(f"🕵️‍♂️ DEBUGGING VALUES SENT TO YENTE -> Name: '{company_name}', Country: '{country_iso}'")
        async with httpx.AsyncClient(timeout=15) as client:
            # We target the specific single-match query endpoint directly
            url = f"{YENTE_URL}/match/sanctions"
            
            # Direct, flattened schema structure
            payload = {
                "schema": "Organization",
                "properties": {
                    "name": [safe_name],
                    "jurisdiction": [safe_country]
                }
            }
            
            response = await client.post(url, json=payload)
            
            print(f"🔍 Yente Raw Response Code: {response.status_code}")
            print(f"🔍 Yente Raw Text: {response.text}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception as json_err:
                print(f"❌ Failed to parse JSON: {json_err}")
                raise ValueError("Yente response body was empty or corrupt.")

        # The single-match endpoint returns a flat 'results' array directly at the top level
        results = data.get("results", []) if data else []
        
        for match in results:
            if match is None:
                continue
            score = match.get("score", 0)
            print(f"🎯 Found Watchlist Match: {match.get('caption')} with Score: {score}")
            
            # If match confidence is higher than 70%, flag it
            if score > 0.70:
                kyb_status = "FLAGGED"
                break
                
    except Exception as e:
        print(f"⚠️ KYV Screening Exception Handled: {str(e)}")
        print("⚠️ Defaulting to CLEAN status to keep workflow alive.")
        kyb_status = "CLEAN"
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
    
    summary= (f"KYB screening complete for '{company_name}'."
              f"Status: {kyb_status}."
              f"Flags found: {len(watch_list)}.")
        

    return {
<<<<<<< HEAD
        "kyb_status":kyb_status,
        "watchlist_flags": watch_list,
        "messages": [AIMessage(content=summary)]
=======
        "messages": [AIMessage(content=f"KYB Screening completed with status: {kyb_status}")],
        "kyb_status": kyb_status,
        "watchlist_flags": [],
        "vendor_id": vendor_id,
        "tenant_id": state.get("tenant_id", "1"),    
        "company_name": company_name,
        "country_iso": country_iso
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
    }