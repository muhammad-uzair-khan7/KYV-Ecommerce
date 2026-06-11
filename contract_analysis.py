# import os
# import json as _json
# from google import genai
# from google.genai import types
# from state_container import AssessmentGraphState
# from langchain_core.messages import AIMessage
# from pinecone_search import query_hybrid_contract_context

# _client = None

# def _get_client():
#     global _client
#     if _client is None:
#         _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
#     return _client

# async def contract_analysis_node(state: AssessmentGraphState) -> dict:
#     vendor_id    = state["vendor_id"]
#     tenant_id    = state["tenant_id"]
#     company_name = state["company_name"]

#     query_text = (
#         f"liability indemnification force majeure data processing "
#         f"termination clause compliance obligations {company_name}"
#     )

#     client = _get_client()
#     try:
#         embedding_result = await client.aio.models.embed_content(
#             model="gemini-embedding-001",
#             contents=query_text,
#             config=types.EmbedContentConfig(
#                 task_type="RETRIEVAL_QUERY"
#             )
#         )
#         print(f"DEBUG GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')}")
#         print(f"DEBUG embedding_result type: {type(embedding_result)}")
#         print(f"DEBUG embedding_result: {embedding_result}")

#         if embedding_result and hasattr(embedding_result, 'embeddings') and embedding_result.embeddings:
#             query_vector = embedding_result.embeddings[0].values
#             print(f"[+] Embeddings generated. Dimensions: {len(query_vector)}")
#         else:
#             print("[-] WARNING: Google API returned empty embedding structure. Using zero-vector fallback.")
#             query_vector = [0.0] * 3072

#     except Exception as e:
#         print(f"[-] CRITICAL ERROR in Embedding API: {e}")
#         query_vector = [0.0] * 3072

#     hits = await query_hybrid_contract_context(
#         tenant_id=tenant_id,
#         vendor_id=vendor_id,
#         query_text=query_text,
#         vector_values=query_vector
#     )

#     if not hits:
#         return {
#             "parsed_contracts": [{
#                 "vendor_id": vendor_id,
#                 "clause_analysis": {
#                     "overall_contract_risk": "UNKNOWN",
#                     "high_risk_clauses": [],
#                     "no_contract_found": True
#                 },
#                 "source_chunks": []
#             }],
#             "messages": [AIMessage(content=f"No contract documents found for vendor {vendor_id}.")]
#         }

#     context_chunks = "\n\n---\n\n".join([
#         f"[{h['title']} | Risk: {h['risk_classification']}]\n{h['body']}"
#         for h in hits
#     ])

#     llm_prompt = f"""You are a legal risk analyst. Analyze the following contract clauses 
# extracted from a vendor agreement and return a JSON object with this exact structure:

# {{
#   "liability_cap_found": true/false,
#   "liability_cap_amount": "string or null",
#   "force_majeure_present": true/false,
#   "data_processing_agreement": true/false,
#   "auto_renewal_clause": true/false,
#   "termination_for_convenience": true/false,
#   "indemnification_scope": "broad/narrow/none",
#   "governing_law": "jurisdiction string or null",
#   "high_risk_clauses": ["list of concerning clause summaries"],
#   "overall_contract_risk": "LOW/MEDIUM/HIGH"
# }}

# CONTRACT CLAUSES:
# {context_chunks}
# """

#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-lite",
#             contents=llm_prompt,
#             config=types.GenerateContentConfig(
#                 response_mime_type="application/json"
#             )
#         )
#         raw_text = response.text.strip()
#         clause_analysis = _json.loads(raw_text)

#     except Exception as json_err:
#         print(f"[-] JSON Parsing or LLM call failed: {json_err}")
#         clause_analysis = {
#             "overall_contract_risk": "HIGH",
#             "high_risk_clauses": [f"LLM parsing failed: {str(json_err)} — manual review required"],
#             "parse_error": True
#         }

#     parsed_contracts = [{
#         "vendor_id": vendor_id,
#         "clause_analysis": clause_analysis,
#         "source_chunks": hits
#     }]

#     summary = (
#         f"Contract analysis complete. "
#         f"Overall contract risk: {clause_analysis.get('overall_contract_risk')}. "
#         f"High-risk clauses found: {len(clause_analysis.get('high_risk_clauses', []))}."
#     )

#     return {
#         "parsed_contracts": parsed_contracts,
#         "messages": [AIMessage(content=summary)]
#     }



#---------OPENROUTER-----------
# import os
# import httpx
# import json as _json
# from google import genai
# from google.genai import types
# from state_container import AssessmentGraphState
# from langchain_core.messages import AIMessage
# from pinecone_search import query_hybrid_contract_context
# from dotenv import load_dotenv

