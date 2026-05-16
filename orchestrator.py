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

# Global state container
from state_container import AssessmentGraphState


def orchestration_supervisor(state: AssessmentGraphState):
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
    target= state["next_action_node"]
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
from IPython.display import Image, display

display(Image(compiled_graph.get_graph().draw_mermaid_png()))
