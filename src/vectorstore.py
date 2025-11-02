from datetime import datetime
import os
from langchain_community.vectorstores import Chroma
# from dotenv import load_dotenv
import chromadb
import uuid
import warnings



class VectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        # ensure persist dir exists for chroma client if needed
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.Client(chromadb.config.Settings(persist_directory=persist_directory))
        self.collection = None

    def create_collection(self, name, embedding_function=None, description=""):
        # Try to reuse an existing collection if present to avoid duplicates
        try:
            # preferred: get_collection if available in this chromadb version
            existing = self.client.get_collection(name)
            self.collection = existing
            warnings.warn(f"Reusing existing collection '{name}'.")
            return
        except Exception:
            # fallback: inspect list_collections (older/newer chromadb versions)
            try:
                cols = self.client.list_collections()
                for c in cols:
                    if c.get("name") == name:
                        # attempt to retrieve the collection object
                        try:
                            self.collection = self.client.get_collection(name)
                        except Exception:
                            # some client implementations return the collection info only;
                            # create_collection will return the actual collection object if needed
                            pass
                        warnings.warn(f"Reusing existing collection '{name}' found in list_collections.")
                        return
            except Exception:
                # if list_collections not available or fails, continue to create
                pass

        # Not found — create a new collection (embedding_function optional)
        kwargs = {
            "name": name,
            "metadata": {
                "description": description,
                "created": str(datetime.now())
            }
        }
        if embedding_function is not None:
            kwargs["embedding_function"] = embedding_function
        self.collection = self.client.create_collection(**kwargs)

    def add_documents(self, documents):
        if self.collection is None:
            raise ValueError("Collection not created. Call create_collection first.")
        
        if len(documents) == 0:
            return

        # support objects with .page_content or plain strings
        if hasattr(documents[0], "page_content"):
            docs = [doc.page_content for doc in documents]
        else:
            docs = [str(d) for d in documents]

        # compute stable start index using existing ids if available
        try:
            existing = self.collection.get(include=["ids"])
            start_idx = len(existing.get("ids", []))
        except Exception:
            start_idx = 0

        ids = [str(start_idx + i) for i in range(len(docs))]

        self.collection.add(
            documents=docs,
            ids=ids
        )

    def query(self, query_texts, n_results=4):
        if self.collection is None:
            raise ValueError("Collection not created. Call create_collection first.")
        
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )


# --- convenience helpers and module-level collection for chain.py to import ---

vector_store = VectorStore()
collection = None  # will be set after initialization


def _get_openai_embedding_function():
    """
    Try to create a chromadb OpenAIEmbeddingFunction using OPENAI_API_KEY env var.
    Returns embedding function instance or raises RuntimeError if unavailable.
    """
    try:
        from chromadb.utils import embedding_functions
    except Exception as e:
        raise RuntimeError("chromadb.utils.embedding_functions is required for OpenAI embeddings") from e

    # safer lookup (avoid KeyError) and avoid printing the secret
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Add OPENAI_API_KEY to your .env or export it before running Streamlit.\n"
            "Example (PowerShell): $env:OPENAI_API_KEY='sk-...'\n"
            "Then restart the Streamlit server."
        )

    ef = embedding_functions.OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")
    return ef


def init_vectorstore(persist_directory="./chroma_db", collection_name="yt_collection",
                     description="YouTube transcripts", embedding_function=None):
    """
    Initialize the module-level vectorstore and collection.
    If embedding_function is None, this attempts to build an OpenAI embedding function
    from the OPENAI_API_KEY env var. If that fails, it still creates the collection
    without an embedding function (you can add embeddings later).
    Returns the created collection.
    """
    global vector_store, collection
    vector_store = VectorStore(persist_directory=persist_directory)

    if embedding_function is None:
        try:
            embedding_function = _get_openai_embedding_function()
        except Exception as e:
            warnings.warn(f"Could not create OpenAI embedding function: {e}. Creating collection without embedding function.")
            embedding_function = None

    print(f"Collection Name: {collection_name}")

    vector_store.create_collection(name=collection_name, embedding_function=embedding_function, description=description)
    collection = vector_store.collection
    return collection, vector_store

def add_documents_to_vector_store(vector_store, documents):
    """
    Add documents to the provided vector_store (VectorStore instance).
    """
    vector_store.add_documents(documents)

# Try to auto-initialize only if OPENAI_API_KEY is set; otherwise don't fail import.
try:
    if os.environ.get("OPENAI_API_KEY") is not None and collection is None:
        init_vectorstore()
except Exception:
    collection = None


if __name__ == "__main__":
    # quick CLI check
    print("OPENAI_API_KEY set:", bool(os.environ.get("OPENAI_API_KEY")))
    try:
        col = init_vectorstore()
        print("Collection created:", col.name if hasattr(col, "name") else repr(col))
    except Exception as e:
        print("Failed to init vectorstore:", e)