import os
from pinecone import Pinecone
from google import genai
from google.genai import types
from dotenv import load_dotenv
 
load_dotenv()
 
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
INDEX_NAME       = "vendor-contracts-intelligence"
NAMESPACE        = "tenant_001"
VENDOR_ID        = "VND-ABC123"
 
pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(
    name=INDEX_NAME,
    host=os.getenv("PINECONE_INDEX_HOST")
)
 
gemini = genai.Client(api_key=GEMINI_API_KEY)
 
def get_embedding(text: str) -> list[float]:
    result = gemini.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT"
        )
    )
    return result.embeddings[0].values
 
clauses = [
    {
        "id": f"{VENDOR_ID}-clause-001",
        "title": "Master Service Agreement - Liability Clause",
        "risk": "HIGH",
        "body": (
            "The vendor's total liability under this agreement shall not exceed "
            "USD 50,000 in any twelve-month period. This cap applies regardless "
            "of the nature of the claim, whether in contract, tort, or otherwise. "
            "The vendor explicitly excludes liability for indirect, consequential, "
            "or punitive damages."
        )
    },
    {
        "id": f"{VENDOR_ID}-clause-002",
        "title": "Data Processing Agreement",
        "risk": "MEDIUM",
        "body": (
            "Vendor agrees to process personal data solely on documented instructions "
            "from the controller. Vendor shall implement appropriate technical and "
            "organisational measures to ensure security of data processing. Sub-processors "
            "may only be engaged with prior written consent of the controller. "
            "GDPR Article 28 obligations are fully accepted."
        )
    },
    {
        "id": f"{VENDOR_ID}-clause-003",
        "title": "Force Majeure Clause",
        "risk": "LOW",
        "body": (
            "Neither party shall be liable for delays or failures in performance "
            "resulting from acts beyond their reasonable control, including but not "
            "limited to acts of God, natural disasters, war, terrorism, pandemics, "
            "government actions, or internet outages. The affected party must provide "
            "written notice within 5 business days of the force majeure event."
        )
    },
    {
        "id": f"{VENDOR_ID}-clause-004",
        "title": "Termination and Auto-Renewal Clause",
        "risk": "MEDIUM",
        "body": (
            "This agreement shall automatically renew for successive one-year terms "
            "unless either party provides written notice of non-renewal at least 90 days "
            "prior to the end of the then-current term. Either party may terminate this "
            "agreement for convenience upon 30 days written notice. Upon termination, "
            "vendor shall return or destroy all client data within 14 days."
        )
    },
    {
        "id": f"{VENDOR_ID}-clause-005",
        "title": "Indemnification Clause",
        "risk": "HIGH",
        "body": (
            "Vendor shall indemnify, defend, and hold harmless the client from any "
            "third-party claims arising from vendor's gross negligence, wilful misconduct, "
            "or breach of this agreement. Client's indemnification obligations are limited "
            "solely to claims arising from client's misuse of the services. Indemnification "
            "scope is broad and includes legal fees, settlements, and judgments."
        )
    },
]
print(f"Generating real embeddings and upserting {len(clauses)} clauses...")
print(f"  Index     : {INDEX_NAME}")
print(f"  Namespace : {NAMESPACE}")
print(f"  Vendor ID : {VENDOR_ID}\n")
 
vectors = []
for c in clauses:
    print(f"  Embedding: {c['title']}...")
    vec = get_embedding(c["body"])
    vectors.append({
        "id": c["id"],
        "values": vec,
        "metadata": {
            "vendor_id": VENDOR_ID,
            "document_status": "active",
            "document_title": c["title"],
            "risk_classification": c["risk"],
            "body": c["body"]
        }
    })

index.upsert(vectors=vectors, namespace=NAMESPACE)
 
print("\nDone. Verifying...")
stats = index.describe_index_stats()
print(f"  Total vectors : {stats.total_vector_count}")
ns = stats.namespaces.get(NAMESPACE)
if ns:
    print(f"  Vectors in '{NAMESPACE}' : {ns.vector_count}")
print(f"Vector dimensions: {len(vectors[0]['values'])}")
print("\nUpsert complete. Run your pipeline now.")
print(f"Upserting to host: {os.getenv('PINECONE_INDEX_HOST')}")
stats = index.describe_index_stats()
print(f"Stats before upsert: {stats}")
print(f"PINECONE_API_KEY: {os.getenv('PINECONE_API_KEY')[:8]}...")