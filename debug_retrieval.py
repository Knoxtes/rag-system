# app.py - Streamlit Web Interface

import streamlit as st
from rag_system import EnhancedRAGSystem
from auth import authenticate_google_drive
from config import INDEXED_FOLDERS_FILE
import time
import os
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Google Drive RAG",
    page_icon="💬",
    layout="wide"
)

# --- Caching Functions (UNCHANGED) ---

@st.cache_resource
def init_drive_service():
    """Authenticate and cache the Google Drive service."""
    with st.spinner("Authenticating Google Drive..."):
        try:
            drive_service = authenticate_google_drive()
            return drive_service
        except Exception as e:
            st.error(f"Google Drive Authentication Failed: {e}")
            st.stop()

@st.cache_data
def load_indexed_folders():
    """Load and cache the list of indexed folders from the JSON log."""
    if not os.path.exists(INDEXED_FOLDERS_FILE):
        return {}
    with open(INDEXED_FOLDERS_FILE, 'r') as f:
        return json.load(f)

@st.cache_resource
def init_rag_system(_drive_service, collection_name, display_name):
    """
    Initialize and cache the RAG system *per collection*.
    The display_name is just to make the spinner text nicer.
    """
    with st.spinner(f"Loading expert models for '{display_name}'..."):
        try:
            rag_system = EnhancedRAGSystem(
                drive_service=_drive_service,
                collection_name=collection_name
            )
            return rag_system
        except Exception as e:
            st.error(f"Failed to initialize RAG system: {e}")
            st.stop()

# --- Main App Logic (UNCHANGED) ---

st.title("💬 Google Drive Q&A System")
st.caption("Powered by Google Gemini, ChromaDB, and Streamlit")

drive_service = init_drive_service()
indexed_folders = load_indexed_folders()

if not indexed_folders:
    st.warning("⚠️ No folders have been indexed yet!")
    st.info("Please run `python main.py` from your terminal and select option 2 to index a folder.")
    st.stop()

topic_options = {
    folder_id: f"{info['name']} ({info['location']})"
    for folder_id, info in indexed_folders.items()
}

st.sidebar.title("Configuration")
selected_folder_id = st.sidebar.selectbox(
    "**Select a Chat Topic:**",
    options=topic_options.keys(),
    format_func=lambda folder_id: topic_options[folder_id],
    key="topic_selector"
)

if not selected_folder_id:
    st.info("Please select a chat topic from the sidebar to begin.")
    st.stop()

selected_info = indexed_folders[selected_folder_id]
collection_name = selected_info['collection_name']
display_name = topic_options[selected_folder_id]

rag = init_rag_system(drive_service, collection_name, display_name)

# --- Chat Interface (MODIFIED) ---

if "messages" not in st.session_state or st.session_state.get("current_topic") != selected_folder_id:
    st.session_state.messages = []
    st.session_state.current_topic = selected_folder_id
    st.info(f"Chat mode set to: **{display_name}**")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(f"Ask an expert question about '{display_name}'..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Searching, re-ranking, and performing expert analysis..."):
            
            chat_history = []
            for msg in st.session_state.messages[-4:-1]:
                chat_history.append(f"{msg['role'].title()}: {msg['content']}")

            start_time = time.time()
            result = rag.query(prompt, chat_history=chat_history)
            end_time = time.time()
            
            response_text = result.get('answer', "I wasn't able to find an answer.")
            
            # --- MODIFIED: Build full response ---
            full_response = response_text
            
            if result['files']:
                full_response += "\n\n---\n**Relevant Files:**\n"
                for file in result['files'][:5]: # Show top 5
                    source_label = file['source']
                    if file['source'] == 'RAG (Re-ranked)':
                        source_label = f"Indexed (Relevance: {file['relevance']:.2f})"
                    elif file['source'] == 'Drive (Live Search)':
                         source_label = "Live Search (in folder)"
                    
                    # NEW: Combine path and name
                    full_path_name = f"{file.get('file_path', '')}{file['file_name']}"
                    
                    full_response += (
                        f"1. **{full_path_name}**\n" # <-- UPDATED
                        f"   - *Source: {source_label}* | [Open Link]({file['drive_link']})\n"
                    )
            
            full_response += f"\n\n*Analysis generated in {end_time - start_time:.2f} seconds.*"

            st.markdown(full_response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_response})