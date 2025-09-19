# src/retriever.py

import os
import logging
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer

# Configure logging
logger = logging.getLogger()

# Define a fallback retriever function for when dependencies are not available
def retrieve_chunks(query: str, k: int = 5) -> List[str]:
    """
    Query for top-k chunks matching the query. This is a fallback version that returns
    empty results if the dependencies aren't available.
    
    Returns an empty list when:
    1. ChromaDB is not installed
    2. SentenceTransformer is not installed
    3. No database exists at the specified path
    """
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode(query)
        
        embeddings_dir = os.path.join(os.path.dirname(__file__), 'embeddings')
        if not os.path.exists(embeddings_dir):
            logger.warning(f"Embeddings directory not found: {embeddings_dir}")
            return []
        
        chunks = []
        for filename in os.listdir(embeddings_dir):
            if filename.endswith('.npy'):
                embedding_path = os.path.join(embeddings_dir, filename)
                chunk_embedding = np.load(embedding_path)
                
                similarity = np.dot(query_embedding, chunk_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding))
                chunks.append((similarity, filename))
        
        chunks.sort(reverse=True)
        top_k_chunks = chunks[:k]
        
        retrieved_texts = []
        for _, filename in top_k_chunks:
            text_path = os.path.join(embeddings_dir, filename.replace('.npy', '.txt'))
            if os.path.exists(text_path):
                with open(text_path, 'r', encoding='utf-8') as f:
                    retrieved_texts.append(f.read())
        
        return retrieved_texts
    except Exception as e:
        logger.error(f"Error in retrieve_chunks: {e}")
        return []