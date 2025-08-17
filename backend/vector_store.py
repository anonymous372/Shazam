import os
from pinecone import Pinecone, ServerlessSpec
import uuid

# Initialize Pinecone client
api_key = os.environ.get("PINECONE_API_KEY", "")
pc = Pinecone(api_key=api_key) if api_key else None

INDEX_NAME = "shazam-kishore-v2"

def get_safe_id(song_name, chunk_index):
    # Create an MD5 hash of the song name to ensure it's strictly ASCII
    safe_hash = hashlib.md5(song_name.encode('utf-8')).hexdigest()
    return f"{safe_hash}_chunk_{chunk_index}"

def get_index():
    if not pc:
        raise ValueError("PINECONE_API_KEY environment variable is not set!")
    
    # Check if index exists, if not create it
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating Pinecone index '{INDEX_NAME}'...")
        # Wav2Vec2 embedding size is 768, metric is cosine similarity
        pc.create_index(
            name=INDEX_NAME,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    return pc.Index(INDEX_NAME)

def upsert_vectors(index, vectors_with_metadata):
    """
    Upserts a list of dictionaries containing embeddings and metadata into Pinecone.
    vectors_with_metadata format: 
    [ {"id": "chunk_0", "values": [0.1, 0.2...], "metadata": {"song": "Title", "start": 0}} ]
    """
    # Pinecone allows batch upserts. We upsert in batches of 100.
    batch_size = 100
    for i in range(0, len(vectors_with_metadata), batch_size):
        batch = vectors_with_metadata[i:i + batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted {len(batch)} vectors.")

def search_song(index, query_embedding, top_k=5):
    """
    Searches the Pinecone index for the closest audio chunks to the hummed query.
    Returns the top matches.
    """
    response = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return response.get('matches', [])
