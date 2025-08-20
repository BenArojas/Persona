import streamlit as st
import time
import os
import sys
import json
from pathlib import Path

# Add project root to sys.path to fix module imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import PERSONAS_DIR, CHROMA_DIR

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
if 'form_reset' not in st.session_state:
    st.session_state.form_reset = False
if 'files' not in st.session_state:
    st.session_state.files = None
if 'url' not in st.session_state:
    st.session_state.url = ""

# Function to get list of personas from personas/ directory
def get_personas():
    try:
        # List directories in PERSONAS_DIR, excluding non-folders
        personas = [name for name in os.listdir(PERSONAS_DIR) 
                    if os.path.isdir(os.path.join(PERSONAS_DIR, name))]
        return sorted(personas)  # Sort for consistent display
    except FileNotFoundError:
        os.makedirs(PERSONAS_DIR, exist_ok=True)
        return []

# --- Backend Functions ---
def create_new_persona_backend(name, source_type, files=None, url=None):
    """Create a new persona folder and metadata file."""
    # Validate persona name
    if not name.strip():
        st.error("Persona name cannot be empty.")
        return False
    # Sanitize name to avoid invalid characters in folder names
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    if not safe_name:
        st.error("Persona name contains invalid characters.")
        return False
    if safe_name in get_personas():
        st.error(f"Persona '{safe_name}' already exists.")
        return False
    if source_type not in ["local", "web"]:
        st.error("Please select exactly one data source (Upload Files or Fetch from Web).")
        return False
    if source_type == "local" and not files:
        st.error("Please upload at least one file.")
        return False
    if source_type == "web" and (not url or not url.strip()):
        st.error("Please provide a valid URL.")
        return False

    try:
        # Create persona folder and vectordb subfolder
        persona_dir = os.path.join(PERSONAS_DIR, safe_name)
        vector_dir = os.path.join(persona_dir, CHROMA_DIR)
        os.makedirs(vector_dir, exist_ok=True)

        # Prepare metadata
        metadata = {
            "name": name,
            "source_type": source_type,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sources": []
        }
        if source_type == "local" and files:
            metadata["sources"] = [{"type": "file", "name": file.name} for file in files]
        elif source_type == "web" and url:
            metadata["sources"] = [{"type": "url", "value": url}]

        # Create metadata file
        with open(os.path.join(persona_dir, "info.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        st.toast(f"Creating persona '{name}'...")
        with st.spinner(f"Setting up persona '{name}'..."):
            time.sleep(1)  # Brief delay for UX, replace with pipeline processing later
        st.success(f"Persona '{name}' created successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to create persona: {str(e)}")
        return False

def delete_persona_backend(name):
    st.toast(f"Persona '{name}' has been removed.")
    time.sleep(1)

def get_ai_response_backend(persona, user_message, chat_history):
    return f"This is a mock response from **{persona}**. You said: '{user_message}'"

# --- UI Screen Functions ---
def show_main_page():
    shimmering_text_css()
    st.markdown('<h1 class="shimmer">Who do you want me to be?</h1>', unsafe_allow_html=True)
    st.info("Create a new persona below, or select an existing one from the sidebar to begin chatting.")

    st.header("Create a New Persona")

    # Initialize checkbox states if form was reset
    if st.session_state.form_reset:
        upload_files = False
        fetch_web = False
    else:
        upload_files = st.session_state.get('upload_files', False)
        fetch_web = st.session_state.get('fetch_web', False)

    # Handle checkbox logic to ensure only one is selected
    def update_upload_files():
        st.session_state.upload_files = True
        st.session_state.fetch_web = False
        st.session_state.url = ""
        st.session_state.files = None

    def update_fetch_web():
        st.session_state.upload_files = False
        st.session_state.fetch_web = True
        st.session_state.files = None
        st.session_state.url = ""

    st.checkbox("Upload Files", value=upload_files, key="upload_files", on_change=update_upload_files)
    st.checkbox("Fetch from Web", value=fetch_web, key="fetch_web", on_change=update_fetch_web)

    # Show inputs based on checkbox state
    if st.session_state.upload_files:
        st.session_state.files = st.file_uploader("Upload documents (.pdf, .txt)", accept_multiple_files=True)
    elif st.session_state.fetch_web:
        st.session_state.url = st.text_input("Website URL", value=st.session_state.url, placeholder="e.g., https://www.gutenberg.org/ebooks/3600")
    else:
        st.session_state.files = None
        st.session_state.url = ""
        st.warning("Please select a data source.")

    # Form for submission
    with st.form(key="persona_form"):
        name = st.text_input("Persona Name", placeholder="e.g., My Mom, Albert Einstein")
        submitted = st.form_submit_button("Create Persona")
        if submitted:
            source_type = "local" if st.session_state.upload_files else "web" if st.session_state.fetch_web else None
            if create_new_persona_backend(name, source_type, files=st.session_state.files, url=st.session_state.url):
                # Signal form reset for next run
                st.session_state.form_reset = True
                st.session_state.files = None
                st.session_state.url = ""
                st.rerun()

def show_chat_screen():
    st.header(f"Conversing with: *{st.session_state.selected_persona}*")

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

# --- Confirmation Dialog for Deletion ---
@st.dialog("Confirm Deletion")
def confirm_delete(name):
    st.warning(f"Are you sure you want to delete the persona: **{name}**?")
    col1, col2 = st.columns(2)
    if col1.button("Yes, Delete", type="primary"):
        delete_persona_backend(name)
        st.rerun()
    if col2.button("Cancel"):
        st.rerun()

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("Persona AI")
    st.header("Your Personas")

    # If a persona is selected, show a button to go back to the main page
    if st.session_state.selected_persona:
        if st.button("🏠 Back to Main Page", use_container_width=True):
            st.session_state.selected_persona = None
            st.rerun()
    
    st.divider()

    # Display each persona with a select button and a delete button
    for name in get_personas():
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(name, key=f"select_{name}", use_container_width=True):
                st.session_state.selected_persona = name
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("❌", key=f"delete_{name}", use_container_width=True):
                confirm_delete(name)

# --- Main Page Router ---
if st.session_state.selected_persona is None:
    show_main_page()
else:
    show_chat_screen()