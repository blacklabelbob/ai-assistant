import streamlit as st
import chromadb
from anthropic import Anthropic
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Initialize ChromaDB
client = chromadb.Client()
collection = client.create_collection("chat_history")

# Streamlit app configuration
st.set_page_config(page_title="Business Assistant", layout="wide")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'context' not in st.session_state:
    st.session_state.context = ""

# UI Components
st.title("Business Assistant")

# Sidebar for document upload and context
with st.sidebar:
    st.header("Documents & Context")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'txt'])
    if uploaded_file:
        # Process uploaded file
        st.success("Document uploaded successfully!")
    
    st.header("Current Context")
    st.text(st.session_state.context or "No active context")

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input():
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get context from ChromaDB
    context = collection.query(
        query_texts=[prompt],
        n_results=5
    )
    
    # Prepare the complete prompt with context
    full_prompt = f"Context: {context}\n\nUser: {prompt}"
    
    # Get AI response
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    )
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response.content})
    
    # Store in ChromaDB
    collection.add(
        documents=[prompt + " " + response.content],
        metadatas=[{"timestamp": datetime.now().isoformat()}],
        ids=[str(len(st.session_state.messages))]
    )

# Export chat button
if st.button("Export Chat"):
    # Export chat history
    chat_export = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    st.download_button(
        label="Download Chat",
        data=chat_export,
        file_name="chat_export.txt",
        mime="text/plain"
    )