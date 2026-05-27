<<<<<<< HEAD
=======
# from state_container import AssessmentGraphState
# import asyncpg
# import os
# import json
# from datetime import datetime, timezone
# from langchain_core.messages import AIMessage

# async def human_review_queue_node(state: AssessmentGraphState) -> dict:
#     vendor_id    = state["vendor_id"]
#     tenant_id    = state["tenant_id"]
#     company_name = state["company_name"]
#     risk_vector  = state.get("computed_risk_vector", {})
#     kyb_flags    = state.get("watchlist_flags", [])
#     contracts    = state.get("parsed_contracts", [])

#     residual_score = risk_vector.get("overall_score", 0)
#     inherent_score = risk_vector.get("inherent_score", 0)

#     # Determine why it ended up here
#     trigger_reasons = []
#     if state.get("kyb_status") == "BLOCKED":
#         trigger_reasons.append("Confirmed sanctions match")
#     if state.get("kyb_status") == "FLAGGED":
#         trigger_reasons.append(f"{len(kyb_flags)} watchlist flag(s) detected")
#     if residual_score >= 51:
#         trigger_reasons.append(f"Residual risk score {residual_score} exceeds EDD threshold")
#     if not trigger_reasons:
#         trigger_reasons.append("Manual review requested by workflow")

#     review_record = {
#         "vendor_id": vendor_id,
#         "tenant_id": tenant_id,
#         "company_name": company_name,
#         "residual_risk_score": residual_score,
#         "inherent_risk_score": inherent_score,
#         "kyb_status": state.get("kyb_status"),
#         "trigger_reasons": trigger_reasons,
#         "watchlist_flags": kyb_flags,
#         "contract_risk": contracts[0].get("clause_analysis", {}).get("overall_contract_risk") if contracts else None,
#         "assigned_to": None,  # compliance officer picks it up from the queue
#         "status": "PENDING_REVIEW",
#         "created_at": datetime.now(timezone.utc).isoformat(),
#     }

#     # Write to the compliance_review_queue table in PostgreSQL
#     try:
#         db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
#         conn = await asyncpg.connect(db_url)
#         await conn.execute("""
#             INSERT INTO compliance_review_queue 
#                 (vendor_id, tenant_id, company_name, residual_risk_score, 
#                  inherent_risk_score, kyb_status, trigger_reasons, 
#                  watchlist_flags, contract_risk, status, created_at)
#             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
#             ON CONFLICT (vendor_id) DO UPDATE SET
#                 status = EXCLUDED.status,
#                 residual_risk_score = EXCLUDED.residual_risk_score,
#                 created_at = EXCLUDED.created_at
#         """,
#             vendor_id, tenant_id, company_name,
#             residual_score, inherent_score,
#             state.get("kyb_status"),
#             json.dumps(trigger_reasons),
#             json.dumps(kyb_flags),
#             review_record["contract_risk"],
#             "PENDING_REVIEW",
#             review_record["created_at"]
#         )
#         await conn.close()
#         db_status = "Audit record written to compliance_review_queue."
#     except Exception as e:
#         db_status = f"DB write failed (non-blocking): {str(e)}"

#     # This message is what n8n reads from the API response to build the Slack alert
#     notification_payload = (
#         f"HUMAN REVIEW REQUIRED\n"
#         f"Vendor: {company_name} ({vendor_id})\n"
#         f"Residual Risk Score: {residual_score}/100\n"
#         f"Triggers: {', '.join(trigger_reasons)}\n"
#         f"KYB Status: {state.get('kyb_status')}\n"
#         f"Action: Log into compliance portal to review and approve/reject."
#     )

#     return {
#         "messages": [AIMessage(content=notification_payload)],
#         # Note: no next_action_node returned here — 
#         # the graph edge goes directly to END after this node
#     }

>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
from state_container import AssessmentGraphState
import asyncpg
import os
import json
from datetime import datetime, timezone
from langchain_core.messages import AIMessage
<<<<<<< HEAD

