from state_container import AssessmentGraphState
import asyncpg
import os
import json
from datetime import datetime, timezone
from langchain_core.messages import AIMessage

async def human_review_queue_node(state: AssessmentGraphState) -> dict:
    vendor_id    = state["vendor_id"]
    tenant_id    = state["tenant_id"]
    company_name = state["company_name"]
    risk_vector  = state.get("computed_risk_vector", {})
    kyb_flags    = state.get("watchlist_flags", [])
    contracts    = state.get("parsed_contracts", [])

    residual_score = risk_vector.get("overall_score", 0)
    inherent_score = risk_vector.get("inherent_score", 0)

    # Determine why it ended up here
    trigger_reasons = []
    if state.get("kyb_status") == "BLOCKED":
        trigger_reasons.append("Confirmed sanctions match")
    if state.get("kyb_status") == "FLAGGED":
        trigger_reasons.append(f"{len(kyb_flags)} watchlist flag(s) detected")
    if residual_score >= 51:
        trigger_reasons.append(f"Residual risk score {residual_score} exceeds EDD threshold")
    if not trigger_reasons:
        trigger_reasons.append("Manual review requested by workflow")

    review_record = {
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "company_name": company_name,
        "residual_risk_score": residual_score,
        "inherent_risk_score": inherent_score,
        "kyb_status": state.get("kyb_status"),
        "trigger_reasons": trigger_reasons,
        "watchlist_flags": kyb_flags,
        "contract_risk": contracts[0].get("clause_analysis", {}).get("overall_contract_risk") if contracts else None,
        "assigned_to": None,  # compliance officer picks it up from the queue
        "status": "PENDING_REVIEW",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Write to the compliance_review_queue table in PostgreSQL
    try:
        db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)
        await conn.execute("""
            INSERT INTO compliance_review_queue 
                (vendor_id, tenant_id, company_name, residual_risk_score, 
                 inherent_risk_score, kyb_status, trigger_reasons, 
                 watchlist_flags, contract_risk, status, created_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT (vendor_id) DO UPDATE SET
                status = EXCLUDED.status,
                residual_risk_score = EXCLUDED.residual_risk_score,
                created_at = EXCLUDED.created_at
        """,
            vendor_id, tenant_id, company_name,
            residual_score, inherent_score,
            state.get("kyb_status"),
            json.dumps(trigger_reasons),
            json.dumps(kyb_flags),
            review_record["contract_risk"],
            "PENDING_REVIEW",
            review_record["created_at"]
        )
        await conn.close()
        db_status = "Audit record written to compliance_review_queue."
    except Exception as e:
        db_status = f"DB write failed (non-blocking): {str(e)}"

    # This message is what n8n reads from the API response to build the Slack alert
    notification_payload = (
        f"HUMAN REVIEW REQUIRED\n"
        f"Vendor: {company_name} ({vendor_id})\n"
        f"Residual Risk Score: {residual_score}/100\n"
        f"Triggers: {', '.join(trigger_reasons)}\n"
        f"KYB Status: {state.get('kyb_status')}\n"
        f"Action: Log into compliance portal to review and approve/reject."
    )

    return {
        "messages": [AIMessage(content=notification_payload)],
        # Note: no next_action_node returned here — 
        # the graph edge goes directly to END after this node
    }