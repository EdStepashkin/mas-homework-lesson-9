"""
Knowledge ingestion pipeline.

Loads documents from data/ directory, splits into chunks,
generates embeddings, and saves the index to disk.

Usage: python ingest.py
"""

import os
import pickle
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from config import settings

def ingest():
    print(f"Loading documents from {settings.data_dir}...")
    loader = PyPDFDirectoryLoader(settings.data_dir)
    docs = loader.load()
    if not docs:
        print("No documents found to ingest!")
        return

    print(f"Loaded {len(docs)} documents.")

    print(f"Splitting documents into chunks of size {settings.chunk_size} with overlap {settings.chunk_overlap}...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Generated {len(chunks)} chunks.")

    print(f"Generating embeddings using {settings.embedding_model} and building FAISS index...")
    
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(settings.index_dir, exist_ok=True)
    
    print(f"Saving vector store to {settings.index_dir}...")
    vectorstore.save_local(settings.index_dir)
    
    # Save chunks for BM25 retriever
    chunks_path = os.path.join(settings.index_dir, "chunks.pkl")
    print(f"Saving chunks for BM25 to {chunks_path}...")
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)

    print("Ingestion complete!")

if __name__ == "__main__":
    ingest()
