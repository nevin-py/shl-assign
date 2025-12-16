import chromadb
import json

print("Updating ChromaDB with clean data from JSON...")

# Load JSON data
with open('data/scraped_assessments_complete.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

print(f"Loaded {len(json_data)} assessments from JSON")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("shl_assessments")

# Get current ChromaDB data
current_data = collection.get()
print(f"Current ChromaDB has {len(current_data['ids'])} records")

# Update all metadata to ensure consistency
print("\nUpdating ChromaDB metadata...")
updated_count = 0

for assessment in json_data:
    # Find matching record in ChromaDB by URL
    name = assessment['name']
    url = assessment['url']
    
    # Try to find by URL first
    matches = collection.get(where={"url": url})
    
    if matches['ids']:
        assessment_id = matches['ids'][0]
        
        # Prepare metadata with correct types
        metadata = {
            'assessment_name': name,
            'url': url,
            'description': assessment['description'],
            'duration': assessment['duration'],
            'adaptive_support': assessment['adaptive_support'],  # String: "Yes" or "No"
            'remote_support': assessment['remote_support'],      # String: "Yes" or "No"
            'test_type': ', '.join(assessment['test_type']) if isinstance(assessment['test_type'], list) else assessment['test_type']
        }
        
        # Update ChromaDB
        collection.update(
            ids=[assessment_id],
            metadatas=[metadata],
            documents=[assessment['description']]  # Use description as the document for embedding
        )
        
        updated_count += 1
        if updated_count % 50 == 0:
            print(f"  Updated {updated_count}/{len(json_data)}...")
    else:
        print(f"  ⚠️ Warning: Could not find {name} in ChromaDB")

print(f"\n✅ Updated {updated_count} records in ChromaDB")

# Verify a few entries
print("\nVerifying updated entries:")
test_names = ["UNIX (New)", "Automata Data Science (New)", "Python (New)"]
for name in test_names:
    results = collection.get(where={"assessment_name": name})
    if results['ids']:
        meta = results['metadatas'][0]
        print(f"\n{name}:")
        print(f"  Adaptive: {meta.get('adaptive_support')} (type: {type(meta.get('adaptive_support')).__name__})")
        print(f"  Remote: {meta.get('remote_support')} (type: {type(meta.get('remote_support')).__name__})")
        print(f"  Duration: {meta.get('duration')}")
        print(f"  Test Type: {meta.get('test_type')}")
    else:
        print(f"  ❌ Not found in ChromaDB")

print("\n✅ ChromaDB update complete!")