# load_dotenv()

# _client = None

# def _get_client():
#     global _client
#     if _client is None:
#         _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
#     return _client


# async def _call_llm(prompt: str) -> str:
#     async with httpx.AsyncClient(timeout=30) as client:
#         response = await client.post(
#             "https://openrouter.ai/api/v1/chat/completions",
#             headers={
#                 "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "model": "mistralai/Mistral-7B-Instruct-v0.3",
#                 "messages": [{"role": "user", "content": prompt}],
#                 "response_format": {"type": "json_object"}
#             }
#         )
#         data = response.json()
#         print(f"DEBUG OpenRouter response: {data}")
#         return data["choices"][0]["message"]["content"]


# async def contract_analysis_node(state: AssessmentGraphState) -> dict:
#     vendor_id    = state["vendor_id"]
#     tenant_id    = state["tenant_id"]
#     company_name = state["company_name"]

#     query_text = (
#         f"liability indemnification force majeure data processing "
#         f"termination clause compliance obligations {company_name}"
#     )

#     # Step 1: Generate embeddings
#     client = _get_client()
#     try:
#         embedding_result = await client.aio.models.embed_content(
#             model="gemini-embedding-001",
#             contents=query_text,
#             config=types.EmbedContentConfig(
#                 task_type="RETRIEVAL_QUERY"
#             )
#         )

#         if embedding_result and hasattr(embedding_result, 'embeddings') and embedding_result.embeddings:
#             query_vector = embedding_result.embeddings[0].values
#             print(f"[+] Embeddings generated. Dimensions: {len(query_vector)}")
#         else:
#             print("[-] WARNING: Google API returned empty embedding structure. Using zero-vector fallback.")
#             query_vector = [0.0] * 3072

#     except Exception as e:
#         print(f"[-] CRITICAL ERROR in Embedding API: {e}")
#         query_vector = [0.0] * 3072

#     # Step 2: Pinecone search
#     hits = await query_hybrid_contract_context(
#         tenant_id=tenant_id,
#         vendor_id=vendor_id,
#         query_text=query_text,
#         vector_values=query_vector
#     )

#     if not hits:
#         return {
#             "parsed_contracts": [{
#                 "vendor_id": vendor_id,
#                 "clause_analysis": {
#                     "overall_contract_risk": "UNKNOWN",
#                     "high_risk_clauses": [],
#                     "no_contract_found": True
#                 },
#                 "source_chunks": []
#             }],
#             "messages": [AIMessage(content=f"No contract documents found for vendor {vendor_id}.")]
#         }

#     # Step 3: Build context
#     context_chunks = "\n\n---\n\n".join([
#         f"[{h['title']} | Risk: {h['risk_classification']}]\n{h['body']}"
#         for h in hits
#     ])

#     # Step 4: LLM extraction via OpenRouter
#     llm_prompt = f"""You are a legal risk analyst. Analyze the following contract clauses 
# extracted from a vendor agreement and return a JSON object with this exact structure:

# {{
#   "liability_cap_found": true or false,
#   "liability_cap_amount": "string or null",
#   "force_majeure_present": true or false,
#   "data_processing_agreement": true or false,
#   "auto_renewal_clause": true or false,
#   "termination_for_convenience": true or false,
#   "indemnification_scope": "broad or narrow or none",
#   "governing_law": "jurisdiction string or null",
#   "high_risk_clauses": ["list of concerning clause summaries"],
#   "overall_contract_risk": "LOW or MEDIUM or HIGH"
# }}

# CONTRACT CLAUSES:
# {context_chunks}
# """

#     try:
#         raw_text = await _call_llm(llm_prompt)
#         clause_analysis = _json.loads(raw_text)

#     except Exception as json_err:
#         print(f"[-] LLM call failed: {json_err}")
#         clause_analysis = {
#             "overall_contract_risk": "HIGH",
#             "high_risk_clauses": [f"LLM parsing failed: {str(json_err)} — manual review required"],
#             "parse_error": True
#         }

#     parsed_contracts = [{
#         "vendor_id": vendor_id,
#         "clause_analysis": clause_analysis,
#         "source_chunks": hits
#     }]

#     summary = (
#         f"Contract analysis complete. "
#         f"Overall contract risk: {clause_analysis.get('overall_contract_risk')}. "
#         f"High-risk clauses found: {len(clause_analysis.get('high_risk_clauses', []))}."
#     )

#     return {
#         "parsed_contracts": parsed_contracts,
#         "messages": [AIMessage(content=summary)]
#     }


