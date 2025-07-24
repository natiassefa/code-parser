import chromadb
from chromadb.utils import embedding_functions

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./.chroma_db")

# Get the collection
try:
    collection = client.get_collection("code_chunks")
    print("✅ Found existing collection: code_chunks")
    
    # Get collection info
    count = collection.count()
    print(f"📊 Total embeddings stored: {count}")
    
    if count > 0:
        # test query
        print(collection.query(query_texts=['what is the purpose of the codebase'], n_results=5))
        
except Exception as e:
    print(f"❌ No collection found or error: {e}")
    print("\n💡 The embeddings might not have been created yet.")
    print("   Run the pipeline first: ts-node run_pipeline.ts") 