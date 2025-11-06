# app.py - Streamlit Web Interface

import streamlit as st
from rag_system import EnhancedRAGSystem
from auth import authenticate_google_drive
from config import INDEXED_FOLDERS_FILE, TOP_K_RESULTS
import time
import os
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Google Drive RAG Agent", # <-- Renamed
    page_icon="🤖",
    layout="wide"
)

# --- Caching Functions (UNCHANGED) ---
@st.cache_resource
def init_drive_service():
    with st.spinner("Authenticating Google Drive..."):
        try:
            drive_service = authenticate_google_drive()
            return drive_service
        except Exception as e:
            st.error(f"Google Drive Authentication Failed: {e}")
            st.stop()

@st.cache_data
def load_indexed_folders():
    if not os.path.exists(INDEXED_FOLDERS_FILE):
        return {}
    with open(INDEXED_FOLDERS_FILE, 'r') as f:
        return json.load(f)

@st.cache_resource
def init_rag_system(_drive_service, collection_name, display_name):
    with st.spinner(f"Loading expert agent for '{display_name}'..."): # <-- Renamed
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

st.title("🤖 Google Drive Q&A Agent") # <-- Renamed
st.caption("Powered by Google Gemini Agents, ChromaDB, and Streamlit")

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
    "**Select an Agent Topic:**", # <-- Renamed
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

# --- ✅ FIX: Added st.session_state.chat_history for agent memory ---
if "messages" not in st.session_state or st.session_state.get("current_topic") != selected_folder_id:
    st.session_state.messages = []       # For display
    st.session_state.chat_history = []  # For agent memory
    st.session_state.current_topic = selected_folder_id
    st.info(f"Chat agent set to: **{display_name}**")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(f"Ask a complex question about '{display_name}'..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent is thinking and using tools..."):
            
            start_time = time.time()
            
            # --- ✅ FIX: Get current history from session state ---
            current_history = st.session_state.get("chat_history", [])
            
            # --- ✅ FIX: Pass the history to the agent ---
            result = rag.query(prompt, chat_history=current_history) 
            
            end_time = time.time()
            
            # --- ✅ FIX: Save the updated history back to session state ---
            st.session_state.chat_history = result.get('chat_history', [])
            
            # The agent's final answer *already contains* citations.
            full_response = result.get('answer', "I wasn't able to find an answer.")
            
            full_response += f"\n\n*Agent task completed in {end_time - start_time:.2f} seconds.*"

            st.markdown(full_response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_response})