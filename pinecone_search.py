import asyncio
import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")
_pinecone_client = None
_index_handle = None
print(f"PINECONE_INDEX_HOST at import time: {os.getenv('PINECONE_INDEX_HOST')}")
def _get_index():
    """Lazy init — only connects when actually called, not at import time"""
    # global _pinecone_client, _index_handle
    # if _index_handle is None:
    #     _pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    #     _index_handle = _pinecone_client.Index("vendor-contracts-intelligence",
    #     host= PINECONE_INDEX_HOST)
    # return _index_handle
    global _pinecone_client, _index_handle
    _pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    _index_handle = _pinecone_client.Index(
        "vendor-contracts-intelligence",
        host=os.getenv("PINECONE_INDEX_HOST")
    )
    print(f"Connecting to host: {PINECONE_INDEX_HOST}")
    print(f"PINECONE_API_KEY: {PINECONE_API_KEY[:8]}...")
    return _index_handle

async def query_hybrid_contract_context(
    tenant_id:     str,
    vendor_id:     str,
    query_text:    str,
    vector_values: list[float]
) -> list[dict]:

    index = _get_index()  # only connects here, not at import
    print(f"DEBUG tenant_id={tenant_id}, vendor_id={vendor_id}")
    test_response = await asyncio.to_thread(
    index.describe_index_stats
)
    print(f"DEBUG index stats: {test_response}")
    raw_response = await asyncio.to_thread(
    index.query,
    namespace="tenant_001",
    vector=vector_values,
    top_k=5,
    include_metadata=True
)
    print(f"DEBUG index host: {PINECONE_INDEX_HOST}")
    print(f"DEBUG query vector length: {len(vector_values)}")
    print(f"DEBUG namespace: '{tenant_id}'")
    print(f"DEBUG vendor_id filter: '{vendor_id}'")
    print(f"RAW PINECONE RESPONSE: {raw_response}")
    # ==========================================================
    # THE CRITICAL FIX: Response ko safe dictionary mein convert kiya
    # ==========================================================
    # Naye Pinecone SDK (v6+) ke strict Pydantic parsing validation crash se bachane ke liye:
    if hasattr(raw_response, 'to_dict'):
        response = raw_response.to_dict()
    else:
        response = dict(raw_response)

    extracted_hits = []
    
    # Safely matches uthaye dictionary format mein
    matches = response.get('matches', [])
    if not matches and hasattr(raw_response, 'matches'):
        matches = raw_response.matches  # Fallback agar direct access ho sake

    for match in matches:
        # Check kiya ke match dictionary hai ya object (safety first)
        if isinstance(match, dict):
            meta = match.get("metadata") or {}
            match_id = match.get("id")
            match_score = match.get("score")
        else:
            meta = getattr(match, 'metadata', {}) or {}
            match_id = getattr(match, 'id', None)
            match_score = getattr(match, 'score', None)

        extracted_hits.append({
            "id":                  match_id,
            "score":               match_score,
            "title":               meta.get("document_title") or meta.get("title", "Untitled"),
            "body":                meta.get("body") or meta.get("text", ""),
            "risk_classification": meta.get("risk_classification") or "UNKNOWN"
        })
        
    print(f"[+] Pinecone search complete. Found matches: {len(extracted_hits)}")
    return extracted_hits