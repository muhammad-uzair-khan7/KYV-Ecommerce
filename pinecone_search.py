# pinecone_search.py

from pinecone import Pinecone
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
_pinecone_client = None
_index_handle = None

def _get_index():
    """Lazy init — only connects when actually called, not at import time"""
    global _pinecone_client, _index_handle
    if _index_handle is None:
        _pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
        _index_handle = _pinecone_client.Index("vendor-contracts-intelligence")
    return _index_handle

async def query_hybrid_contract_context(
    tenant_id:     str,
    vendor_id:     str,
    query_text:    str,
    vector_values: list[float]
) -> list[dict]:

    index = _get_index()  # only connects here, not at import

    response = index.query(
        namespace=tenant_id,
        vector=vector_values,
        top_k=5,
        include_metadata=True,
        filter={
            "$and": [
                {"vendor_id":       {"$eq": vendor_id}},
                {"document_status": {"$eq": "active"}}
            ]
        }
    )

    extracted_hits = []
    for match in response.matches:
        meta = match.metadata or {}
        extracted_hits.append({
            "id":                  match.id,
            "score":               match.score,
            "title":               meta.get("document_title"),
            "body":                meta.get("body"),
            "risk_classification": meta.get("risk_classification")
        })
    return extracted_hits