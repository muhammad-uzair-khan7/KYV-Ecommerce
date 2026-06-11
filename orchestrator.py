from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import AIMessage
import os
from kyb_screening import kyb_sreening_node
from typing import Annotated, TypedDict, Literal
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, BaseMessage
from pydantic import BaseModel, Field
from contract_analysis import contract_analysis_node
from risk_scoring import risk_scoring_node
from human_review import human_review_queue_node
from fastapi import FastAPI, HTTPException
import uuid

from state_container import AssessmentGraphState


def orchestration_supervisor(state: AssessmentGraphState):
    kyb_status = state.get("kyb_status")
    parsed_contracts = state.get("parsed_contracts")
    risk_vector = state.get("computed_risk_vector", {})

    contract_attempts = state.get("contract_analysis_attempts", 0)
    if contract_attempts >= 3:
        print(f"⚠️ LOOP BREAKER: Contract analysis attempted {contract_attempts} times. FORCING to RiskScoring.")
        return {"next_action_node": "RiskScoring"}

    if not kyb_status or kyb_status == "PENDING":
        return {"next_action_node": "KYBScreening"}

    if kyb_status == "CLEAN" and not parsed_contracts:
        return {
            "next_action_node": "ContractAnalysis",
            "contract_analysis_attempts": contract_attempts + 1
        }

    if kyb_status in ("BLOCKED", "FLAGGED"):
        return {"next_action_node": "HumanReview"}

    if parsed_contracts and not risk_vector:
        return {"next_action_node": "RiskScoring"}

    if risk_vector.get("overall_score", 0) >= 51:
        return {"next_action_node": "HumanReviewQueue"}

    return {"next_action_node": "END"}


graph = StateGraph(AssessmentGraphState)
graph.add_node("Supervisor", orchestration_supervisor)
graph.add_node("KYBScreening", kyb_sreening_node)
graph.add_node("ContractAnalysis", contract_analysis_node)
graph.add_node("RiskScoring", risk_scoring_node)
graph.add_node("HumanReview", human_review_queue_node)


def routing_logic(state: AssessmentGraphState):
    target = state["next_action_node"]
    if target in ["KYBScreening", "ContractAnalysis", "RiskScoring", "HumanReview", "END"]:
        return target
    return END


graph.add_edge(START, "Supervisor")
graph.add_conditional_edges("Supervisor", routing_logic, {
    "KYBScreening": "KYBScreening",
    "ContractAnalysis": "ContractAnalysis",
    "RiskScoring": "RiskScoring",
    "HumanReview": "HumanReview",
    "END": END
})
graph.add_edge("KYBScreening", "Supervisor")
graph.add_edge("ContractAnalysis", "Supervisor")
graph.add_edge("RiskScoring", "Supervisor")
graph.add_edge("HumanReview", END)

compiled_graph = graph.compile()

app = FastAPI(title="Zirtex Vendor Risk & KYB Screening Platform")


class VendorInput(BaseModel):
    company_name: str
    country_iso: str = "PK"
    country_code: str | None = None
    tenant_id: str = "default_tenant"
    vendor_type: str = "saas_software"
    vendor_id: str = ""
    kyb_status: str = "PENDING"
    parsed_contracts: list = Field(default_factory=list)
    computed_risk_vector: dict = Field(default_factory=dict)
    model_config = {"extra": "ignore"}


@app.post("/evaluate-vendor")
async def evaluate_vendor(vendor_data: VendorInput):
    try:
        v_id = vendor_data.vendor_id if vendor_data.vendor_id else f"VND-{uuid.uuid4().hex[:6].upper()}"
        initial_state = {
            "vendor_id": v_id,
            "tenant_id": vendor_data.tenant_id or "default_tenant",
            "company_name": vendor_data.company_name,
            "country_iso": vendor_data.country_iso or vendor_data.country_code or "PK",
            "vendor_type": vendor_data.vendor_type,
            "kyb_status": vendor_data.kyb_status,
            "parsed_contracts": list(vendor_data.parsed_contracts) if vendor_data.parsed_contracts else [],
            "computed_risk_vector": vendor_data.computed_risk_vector or {},
            "messages": [],
            "contract_analysis_attempts": 0,
        }

        final_output = await compiled_graph.ainvoke(initial_state)
        return {"status": "Success", "graph_output": final_output}

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@app.get("/")
def read_root():
    return {"message": "Zirtex Multi-Agent Orchestrator Engine is Running!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orchestrator:app", host="127.0.0.1", port=8000)