import json
import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

# Load model
model = SentenceTransformer("BAAI/bge-small-en")  # Or "intfloat/e5-small-v2"
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en")

# Init Chroma
client = chromadb.PersistentClient(path="./.chroma_db")
collection = client.get_or_create_collection("code_chunks", embedding_function=embed_fn)

# Load all chunks from the chunks-output directory
chunks_dir = ".chunks-output"
chunks = []
for file in os.listdir(chunks_dir):
    if file.endswith(".json"):
        with open(os.path.join(chunks_dir, file), "r") as f:
            chunks.extend(json.load(f))

# Ingest
for i, chunk in enumerate(chunks):
    # Extract language from filePath extension
    file_ext = os.path.splitext(chunk['filePath'])[1].lower()
    language_map = {
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.py': 'python',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
        '.kt': 'kotlin',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.zig': 'zig',
        '.hs': 'haskell'
    }
    language = language_map.get(file_ext, 'unknown')
    
    # Convert range to string format for ChromaDB
    range_str = f"{chunk['range']['start']['line']}-{chunk['range']['end']['line']}"
    
    collection.add(
        ids=[f"{chunk['filePath']}::{chunk['name'] or 'anon'}"],
        documents=[chunk["code"]],
        metadatas=[{
            "file": chunk["filePath"],
            "name": chunk["name"],
            "kind": chunk["kind"],
            "range": range_str,
            "language": language,
        }]
    )

print("✅ Embedded and stored all chunks.")

