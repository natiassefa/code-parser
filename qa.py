#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# load env
load_dotenv()

# ---------- LLM backends ----------
def generate_with_anthropic(system_prompt: str, user_prompt: str, model: str = "claude-3-5-sonnet-20240620") -> str:
    from anthropic import Anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=1000
    )
    return resp.content[0].text

def generate_with_openai(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> str:
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
        )
    return resp.choices[0].message.content.strip()

def generate_with_ollama(system_prompt: str, user_prompt: str, model: str = "mistral:7b") -> str:
    import requests
    url = "http://127.0.0.1:11434/api/generate"
    prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}"

    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["response"].strip()
# ---------- Retrieval + Prompting ----------

SYSTEM_PROMPT = """You are a senior code assistant with expertise in multiple programming languages. You will answer questions about a codebase using ONLY the provided context snippets.

The context includes code chunks with the following format:
- Language and type (e.g., PYTHON function, GO method, RUST struct)
- Name of the code construct (when available)
- File path and line range
- The actual code content

Key guidelines:
1. Pay attention to the language context - different languages have different patterns and conventions
2. Use the file path and line range to understand code organization
3. Consider the relationship between different code constructs
4. If the answer is not in the provided context, say "I don't know based on the provided context."
5. Cite specific files, functions, and line ranges when referencing code."""

USER_PROMPT_TEMPLATE = """Question:
{question}

Context (top {k} results):
{context}

Instructions:
- Cite the file and symbol names you used.
- If unsure, say "I don't know based on the provided context."
"""

def format_context(docs: List[str], metas: List[Dict[str, Any]]) -> str:
    blocks = []
    for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
        file = meta.get("file")
        name = meta.get("name")
        kind = meta.get("kind")
        language = meta.get("language", "unknown")
        rng = meta.get("range")
        
        # Enhanced context formatting
        language_upper = language.upper()
        
        # Create descriptive context header
        if name and name != kind and name not in ["import", "assignment", "if", "for", "while", "try", "with", "lambda", "list", "dict", "set", "tuple", "assert", "raise", "return", "yield", "expression"]:
            # For named constructs (functions, classes, etc.)
            context_header = f"[{i}] {language_upper} {kind}: {name}"
        else:
            # For unnamed constructs or generic ones
            context_header = f"[{i}] {language_upper} {kind}"
        
        # Add file and line information
        context_header += f" in {file} (lines {rng})"
        
        # Format the code block with better structure
        code_block = doc.strip()
        
        # Add the formatted block
        blocks.append(f"{context_header}\n---\n{code_block}\n")
    
    return "\n\n".join(blocks)

def ask(
    question: str,
    collection_name: str,
    persist_dir: str,
    top_k: int,
    backend: str,
    model: str,
) -> str:
    client = chromadb.PersistentClient(path="./.chroma_db")
    col = client.get_collection(collection_name)

    res = col.query(query_texts=[question], n_results=top_k)
    documents = res["documents"][0]
    metadatas = res["metadatas"][0]
    # distances = res["distances"][0]  # if you want to show scores

    context = format_context(documents, metadatas)
    user_prompt = USER_PROMPT_TEMPLATE.format(question=question, k=top_k, context=context)

    if backend == "openai":
        return generate_with_openai(SYSTEM_PROMPT, user_prompt)
    elif backend == "ollama":
        return generate_with_ollama(SYSTEM_PROMPT, user_prompt, model=model)
    elif backend == "anthropic":
        return generate_with_anthropic(SYSTEM_PROMPT, user_prompt)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

# ---------- CLI / REPL ----------

def main():
    parser = argparse.ArgumentParser(description="RAG over your code chunks (Chroma + LLM).")
    parser.add_argument("--question", "-q", type=str, help="Your question. If omitted, starts an interactive REPL.")
    parser.add_argument("--collection", "-c", type=str, default="code_chunks", help="Chroma collection name.")
    parser.add_argument("--persist-dir", "-p", type=str, default=".chroma", help="Chroma persist directory.")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Top K results to retrieve.")
    parser.add_argument("--backend", "-b", type=str, choices=["openai", "ollama", "anthropic"], default="ollama", help="LLM backend.")
    parser.add_argument("--model", "-m", type=str, default="llama3:latest", help="LLM model (e.g., llama3.1:8b or gpt-4o-mini).")
    args = parser.parse_args()
    print(args)

    # Example usage
    if args.question:
        answer = ask(args.question, args.collection, args.persist_dir, args.top_k, args.backend, args.model)
        print("\n=== Answer ===\n")
        print(answer)
        return

    # REPL
    print("RAG REPL. Type 'exit' to quit.")
    while True:
        try:
            q = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.strip().lower() in {"exit", "quit"}:
            break
        if not q.strip():
            continue
        try:
            answer = ask(q, args.collection, args.persist_dir, args.top_k, args.backend, args.model)
            print("\n=== Answer ===\n")
            print(answer)
            print("\n==============\n")
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)

if __name__ == "__main__":
    main()