#-----------HUGGINGFACE INFERENCE API-----------
# import os
# import httpx
# import json as _json
# from google import genai
# from google.genai import types
# from state_container import AssessmentGraphState
# from langchain_core.messages import AIMessage
# from pinecone_search import query_hybrid_contract_context
# from dotenv import load_dotenv

# load_dotenv()

# _client = None

# def _get_client():
#     global _client
#     if _client is None:
#         _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
#     return _client


# async def _call_llm(prompt: str) -> str:
#     hf_token = os.getenv("HF_API_TOKEN")
#     model_id  = "mistralai/Mistral-7B-Instruct-v0.3"

#     # Wrap prompt in Mistral instruction format
#     formatted = f"[INST] {prompt}\n\nRespond ONLY with a valid JSON object, no explanation, no markdown, no backticks. [/INST]"

#     async with httpx.AsyncClient(timeout=60) as client:
#         response = await client.post(
#             f"https://api-inference.huggingface.co/models/{model_id}",
#             headers={
#                 "Authorization": f"Bearer {hf_token}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "inputs": formatted,
#                 "parameters": {
#                     "max_new_tokens": 800,
#                     "temperature": 0.1,
#                     "return_full_text": False
#                 }
#             }
#         )

#         data = response.json()
#         print(f"DEBUG HF response: {str(data)[:300]}")

#         # HF returns a list of generated texts
#         if isinstance(data, list) and data:
#             raw = data[0].get("generated_text", "")
#         elif isinstance(data, dict) and "error" in data:
#             raise Exception(f"HF API error: {data['error']}")
#         else:
#             raise Exception(f"Unexpected HF response format: {data}")

#         # Extract JSON from response
#         raw = raw.strip()
#         if "```" in raw:
#             raw = raw.split("```")[1]
#             if raw.startswith("json"):
#                 raw = raw[4:]
#             raw = raw.split("```")[0]

#         # Find JSON object in response
#         start = raw.find("{")
#         end   = raw.rfind("}") + 1
#         if start == -1 or end == 0:
#             raise Exception(f"No JSON object found in response: {raw[:200]}")

#         return raw[start:end]


# async def contract_analysis_node(state: AssessmentGraphState) -> dict:
#     vendor_id    = state["vendor_id"]
#     tenant_id    = state["tenant_id"]
#     company_name = state["company_name"]

#     query_text = (
#         f"liability indemnification force majeure data processing "
#         f"termination clause compliance obligations {company_name}"
#     )

#     # Step 1: Generate embeddings
#     client = _get_client()
#     try:
#         embedding_result = await client.aio.models.embed_content(
#             model="gemini-embedding-001",
#             contents=query_text,
#             config=types.EmbedContentConfig(
#                 task_type="RETRIEVAL_QUERY"
#             )
#         )

#         if embedding_result and hasattr(embedding_result, 'embeddings') and embedding_result.embeddings:
#             query_vector = embedding_result.embeddings[0].values
#             print(f"[+] Embeddings generated. Dimensions: {len(query_vector)}")
#         else:
#             print("[-] WARNING: Google API returned empty embedding structure. Using zero-vector fallback.")
#             query_vector = [0.0] * 3072

#     except Exception as e:
#         print(f"[-] CRITICAL ERROR in Embedding API: {e}")
#         query_vector = [0.0] * 3072

#     # Step 2: Pinecone search
#     hits = await query_hybrid_contract_context(
#         tenant_id=tenant_id,
#         vendor_id=vendor_id,
#         query_text=query_text,
#         vector_values=query_vector
#     )

#     if not hits:
#         return {
#             "parsed_contracts": [{
#                 "vendor_id": vendor_id,
#                 "clause_analysis": {
#                     "overall_contract_risk": "UNKNOWN",
#                     "high_risk_clauses": [],
#                     "no_contract_found": True
#                 },
#                 "source_chunks": []
#             }],
#             "messages": [AIMessage(content=f"No contract documents found for vendor {vendor_id}.")]
#         }

#     # Step 3: Build context
#     context_chunks = "\n\n---\n\n".join([
#         f"[{h['title']} | Risk: {h['risk_classification']}]\n{h['body']}"
#         for h in hits
#     ])

#     # Step 4: LLM extraction
#     llm_prompt = f"""You are a legal risk analyst. Analyze the following contract clauses and return a JSON object with EXACTLY this structure:

# {{
#   "liability_cap_found": true or false,
#   "liability_cap_amount": "string or null",
#   "force_majeure_present": true or false,
#   "data_processing_agreement": true or false,
#   "auto_renewal_clause": true or false,
#   "termination_for_convenience": true or false,
#   "indemnification_scope": "broad or narrow or none",
#   "governing_law": "jurisdiction string or null",
#   "high_risk_clauses": ["list of concerning clause summaries"],
#   "overall_contract_risk": "LOW or MEDIUM or HIGH"
# }}

