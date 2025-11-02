import time
import streamlit as st
from extractor import download_transcript
from cleaner import extract_clean_subtitles, get_youtube_video_id
from splitter import RecursiveCharacterTextSplitter
from embeddings import create_embeddings
from vectorstore import init_vectorstore, add_documents_to_vector_store
from chain import query_chain

st.title("YouTube Chatbot")

st.sidebar.header("User Input")
video_url = st.sidebar.text_input("Enter YouTube Video URL:")

# helper to ensure progress state exists
if "progress" not in st.session_state:
    st.session_state.progress = 0

def _set_progress(p):
    st.session_state.progress = int(p)
    prog_bar.progress(st.session_state.progress)

prog_bar = st.sidebar.progress(st.session_state.progress)
status_text = st.sidebar.empty()

if st.sidebar.button("Download Transcript"):
    # reset progress and status
    _set_progress(0)
    status_text.info("Starting process...")

    if not video_url:
        status_text.error("Please enter a valid YouTube video URL.")
        _set_progress(0)
    else:
        try:
            status_text.info("Downloading subtitles...")
            _set_progress(10)
            with st.spinner("Downloading subtitles..."):
                transcript_file = download_transcript(video_url)
            if not transcript_file:
                status_text.error("Failed to download transcript.")
                _set_progress(0)
            else:
                status_text.success("Transcript downloaded.")
                _set_progress(30)

                status_text.info("Cleaning transcript...")
                with st.spinner("Cleaning subtitles..."):
                    transcript = extract_clean_subtitles(transcript_file)
                if not transcript:
                    status_text.error("Failed to clean transcript.")
                    _set_progress(0)
                else:
                    st.session_state.transcript = transcript
                    _set_progress(50)
                    status_text.info("Splitting transcript into chunks...")
                    with st.spinner("Splitting text..."):
                        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        chunks = splitter.create_documents([transcript])
                    st.session_state.chunks = chunks
                    _set_progress(70)
                    status_text.info(f"Initializing vector store and adding {len(chunks)} chunks...")
                    with st.spinner("Initializing vector store..."):
                        st.session_state.collection, st.session_state.vector_store = init_vectorstore(collection_name=f"{get_youtube_video_id(video_url)}_collection")
                    _set_progress(80)
                    with st.spinner("Adding documents to vector store..."):
                        add_documents_to_vector_store(st.session_state.vector_store, st.session_state.chunks)
                    _set_progress(100)
                    status_text.success("Indexing complete.")
        except Exception as e:
            status_text.error(f"Error: {e}")
            _set_progress(0)

if 'transcript' in st.session_state:

    user_query = st.text_input("Ask a question about the video:")
    if st.button("Get Answer"):
        if not user_query:
            st.error("Please enter a question.")
        else:
            # show progress for retrieval + answer generation
            answer_slot = st.empty()
            prog = st.empty()
            try:
                with st.spinner("Retrieving context and generating answer..."):
                    prog.info("Querying vector store...")
                    time.sleep(0.2)
                    prog.progress(25)
                    response = query_chain(user_query, st.session_state.vector_store)
                    prog.progress(100)
                answer_slot.subheader("Response")
                answer_slot.write(response)
            except Exception as e:
                st.error(f"Failed to get answer: {e}")
                prog.empty()