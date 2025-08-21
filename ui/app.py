import logging
import traceback

logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('app.log', mode='w')  # Output to a file
    ]
)
logger = logging.getLogger(__name__)

import shutil
import streamlit as st
import time
import os
import sys
import json
from pathlib import Path

# Add project root to sys.path to fix module imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import PERSONAS_DIR, CHROMA_DIR
from src.ingestion_local import process_local_files


# --- Page Configuration ---
st.set_page_config(
    page_title="Persona AI",
    page_icon="🧠",
    layout="wide"
)

# --- Custom CSS for Shimmering Text Effect ---
def shimmering_text_css():
    """Injects CSS for the shimmering gradient text effect."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap');
    
    .shimmer {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 3em;
        text-align: center;
        color: rgba(255, 255, 255, 0.1);
        background: -webkit-linear-gradient(45deg, #7F00FF, #E100FF, #00BFFF, #E100FF, #7F00FF);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 400% 100%;
        animation: shimmer_animation 5s ease-in-out infinite alternate;
        -webkit-animation: shimmer_animation 5s ease-in-out infinite alternate;
    }

    @keyframes shimmer_animation {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Initialization ---
if 'selected_persona' not in st.session_state:
    st.session_state.selected_persona = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- Helper Functions ---
def get_personas():
    try:
        personas = [name for name in os.listdir(PERSONAS_DIR) 
                    if os.path.isdir(os.path.join(PERSONAS_DIR, name))]
        return sorted(personas)
    except FileNotFoundError:
        os.makedirs(PERSONAS_DIR, exist_ok=True)
        return []

# --- Backend Functions ---
def create_new_persona_backend(name, source_type, files=None, url=None):
    """
    Creates a new persona with improved error handling and cleanup.
    """
    logger.debug(f"Starting create_new_persona_backend: name='{name}', source_type='{source_type}', files={files}, url={url}")
    
    if not name.strip():
        st.error("Persona name cannot be empty.")
        logger.error("Persona name is empty")
        return False
    
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    logger.debug(f"Safe name generated: {safe_name}")
    if not safe_name:
        st.error("Persona name contains invalid characters.")
        logger.error("Invalid persona name after sanitization")
        return False
    
    if safe_name in get_personas():
        st.error(f"Persona '{safe_name}' already exists.")
        logger.error(f"Persona '{safe_name}' already exists")
        return False

    if source_type == "Upload_Files" and not files:
        st.error("Please upload at least one file.")
        logger.error("No files uploaded for 'Upload Files' source type")
        return False
    if source_type == "Fetch from Web" and (not url or not url.strip()):
        st.error("Please provide a valid URL.")
        logger.error("No valid URL provided for 'Fetch from Web' source type")
        return False

    persona_dir = os.path.join(PERSONAS_DIR, safe_name)
    logger.debug(f"Persona directory: {persona_dir}")
    
    meta_source_type = "local" if source_type == "Upload_Files" else "web"
    metadata = {
        "name": name, 
        "source_type": meta_source_type, 
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"), 
        "sources": []
    }
    
    if meta_source_type == "local" and files:
        metadata["sources"] = [{"type": "file", "name": file.name} for file in files]
    elif meta_source_type == "web" and url:
        metadata["sources"] = [{"type": "url", "value": url}]
    logger.debug(f"Metadata prepared: {metadata}")

    st.toast(f"Creating persona '{name}'...")
    
    try:
        logger.debug(f"Creating directory: {os.path.join(persona_dir, CHROMA_DIR)}")
        os.makedirs(os.path.join(persona_dir, CHROMA_DIR), exist_ok=True)
        
        logger.debug(f"Writing metadata to {os.path.join(persona_dir, 'info.json')}")
        with open(os.path.join(persona_dir, "info.json"), "w") as f:
            json.dump(metadata, f, indent=4)
        
        with st.spinner(f"Ingesting documents for '{name}'... This may take a while."):
            logger.debug(f"Source type: {meta_source_type}")
            if meta_source_type == "local":
                logger.debug("Calling process_local_files...")
                success = process_local_files(safe_name, files)
                logger.debug(f"process_local_files returned: {success}")
            # elif meta_source_type == "web":
            #     success = process_web_url(safe_name, url)
            else:
                logger.error(f"Invalid source type: {meta_source_type}")
                success = False
        
        if success:
            st.success(f"Persona '{name}' created successfully!")
            logger.info(f"Persona '{name}' created successfully")
            return True
        else:
            logger.error(f"Failed to process documents for '{name}'")
            if os.path.exists(persona_dir):
                logger.debug(f"Cleaning up directory: {persona_dir}")
                shutil.rmtree(persona_dir)
            st.error(f"Failed to process documents for '{name}'. Directory cleaned up. Please check the error details above.")
            return False
            
    except Exception as e:
        logger.error(f"Error creating persona '{name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if os.path.exists(persona_dir):
            logger.debug(f"Cleaning up directory: {persona_dir}")
            shutil.rmtree(persona_dir)
        st.error(f"Error creating persona '{name}': {str(e)}")
        st.error("Check the console or app.log for detailed error information.")
        return False

def delete_persona_backend(name):
    # This will be expanded later to delete the actual folder
    st.toast(f"Persona '{name}' has been removed (mock).")

def get_ai_response_backend(persona, user_message, chat_history):
    return f"This is a mock response from **{persona}**. You said: '{user_message}'"

# --- UI Screen Functions ---


def show_main_page():
    shimmering_text_css()
    st.markdown('<h1 class="shimmer">Who do you want me to be?</h1>', unsafe_allow_html=True)
    st.info("Create a new persona below, or select an existing one from the sidebar to begin chatting.")
    st.header("Create a New Persona")

    name = st.text_input("Persona Name", placeholder="e.g., My Mom, Albert Einstein")
    source_type = st.radio("Select Data Source", ['Upload_Files', 'Fetch_from_Web'], horizontal=True)
    
    files = None
    url = None
    
    if source_type == 'Upload_Files':
        files = st.file_uploader(
            "Upload documents (.pdf, .txt)", 
            accept_multiple_files=True, 
            type=['pdf', 'txt'],  # Explicitly specify accepted types
            label_visibility="collapsed"
        )
        
        # Show file preview
        if files:
            st.write("📁 **Selected Files:**")
            for i, file in enumerate(files):
                file_size = len(file.getvalue())
                st.write(f"   {i+1}. {file.name} ({file.type}, {file_size:,} bytes)")
                file.seek(0)  # Reset file pointer
    else:
        url = st.text_input(
            "Website URL", 
            placeholder="e.g., https://www.gutenberg.org/ebooks/3600", 
            label_visibility="collapsed"
        )
    
    if st.button("Create Persona", type="primary"):
        if create_new_persona_backend(name, source_type, files=files, url=url):
            for key in ["persona_name", "persona_source_type", "persona_files", "persona_url"]:
                st.session_state.pop(key, None)

            # Go directly to chat with this persona
            st.session_state.selected_persona = name
            st.session_state.chat_history = []
            st.rerun()

def show_chat_screen():
    st.header(f"Conversing with: *{st.session_state.selected_persona}*")
    # Chat history and input logic remains the same
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("What would you like to ask?"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                response = get_ai_response_backend(st.session_state.selected_persona, prompt, st.session_state.chat_history)
                st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

@st.dialog("Confirm Deletion")
def confirm_delete(name):
    st.warning(f"Are you sure you want to delete the persona: **{name}**?")
    if st.button("Yes, Delete", type="primary"):
        delete_persona_backend(name)
        st.rerun()
    if st.button("Cancel"):
        st.rerun()

# --- Sidebar & Main Router ---
with st.sidebar:
    st.title("Persona AI")
    st.header("Your Personas")
    if st.session_state.selected_persona:
        if st.button("🏠 Back to Main Page", use_container_width=True):
            st.session_state.selected_persona = None
            st.rerun()
    st.divider()
    for name in get_personas():
        col1, col2 = st.columns([4, 1])
        if col1.button(name, key=f"select_{name}", use_container_width=True):
            st.session_state.selected_persona = name
            st.session_state.chat_history = []
            st.rerun()
        if col2.button("❌", key=f"delete_{name}", use_container_width=True):
            confirm_delete(name)

if st.session_state.selected_persona is None:
    show_main_page()
else:
    show_chat_screen()