# CONTRACT CLAUSES:
# {context_chunks}"""

#     try:
#         raw_text = await _call_llm(llm_prompt)
#         clause_analysis = _json.loads(raw_text)

#     except Exception as json_err:
#         print(f"[-] LLM call failed: {json_err}")
#         clause_analysis = {
#             "overall_contract_risk": "HIGH",
#             "high_risk_clauses": [f"LLM parsing failed: {str(json_err)} — manual review required"],
#             "parse_error": True
#         }

#     parsed_contracts = [{
#         "vendor_id": vendor_id,
#         "clause_analysis": clause_analysis,
#         "source_chunks": hits
#     }]

#     summary = (
#         f"Contract analysis complete. "
#         f"Overall contract risk: {clause_analysis.get('overall_contract_risk')}. "
#         f"High-risk clauses found: {len(clause_analysis.get('high_risk_clauses', []))}."
#     )

#     return {
#         "parsed_contracts": parsed_contracts,
#         "messages": [AIMessage(content=summary)]
#     }


#------------ GROQ API KEY-----------------
import os
import httpx
import json as _json
from google import genai
from google.genai import types
from state_container import AssessmentGraphState
from langchain_core.messages import AIMessage
from pinecone_search import query_hybrid_contract_context
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


async def _call_llm(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
        )
        data = response.json()
        print(f"DEBUG Groq response: {str(data)[:200]}")
        return data["choices"][0]["message"]["content"]


async def contract_analysis_node(state: AssessmentGraphState) -> dict:
    vendor_id    = state["vendor_id"]
    tenant_id    = state["tenant_id"]
    company_name = state["company_name"]

    query_text = (
        f"liability indemnification force majeure data processing "
        f"termination clause compliance obligations {company_name}"
    )

    # Step 1: Generate embeddings
    client = _get_client()
    try:
        embedding_result = await client.aio.models.embed_content(
            model="gemini-embedding-001",
            contents=query_text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )

        if embedding_result and hasattr(embedding_result, 'embeddings') and embedding_result.embeddings:
            query_vector = embedding_result.embeddings[0].values
            print(f"[+] Embeddings generated. Dimensions: {len(query_vector)}")
        else:
            print("[-] WARNING: Google API returned empty embedding structure. Using zero-vector fallback.")
            query_vector = [0.0] * 3072

    except Exception as e:
        print(f"[-] CRITICAL ERROR in Embedding API: {e}")
        query_vector = [0.0] * 3072

    # Step 2: Pinecone search
    hits = await query_hybrid_contract_context(
        tenant_id=tenant_id,
        vendor_id=vendor_id,
        query_text=query_text,
        vector_values=query_vector
    )

    if not hits:
        return {
            "parsed_contracts": [{
                "vendor_id": vendor_id,
                "clause_analysis": {
                    "overall_contract_risk": "UNKNOWN",
                    "high_risk_clauses": [],
                    "no_contract_found": True
                },
                "source_chunks": []
            }],
            "messages": [AIMessage(content=f"No contract documents found for vendor {vendor_id}.")]
        }

    # Step 3: Build context
    context_chunks = "\n\n---\n\n".join([
        f"[{h['title']} | Risk: {h['risk_classification']}]\n{h['body']}"
        for h in hits
    ])

    # Step 4: LLM extraction
    llm_prompt = f"""You are a legal risk analyst. Analyze the following contract clauses and return a JSON object with EXACTLY this structure:

{{
  "liability_cap_found": true or false,
  "liability_cap_amount": "string or null",
  "force_majeure_present": true or false,
  "data_processing_agreement": true or false,
  "auto_renewal_clause": true or false,
  "termination_for_convenience": true or false,
  "indemnification_scope": "broad or narrow or none",
  "governing_law": "jurisdiction string or null",
  "high_risk_clauses": ["list of concerning clause summaries"],
  "overall_contract_risk": "LOW or MEDIUM or HIGH"
}}

CONTRACT CLAUSES:
{context_chunks}"""

    try:
        raw_text = await _call_llm(llm_prompt)
        clause_analysis = _json.loads(raw_text)

    except Exception as json_err:
        print(f"[-] LLM call failed: {json_err}")
        clause_analysis = {
            "overall_contract_risk": "HIGH",
            "high_risk_clauses": [f"LLM parsing failed: {str(json_err)} — manual review required"],
            "parse_error": True
        }

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