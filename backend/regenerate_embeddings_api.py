"""
Regenerate ChromaDB embeddings using Google Gemini API
This creates embeddings compatible with the API-based search for Render deployment
"""

import os
import json
import google.generativeai as genai
import chromadb
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configure Google Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment")

genai.configure(api_key=api_key)

print("=" * 80)
print("Regenerating ChromaDB Embeddings with Google Gemini API")
print("=" * 80)

# Load assessments
json_file = "data/scraped_assessments_complete.json"
with open(json_file, 'r', encoding='utf-8') as f:
    assessments = json.load(f)

print(f"✓ Loaded {len(assessments)} assessments")

# Initialize ChromaDB
chroma_dir = "./chroma_db"
client = chromadb.PersistentClient(path=chroma_dir)

# Delete existing collection
try:
    client.delete_collection(name="shl_assessments")
    print("✓ Deleted existing collection")
except:
    pass

# Create new collection
collection = client.create_collection(
    name="shl_assessments",
    metadata={"hnsw:space": "cosine"}
)
print("✓ Created new collection")

# Prepare documents and metadata
ids = []
documents = []
metadatas = []

for i, assessment in enumerate(assessments):
    # Create document text
    parts = []
    if assessment.get('name'):
        parts.append(assessment['name'])
    
    test_type = assessment.get('test_type')
    if test_type:
        if isinstance(test_type, list):
            parts.append(', '.join(test_type))
        else:
            parts.append(str(test_type))
    
    if assessment.get('description'):
        parts.append(assessment['description'])
    
    doc_text = " | ".join(parts)
    
    ids.append(f"assessment_{i}")
    documents.append(doc_text)
    
    # Metadata
    metadata = {
        'assessment_name': assessment.get('name', ''),
        'url': assessment.get('url', ''),
        'test_type': ', '.join(assessment.get('test_type', [])) if isinstance(assessment.get('test_type'), list) else assessment.get('test_type', ''),
        'description': assessment.get('description', ''),
        'duration': assessment.get('duration'),
        'adaptive_support': assessment.get('adaptive_support', 'No'),
        'remote_support': assessment.get('remote_support', 'No')
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}
    metadatas.append(metadata)

print(f"✓ Prepared {len(documents)} documents")

# Generate embeddings using Google Gemini API
print("\nGenerating embeddings with Google Gemini API...")
print("This may take a few minutes...")

embeddings = []
batch_size = 10  # Process in small batches to avoid rate limits

for i in tqdm(range(0, len(documents), batch_size)):
    batch = documents[i:i+batch_size]
    
    # Generate embeddings for batch
    for doc in batch:
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=doc,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        except Exception as e:
            print(f"\nError on document {i}: {e}")
            raise

print(f"\n✓ Generated {len(embeddings)} embeddings")

# Add to ChromaDB
print("Adding to ChromaDB...")
collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)

print(f"\n{'='*80}")
print(f"✓ Successfully embedded {collection.count()} assessments!")
print(f"✓ Embeddings are now compatible with Google Gemini API search")
print(f"{'='*80}")

# Test search
print("\nTesting search...")
test_query = "Python programming"
result = genai.embed_content(
    model="models/text-embedding-004",
    content=test_query,
    task_type="retrieval_query"
)
query_embedding = result['embedding']

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

print(f"\nTop 5 results for '{test_query}':")
for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"{i+1}. {metadata['assessment_name']} ({metadata.get('test_type', 'N/A')})")

print("\n✓ Everything working! Ready to deploy to Render.")
