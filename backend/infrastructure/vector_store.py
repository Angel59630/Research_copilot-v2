from functools import lru_cache

import chromadb
from langchain_ollama import OllamaEmbeddings

from config import settings


COLLECTION_NAME = "paper_chunks"


@lru_cache
def chroma_client():
    settings.chroma_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return chromadb.PersistentClient(
        path=str(
            settings.chroma_dir
        )
    )


@lru_cache
def embedding_client() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.ollama_embed_model,
        base_url=settings.ollama_base_url,
    )


def collection():
    return chroma_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
        },
    )


async def add_chunks(
    chunks,
) -> None:
    if not chunks:
        return

    texts = [
        chunk.text
        for chunk in chunks
    ]

    vectors = (
        await embedding_client().aembed_documents(
            texts
        )
    )

    collection().upsert(
        ids=[
            chunk.chunk_id
            for chunk in chunks
        ],
        embeddings=vectors,
        documents=texts,
        metadatas=[
            {
                "paper_id": chunk.paper_id,
                "page_number":
                    chunk.page_number,
                "chunk_index":
                    chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )


def delete_paper_vectors(
    paper_id: str,
) -> None:
    collection().delete(
        where={
            "paper_id": paper_id,
        }
    )