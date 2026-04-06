"""
Hybrid retrieval module.

Combines semantic search (vector DB) + BM25 (lexical) + cross-encoder reranking.
"""

import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_classic.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever

from config import settings

def get_retriever():
    print("Loading FAISS index...")
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    vectorstore = FAISS.load_local(
        settings.index_dir, 
        embeddings, 
        allow_dangerous_deserialization=True # Need this since we trust our own local index
    )
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": settings.retrieval_top_k})

    print("Loading BM25 chunks...")
    chunks_path = os.path.join(settings.index_dir, "chunks.pkl")
    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)
    
    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = settings.retrieval_top_k

    print("Combining into EnsembleRetriever...")
    # Weights for hybrid search: 50% semantic, 50% keyword
    ensemble_retriever = EnsembleRetriever(
        retrievers=[faiss_retriever, bm25_retriever], weights=[0.5, 0.5]
    )

    print("Initializing CrossEncoder Reranker...")
    # Using the cross-encoder specified in the assignment
    model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
    compressor = CrossEncoderReranker(model=model, top_n=settings.rerank_top_n)

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=ensemble_retriever
    )

    return compression_retriever

if __name__ == "__main__":
    # Test script
    retriever = get_retriever()
    query = "Що таке RAG і які є підходи до retrieval?"
    docs = retriever.invoke(query)
    for i, doc in enumerate(docs):
        print(f"\n--- Document {i+1} ---\n{doc.page_content[:200]}...")
