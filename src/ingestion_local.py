

import logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('app.log', mode='w')  # Output to a file
    ]
)
logger = logging.getLogger(__name__)


import os
import traceback
import pdfplumber
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import streamlit as st


from config.config import PERSONAS_DIR, CHROMA_DIR

def debug_log(message):
    """Log both to console and Streamlit (if available)"""
    logger.debug(message)  # Use logger instead of print
    # try:
    #     st.write(f"🔍 {message}")  # Only works in Streamlit context
    # except:
    #     pass  # Ignore if not in Streamlit context

def process_local_files(persona_name: str, files: list):
    """
    Processes uploaded .txt and .pdf files with improved error handling and logging.
    """
    try:
        debug_log(f"**Debug Info**: Processing {len(files)} files for persona '{persona_name}'")
        
        documents = []
        for i, file in enumerate(files):
            try:
                
                # Validate file size
                file_size = len(file.getvalue())
                if file_size == 0:
                    debug_log(f"WARNING: File '{file.name}' is empty, skipping...")
                    continue
                
                
                # Reset file pointer
                file.seek(0)
                
                # Read the content based on file type
                if file.type == "application/pdf":
                    debug_log(f"Processing PDF: {file.name}")
                    with pdfplumber.open(file) as pdf:
                        text = ""
                        for page_num, page in enumerate(pdf.pages):
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text
                        
                elif file.type == "text/plain" or file.name.endswith('.txt'):
                    debug_log(f"Processing text file: {file.name}")
                    text = file.getvalue().decode("utf-8")
                else:
                    # Try to process as text anyway
                    try:
                        text = file.getvalue().decode("utf-8")
                    except UnicodeDecodeError:
                        error_msg = f"Cannot decode file '{file.name}' as text. Please ensure it's a valid text file."
                        debug_log(f"ERROR: {error_msg}")
                        try:
                            st.error(f"❌ {error_msg}")
                        except:
                            pass
                        continue
                
                if not text or not text.strip():
                    debug_log(f"WARNING: No text extracted from '{file.name}', skipping...")
                    continue
                
                debug_log(f"SUCCESS: Extracted {len(text):,} characters from '{file.name}'")
                
                # Create document object
                doc = type('Document', (object,), {
                    'page_content': text.strip(), 
                    'metadata': {'source': file.name}
                })
                documents.append(doc)
                
            except Exception as file_error:
                error_msg = f"Error processing file '{file.name}': {str(file_error)}"
                debug_log(f"ERROR: {error_msg}")
                continue

        if not documents:
            error_msg = "No valid documents found to process!"
            debug_log(f"ERROR: {error_msg}")
            return False

        debug_log(f"SUCCESS: Successfully processed {len(documents)} documents")


        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        debug_log(f"Created {len(chunks)} chunks for embedding")

        # Check if Ollama is accessible
        try:
            embeddings = OllamaEmbeddings(model="llama3:8b")
            # Test the embeddings with a small text
            test_embedding = embeddings.embed_query("test")
            debug_log(f"SUCCESS: Embeddings model loaded successfully (dimension: {len(test_embedding)})")
        except Exception as embed_error:
            error_msg = f"Failed to initialize embeddings model: {str(embed_error)}"
            debug_log(f"ERROR: {error_msg}")

            try:
                st.error(f"❌ {error_msg}")
                st.error("💡 Make sure Ollama is running and the 'llama3:8b' model is available")
            except:
                pass
            return False

        debug_log("Creating vector store...")
        
        # Create vector store
        persist_directory = os.path.join(PERSONAS_DIR, persona_name, CHROMA_DIR)
        debug_log(f"Vector store path: {persist_directory}")
        
        try:
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=persist_directory,
            )
            debug_log(f"SUCCESS: Vector store created with {len(chunks)} chunks")
            return True
            
        except Exception as chroma_error:
            error_msg = f"Failed to create vector store: {str(chroma_error)}"
            debug_log(f"ERROR: {error_msg}")
            print(f"CHROMA ERROR TRACEBACK: {traceback.format_exc()}")
            try:
                st.error(f"❌ {error_msg}")
            except:
                pass
            return False
        
    except Exception as e:
        error_msg = f"Unexpected error during local file processing: {str(e)}"
        debug_log(f"ERROR: {error_msg}")
        print(f"FULL TRACEBACK: {traceback.format_exc()}")
        try:
            st.error(f"❌ {error_msg}")
            st.error(f"🔍 Traceback: {traceback.format_exc()}")
        except:
            pass
        return False