import httpx
from langchain_core.messages import AIMessage
import os
from state_container import AssessmentGraphState, RoutingInstruction
from dotenv import load_dotenv
load_dotenv()
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
    
    summary= (f"KYB screening complete for '{company_name}'."
              f"Status: {kyb_status}."
              f"Flags found: {len(watch_list)}.")
        

    return {
        "kyb_status":kyb_status,
        "message": [AIMessage(content=summary)]
    }