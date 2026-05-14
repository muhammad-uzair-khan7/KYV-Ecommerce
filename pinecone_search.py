from pinecone import Pinecone
import os

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pinecone_client  = Pinecone(api_key=PINECONE_API_KEY)
index_handle     = pinecone_client.Index("vendor-contracts-intelligence")

async def query_hybrid_contract_context(
    tenant_id:     str,
    vendor_id:     str,
    query_text:    str,
    vector_values: list[float]
) -> list[dict]:

    response = index_handle.query(
        namespace=tenant_id,
        vector=vector_values,
        top_k=5,
        include_metadata=True,
        filter={
            "$and": [
                {"vendor_id":        {"$eq": vendor_id}},
                {"document_status":  {"$eq": "active"}}
            ]
        }
    )

    extracted_hits = []
    for match in response.get("matches", []):
        meta = match.get("metadata", {})
        extracted_hits.append({
            "id":                match.get("id"),
            "score":             match.get("score"),
            "title":             meta.get("document_title"),
            "body":              meta.get("body"),
            "risk_classification": meta.get("risk_classification")
        })
    return extracted_hits