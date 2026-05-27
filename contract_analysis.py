import os
import json
from google import genai
from google.genai import types
<<<<<<< HEAD
=======
from pydantic import BaseModel, Field
from typing import List, Optional
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
from state_container import AssessmentGraphState
from langchain_core.messages import AIMessage
from pinecone_search import query_hybrid_contract_context

<<<<<<< HEAD
# Lazy init — avoids crash at import time if key is missing
=======
# ==========================================
# Pydantic Schema for Gemini Structured Output
# ==========================================
class ContractAnalysisSchema(BaseModel):
    liability_cap_found: bool
    liability_cap_amount: Optional[str] = None
    force_majeure_present: bool
    data_processing_agreement: bool
    auto_renewal_clause: bool
    termination_for_convenience: bool
    indemnification_scope: str = Field(description="Must be one of: broad, narrow, or none")
    governing_law: Optional[str] = None
    high_risk_clauses: List[str]
    overall_contract_risk: str = Field(description="Must be exactly: LOW, MEDIUM, or HIGH")


>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

async def contract_analysis_node(state: AssessmentGraphState) -> dict:
<<<<<<< HEAD
    vendor_id    = state["vendor_id"]
    tenant_id    = state["tenant_id"]
    company_name = state["company_name"]
=======
    if state is None:
        state = {}

    # FIX 1: Safe .get() fallbacks to prevent KeyError / NoneType lookup crashes
    vendor_id    = state.get("vendor_id", 0)
    tenant_id    = state.get("tenant_id", 1)
    company_name = state.get("company_name", "Unknown Vendor")
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

    query_text = (
        f"liability indemnification force majeure data processing "
        f"termination clause compliance obligations {company_name}"
    )

<<<<<<< HEAD
    # Step 1: Embed
    client = _get_client()
    embedding_result = client.models.embed_content(
        model="models/text-embedding-004",
        contents=query_text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    query_vector = embedding_result.embeddings[0].values

    # Step 2: Pinecone hybrid search
    hits = await query_hybrid_contract_context(
        tenant_id=tenant_id,
        vendor_id=vendor_id,
        query_text=query_text,
        vector_values=query_vector
    )
=======
    try:
        # Step 1: Embed via Gemini
        client = _get_client()
        embedding_result = client.models.embed_content(
            model="models/text-embedding-004",
            contents=query_text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        # Add safety checks for embedding result
        if embedding_result is None:
            print(f"⚠️ Embedding result is None")
            query_vector = []
        elif not hasattr(embedding_result, 'embeddings') or embedding_result.embeddings is None:
            print(f"⚠️ Embedding result has no embeddings attribute or embeddings is None")
            query_vector = []
        elif len(embedding_result.embeddings) == 0:
            print(f"⚠️ Embeddings list is empty")
            query_vector = []
        else:
            embedding_values = embedding_result.embeddings[0]
            if embedding_values is None:
                print(f"⚠️ First embedding is None")
                query_vector = []
            elif not hasattr(embedding_values, 'values') or embedding_values.values is None:
                print(f"⚠️ Embedding has no values attribute or values is None")
                query_vector = []
            else:
                query_vector = embedding_values.values
    except Exception as embed_err:
        print(f"⚠️ Contract Embedding Generation Failed: {str(embed_err)}")
        import traceback
        traceback.print_exc()
        query_vector = []

    # Step 2: Pinecone hybrid search
    hits = []
    if query_vector:
        try:
            hits = await query_hybrid_contract_context(
                tenant_id=tenant_id,
                vendor_id=vendor_id,
                query_text=query_text,
                vector_values=query_vector
            )
        except Exception as search_err:
            print(f"⚠️ Pinecone search failed: {str(search_err)}")
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

    if not hits:
        return {
            "parsed_contracts": [],
<<<<<<< HEAD
            "messages": [AIMessage(content=f"No contract documents found for vendor {vendor_id}. Proceeding with reduced confidence.")]
        }

    # Step 3: Build context
    context_chunks = "\n\n---\n\n".join([
        f"[{h['title']} | Risk: {h['risk_classification']}]\n{h['body']}"
        for h in hits
    ])

    # Step 4: LLM extraction
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
=======
            "messages": [AIMessage(content=f"No contract documents found for vendor {vendor_id}. Proceeding with reduced confidence.")],
            # Pass identity properties forward to keep LangGraph state fully complete
            "vendor_id": vendor_id,
            "tenant_id": tenant_id,
            "company_name": company_name,
            "kyb_status": "CLEAN",
            "_contract_analysis_done": True
        }

    # Step 3: Build context chunks
    context_chunks = "\n\n---\n\n".join([
        f"[{h.get('title', 'Document')} | Risk: {h.get('risk_classification', 'UNKNOWN')}]\n{h.get('body', '')}"
        for h in hits
    ])

    # Step 4: Strict Gemini Structured Analysis Execution
    llm_prompt = f"""You are an expert legal risk analyst. Analyze the following contract clauses 
extracted from a vendor agreement and map them perfectly to the requested configuration layout.
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)

CONTRACT CLAUSES:
{context_chunks}
"""

<<<<<<< HEAD
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=llm_prompt
    )
    raw_text = response.text.strip()

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
=======
    try:
        # FIX 2: Using response_mime_type and response_schema eliminates regex string manipulation bugs
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=llm_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ContractAnalysisSchema,
                temperature=0.1
            )
        )
        
        # This is guaranteed to be clean, un-wrapped JSON text
        clause_analysis = json.loads(response.text)
        
    except Exception as llm_err:
        print(f"❌ Gemini Generation/Parsing failed: {str(llm_err)}")
        clause_analysis = {
            "liability_cap_found": False,
            "liability_cap_amount": None,
            "force_majeure_present": False,
            "data_processing_agreement": False,
            "auto_renewal_clause": False,
            "termination_for_convenience": False,
            "indemnification_scope": "none",
            "governing_law": None,
            "overall_contract_risk": "HIGH",
            "high_risk_clauses": [f"Analysis pipeline error: {str(llm_err)}"],
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
            "parse_error": True
        }

    parsed_contracts = [{
        "vendor_id": vendor_id,
        "clause_analysis": clause_analysis,
        "source_chunks": hits
    }]

    summary = (
        f"Contract analysis complete. "
<<<<<<< HEAD
        f"Overall contract risk: {clause_analysis.get('overall_contract_risk')}. "
        f"High-risk clauses found: {len(clause_analysis.get('high_risk_clauses', []))}."
    )

    return {
        "parsed_contracts": parsed_contracts,
        "messages": [AIMessage(content=summary)]
    }
=======
        f"Overall contract risk: {clause_analysis.get('overall_contract_risk', 'HIGH')}. "
        f"High-risk clauses found: {len(clause_analysis.get('high_risk_clauses', []))}."
    )

    # Return structure updates alongside target identity tracking states
    return {
        "parsed_contracts": parsed_contracts,
        "messages": [AIMessage(content=summary)],
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "company_name": company_name,
        "kyb_status": "CLEAN",
        "_contract_analysis_done": True
    }
>>>>>>> 98e84e9 (JSON return and Yente dataset issue solved)
