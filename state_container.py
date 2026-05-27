from typing import Annotated, TypedDict, Literal
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, BaseMessage
from pydantic import BaseModel, Field

# Global state container
class AssessmentGraphState(TypedDict):
    messages: Annotated[list, add_messages]
    vendor_id: str
    tenant_id: str
    company_name: str
    country_iso: str
    vendor_type: str
    kyb_status: str
    parsed_contracts: list[dict]
    watchlist_flags: list[dict]
    computed_risk_vector: dict
    next_action_node: str
<<<<<<< HEAD
=======
    _supervisor_loop_count: int
    _contract_analysis_done: bool
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

class RoutingInstruction(BaseModel):
    selected_worker: Literal[
    "KYBScreeningNode",
    "ContractAnalysisNode",
    "RiskScoringNode",
    "HumanReviewQueue",
    "END"
] = Field(description="Select the appropriate specialized agent node based on state values")