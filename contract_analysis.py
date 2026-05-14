import google.generativeai as genai
import os
import json
from state_container import AssessmentGraphState
from langchain_core.messages import AIMessage
from pinecone_search import query_hybrid_contract_context

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def contract_analysis_node(state: AssessmentGraphState) -> dict:
    vendor_id = state["vendor_id"]
    tenant_id = state["tenant_id"]
    company_name = state["company_name"]

    # Step 1: Generate embedding for the risk-focused query
    query_text = (
        f"liability indemnification force majeure data processing "
        f"termination clause compliance obligations {company_name}"
    )
    
    embedding_result = genai.embed_content(
        model="models/text-embedding-004",  # 768-dim Gemini embedding
        content=query_text,
        task_type="retrieval_query"
    )
    query_vector = embedding_result["embedding"]

    # Step 2: Hybrid search Pinecone for relevant clauses
    # (calls the function from Task B2 in your spec)
    hits = await query_hybrid_contract_context(
        tenant_id=tenant_id,
        vendor_id=vendor_id,
        query_text=query_text,
        vector_values=query_vector
    )

    if not hits:
        # No contracts uploaded yet — flag as incomplete but don't block
        return {
            "parsed_contracts": [],
            "messages": [AIMessage(content=f"No contract documents found for vendor {vendor_id}. Proceeding with reduced confidence.")]
        }

    # Step 3: Build context string from retrieved clauses
    context_chunks = "\n\n---\n\n".join([
        f"[{h['title']} | Risk: {h['risk_classification']}]\n{h['body']}"
        for h in hits
    ])

    # Step 4: Use LLM to extract structured clause analysis
    llm_prompt = f"""You are a legal risk analyst. Analyze the following contract clauses 
extracted from a vendor agreement and return a JSON object with this exact structure:

{{
  "liability_cap_found": true/false,
  "liability_cap_amount": "string or null",
  "force_majeure_present": true/false,
  "data_processing_agreement": true/false,
  "auto_renewal_clause": true/false,
  "termination_for_convenience": true/false,
  "indemnification_scope": "broad/narrow/none",
  "governing_law": "jurisdiction string or null",
  "high_risk_clauses": ["list of concerning clause summaries"],
  "overall_contract_risk": "LOW/MEDIUM/HIGH"
}}

Return ONLY valid JSON. No explanation, no markdown.

CONTRACT CLAUSES:
{context_chunks}
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    llm_response = model.generate_content(llm_prompt)
    raw_text = llm_response.text.strip()

    # Strip markdown fences if model adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        clause_analysis = json.loads(raw_text)
    except json.JSONDecodeError:
        clause_analysis = {
            "overall_contract_risk": "HIGH",
            "high_risk_clauses": ["LLM parsing failed — manual review required"],
            "parse_error": True
        }

    # Attach the raw hits too so risk scorer can reference them
    parsed_contracts = [{
        "vendor_id": vendor_id,
        "clause_analysis": clause_analysis,
        "source_chunks": hits
    }]

    summary = (
        f"Contract analysis complete. "
        f"Overall contract risk: {clause_analysis.get('overall_contract_risk')}. "
        f"High-risk clauses found: {len(clause_analysis.get('high_risk_clauses', []))}."
    )

    return {
        "parsed_contracts": parsed_contracts,
        "messages": [AIMessage(content=summary)]
    }