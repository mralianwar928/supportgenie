from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from src.geniesupport.config import EMBED_MODEL, PERSIST_DIR, TOP_K

import warnings
warnings.filterwarnings("ignore", message="Relevance scores must be between 0 and 1")

_embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
_vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=_embeddings)

def retrieve_with_scores(query: str, k: int = TOP_K):
    """Return [(Document, relevance_score), ...] with score ~0-1 (higher = more relevant)."""
    return _vectordb.similarity_search_with_relevance_scores(query, k=k)