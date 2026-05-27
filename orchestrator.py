from langchain_core.messages import AIMessage
import os
from dotenv import load_dotenv
from kyb_screening import kyb_sreening_node
from typing import Annotated, TypedDict, Literal
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, BaseMessage
from pydantic import BaseModel, Field
from contract_analysis import contract_analysis_node
from risk_scoring import risk_scoring_node
from human_review import human_review_queue_node
<<<<<<< HEAD
=======
from fastapi import FastAPI, HTTPException
import uuid
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

# Global state container
from state_container import AssessmentGraphState


def orchestration_supervisor(state: AssessmentGraphState):
<<<<<<< HEAD
    if not state.get("kyb_status") or state["kyb_status"] == "PENDING":
        return {"next_action_node": "KYBScreening"}
    if state.get("kyb_status") == "CLEAN" and not state.get("parsed_contracts"):
        return {"next_action_node": "ContractAnalysis"}
    if state.get("kyb_status") in ("BLOCKED", "FLAGGED"):
        return {"next_action_node": "HumanReview"}
    if state.get("parsed_contracts") and not state.get("computed_risk_vector"):
        return {"next_action_node": "RiskScoring"}
    if state.get("computed_risk_vector", {}).get("overall_score", 0) >= 51:
        return {"next_action_node":"HumanReviewQueue"}

    return {"next_action_node": "END"}
=======
    if state is None:
        state = {}
    
    # Add loop prevention counter
    loop_count = state.get("_supervisor_loop_count", 0)
    if loop_count > 10:
        print(f"⚠️ Supervisor loop prevention: Breaking out after {loop_count} iterations")
        return {"next_action_node": "END"}
    
    kyb_status = state.get("kyb_status")
    parsed_contracts = state.get("parsed_contracts", [])
    computed_risk = state.get("computed_risk_vector", {})
    
    print(f"📊 Supervisor Check - KYB: {kyb_status}, Contracts: {len(parsed_contracts) if parsed_contracts else 0}, Risk Vector: {bool(computed_risk)}")
    
    # Route 1: KYB Screening (if not done yet)
    if not kyb_status or kyb_status == "PENDING":
        print(f"→ Routing to KYBScreening")
        return {"next_action_node": "KYBScreening", "_supervisor_loop_count": loop_count + 1}
    
    # Route 2: Human Review (if flagged/blocked from KYB)
    if kyb_status in ("BLOCKED", "FLAGGED"):
        print(f"→ Routing to HumanReview")
        return {"next_action_node": "HumanReview", "_supervisor_loop_count": loop_count + 1}
    
    # Route 3: Contract Analysis (only if CLEAN and NOT already attempted)
    # Use a flag to prevent re-attempting contract analysis
    if kyb_status == "CLEAN" and "_contract_analysis_done" not in state:
        print(f"→ Routing to ContractAnalysis")
        return {"next_action_node": "ContractAnalysis", "_supervisor_loop_count": loop_count + 1, "_contract_analysis_done": True}
    
    # Route 4: Risk Scoring (if contracts exist or already analyzed, but no risk vector yet)
    if kyb_status == "CLEAN" and not computed_risk:
        print(f"→ Routing to RiskScoring")
        return {"next_action_node": "RiskScoring", "_supervisor_loop_count": loop_count + 1}
    
    # Route 5: Human Review Queue (if risk is high)
    if computed_risk.get("overall_score", 0) >= 51:
        print(f"→ Routing to HumanReviewQueue (Risk Score: {computed_risk.get('overall_score', 0)})")
        return {"next_action_node":"HumanReviewQueue", "_supervisor_loop_count": loop_count + 1}

    # Default: All checks complete
    print(f"→ Routing to END (All checks complete)")
    return {"next_action_node": "END", "_supervisor_loop_count": loop_count + 1}
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)


load_dotenv()

kyb_screening_node= kyb_sreening_node

contract_analysis_node= contract_analysis_node

risk_scoring_node= risk_scoring_node

human_review_queue= human_review_queue_node

graph = StateGraph(AssessmentGraphState)
graph.add_node("Supervisor", orchestration_supervisor)
graph.add_node("KYBScreening", kyb_sreening_node)
graph.add_node("ContractAnalysis", contract_analysis_node)
graph.add_node("RiskScoring", risk_scoring_node)
graph.add_node("HumanReview", human_review_queue)

def routing_logic(state:AssessmentGraphState):
<<<<<<< HEAD
    target= state["next_action_node"]
=======
    if state is None:
        state = {}
    target = state.get("next_action_node", "END")
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
    if target in ["KYBScreening", "ContractAnalysis", "RiskScoring", "HumanReview", "END"]:
        return target
    return END

graph.add_edge(START, "Supervisor")
graph.add_conditional_edges("Supervisor",
        routing_logic,
        {
            "KYBScreening": "KYBScreening",
            "ContractAnalysis": "ContractAnalysis",
            "RiskScoring": "RiskScoring",
            "HumanReview": "HumanReview",
            "END": END
        }
)

graph.add_edge("KYBScreening", "Supervisor")
graph.add_edge("ContractAnalysis", "Supervisor")
graph.add_edge("RiskScoring", "Supervisor")
graph.add_edge("HumanReview", END)

compiled_graph = graph.compile()
<<<<<<< HEAD
from IPython.display import Image, display

display(Image(compiled_graph.get_graph().draw_mermaid_png()))
=======


# ==========================================
#  ZIRTEX ENTERPRISE FASTAPI INTEGRATION
# ==========================================

# Initialize FastAPI app (Uvicorn sits here)
# ==========================================
# ZIRTEX ENTERPRISE FASTAPI INTEGRATION (KEYFIX)
# ==========================================
MOCK_YENTE_CLEAN = {
    "responses": { "vendor_check": { "results": [] } }
}

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

# 2. FastAPI Initialize
app = FastAPI(title="Zirtex Vendor Risk & KYB Screening Platform")

class VendorInput(BaseModel):
    company_name: str
    country_iso: str = "PK"
    country_code: str = "PK"
    vendor_id: str = ""
    kyb_status: str = "PENDING"
    parsed_contracts: dict = Field(default_factory=dict)
    computed_risk_vector: dict = Field(default_factory=dict)
    vendor_type: str = "default"
    # Additional fields from request
    contact_email: str = ""
    industry: str = ""
    employee_count: int = 0
    quality_score: int = 0
    delivery_score: int = 0
    remarks: str = ""
    registration_number: str = ""

@app.post("/evaluate-vendor")
async def evaluate_vendor(vendor_data: VendorInput):
    try:
        # Prepare state
        v_id = vendor_data.vendor_id if vendor_data.vendor_id else f"VND-{uuid.uuid4().hex[:6].upper()}"
        # Use country_code if provided, otherwise country_iso
        country_iso = vendor_data.country_code if vendor_data.country_code else vendor_data.country_iso
        
        initial_state = {
            "vendor_id": v_id,
            "vendor_name": vendor_data.company_name,
            "company_name": vendor_data.company_name,
            "country_iso": country_iso,
            "kyb_status": vendor_data.kyb_status,
            "vendor_type": vendor_data.vendor_type,
            "parsed_contracts": vendor_data.parsed_contracts,
            "computed_risk_vector": vendor_data.computed_risk_vector,
            "next_action_node": "Supervisor",
            "_supervisor_loop_count": 0
        }
        
        # Invoke LangGraph Graph
        final_output = await compiled_graph.ainvoke(initial_state)
        return {"status": "Success", "graph_output": final_output}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Zirtex Multi-Agent Orchestrator Engine is Running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
