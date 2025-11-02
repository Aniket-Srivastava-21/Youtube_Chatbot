from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI
import os, openai
import config  # ensure load_dotenv() runs and OPENAI_API_KEY is available

# ensure env var is populated (use config value if present)
if getattr(config, "OPENAI_API_KEY", None) and not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
    print(config.OPENAI_API_KEY)

from langchain_core.output_parsers import StrOutputParser
from vectorstore import collection  # Assuming collection is defined in vectorstore.py
import sys


def join_docs(retrieved_docs):
    context_text = "\n\n".join(retrieved_docs["documents"][0])
    return context_text

def query_collection(question):
    return collection.query(
        query_texts=question,
        n_results=4
    )

parallel_chain = RunnableParallel({
    'context': RunnableLambda(query_collection) | RunnableLambda(join_docs),
    'query': RunnablePassthrough()
})

def main_chain_function(query):
    return parallel_chain.invoke(query)

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter query: ")
    result = main_chain_function(query)
    print(result)

if __name__ == "__main__":
    main()

# --- add this wrapper so streamlit_app.imports work ---
def query_chain(query, vector_store=None, n_results=4):
    """
    Retrieve context for `query` from the provided vector_store or the module-level collection,
    then try to generate an answer using OpenAI (if OPENAI_API_KEY is set). Falls back to
    returning the formatted prompt/context if no LLM is available.
    """
    # resolve chroma collection: either a chromadb.Collection object or a wrapper with .collection
    col = None
    if vector_store is not None:
        col = getattr(vector_store, "collection", None) or vector_store
    if col is None:
        try:
            from vectorstore import collection as module_collection
            col = module_collection
        except Exception:
            col = None

    if col is None:
        raise RuntimeError("No vector store collection available. Call init_vectorstore() or pass vector_store to query_chain.")

    # query the collection
    retrieved = col.query(query_texts=[query], n_results=n_results)
    docs = retrieved.get("documents", [[]])[0]
    context = "\n\n".join(docs)

    # build prompt using prompt.default_prompt if available
    try:
        from prompt import default_prompt
        prompt_text = default_prompt().format(context=context, query=query)
    except Exception:
        prompt_text = f"Context: {context}\n\nQuery: {query}"

    # try to call ChatOpenAI (basic fallback). Requires OPENAI_API_KEY in env.
    try:
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        if openai.api_key:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
            # print(f"Prompt: {prompt_text}")
            response = llm.invoke(prompt_text)
            print(response)
            return response.content
    except Exception as e:
        raise RuntimeError(f"Failed to get a response from ChatOpenAI. Error: {e}")

    # final fallback: return the assembled prompt/context so UI shows something useful
    return prompt_text