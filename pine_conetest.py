# import os
# from pinecone import Pinecone
# from dotenv import load_dotenv
# load_dotenv()

# pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# index = pc.Index(
#     name="vendor-contracts-intelligence",
#     host=os.getenv("PINECONE_INDEX_HOST")
# )

# dummy_vector = [0.1] * 3072
# result = index.query(
#     namespace="tenant_001",
#     vector=dummy_vector,
#     top_k=5,
#     include_metadata=True
# )
# print(result)
# print(f"Connecting to host: {os.getenv('PINECONE_INDEX_HOST')}")
import asyncio
import os
from pinecone import Pinecone
from dotenv import load_dotenv
load_dotenv()

async def test():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(
        name="vendor-contracts-intelligence",
        host=os.getenv("PINECONE_INDEX_HOST")
    )
    stats = await asyncio.to_thread(index.describe_index_stats)
    print(f"Stats: {stats}")

asyncio.run(test())