async def human_review_queue_node(state: AssessmentGraphState) -> dict:
    vendor_id    = state["vendor_id"]
    tenant_id    = state["tenant_id"]
    company_name = state["company_name"]
=======
from pinecone import Pinecone
# REMOVED: langchain_openai
# ADDED: Google GenAI Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

async def human_review_queue_node(state: AssessmentGraphState) -> dict:
    # Safe dictionary parsing to prevent crashes
    vendor_id    = state.get("vendor_id", 0)
    tenant_id    = state.get("tenant_id", 1)
    company_name = state.get("company_name", "Unknown Vendor")
    
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
    risk_vector  = state.get("computed_risk_vector", {})
    kyb_flags    = state.get("watchlist_flags", [])
    contracts    = state.get("parsed_contracts", [])

    residual_score = risk_vector.get("overall_score", 0)
    inherent_score = risk_vector.get("inherent_score", 0)

<<<<<<< HEAD
    # Determine why it ended up here
=======
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
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
<<<<<<< HEAD
        "contract_risk": contracts[0].get("clause_analysis", {}).get("overall_contract_risk") if contracts else None,
        "assigned_to": None,  # compliance officer picks it up from the queue
=======
        "contract_risk": contracts[0].get("clause_analysis", {}).get("overall_contract_risk") if contracts and len(contracts) > 0 and contracts[0] is not None else None,
        "assigned_to": None,
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
        "status": "PENDING_REVIEW",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

<<<<<<< HEAD
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
=======
    # ==========================================
    # PINECONE + GEMINI EMBEDDINGS INTEGRATION
    # ==========================================
    try:
        pc_api_key = os.getenv("PINECONE_API_KEY")
        pc_index_name = os.getenv("PINECONE_INDEX_NAME", "kyv-risk-intelligence")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if pc_api_key and gemini_key:
            # Initialize Pinecone Client
            pc = Pinecone(api_key=pc_api_key)
            index = pc.Index(pc_index_name)
            
            # Create the rich semantic text layout
            semantic_text = (
                f"Vendor Review Audit for {company_name}. "
                f"Trigger Reasons: {', '.join(trigger_reasons)}. "
                f"KYB Status is {state.get('kyb_status')}. "
                f"Inherent Risk Score: {inherent_score}. Residual Risk Score: {residual_score}."
            )
            
            # FIXED: Generate Embeddings vector using Gemini's native vector engine
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004", 
                google_api_key=gemini_key
            )
            vector = embeddings.embed_query(semantic_text)
            
            # Upsert into Pinecone Vector Index
            index.upsert(
                vectors=[
                    {
                        "id": f"vendor_{vendor_id}",
                        "values": vector,
                        "metadata": {
                            "vendor_id": int(vendor_id),
                            "tenant_id": int(tenant_id),
                            "company_name": company_name,
                            "residual_score": float(residual_score),
                            "kyb_status": str(state.get("kyb_status")),
                            "text_summary": semantic_text
                        }
                    }
                ],
                namespace="compliance-reviews"
            )
            print(f"🌲 [GEMINI + PINECONE SUCCESS] Vectorized risk context stored for vendor_{vendor_id}")
        else:
            print("⚠️ Missing PINECONE_API_KEY or GEMINI_API_KEY in environment.")
            
    except Exception as pinecone_err:
        print(f"⚠️ Vector storage via Gemini failed (non-blocking): {str(pinecone_err)}")

    # ==========================================
    # POSTGRESQL RELATIONAL STORAGE
    # ==========================================
    try:
        db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
        if db_url:
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
    except Exception as e:
        print(f"❌ Postgres error: {str(e)}")

    # ==========================================
    # SLACK ALERT OUTPUT PAYLOAD
    # ==========================================
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
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
<<<<<<< HEAD
        # Note: no next_action_node returned here — 
        # the graph edge goes directly to END after this node
=======
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "company_name": company_name
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
    }