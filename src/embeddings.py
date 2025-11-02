import os
from langchain_openai import OpenAIEmbeddings
import chromadb
from chromadb.config import Settings
from datetime import datetime

def create_embeddings(transcript_chunks):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return [embeddings.embed(chunk) for chunk in transcript_chunks]

def store_embeddings_in_vector_store(embeddings, collection_name="yt_collection"):
    client = chromadb.Client(Settings(persist_directory="./chroma_db"))
    collection = client.create_collection(
        name=collection_name,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        metadata={
            "description": "YouTube video transcript embeddings",
            "created": str(datetime.now())
        }
    )
    collection.add(
        documents=embeddings,
        ids=[str(i) for i in range(len(embeddings))]
    )