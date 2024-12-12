import streamlit as st
import chromadb
from anthropic import Anthropic
import openai
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize API clients
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize ChromaDB
client = chromadb.Client()
collection = client.create_collection("chat_history")

# Streamlit app configuration
st.set_page_config(page_title="Business Assistant", layout="wide")

# Add API test section
st.sidebar.header("API Status")

# Test Anthropic API
try:
    anthropic_response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": "Say 'Anthropic test successful' briefly"
        }]
    )
    st.sidebar.success("✅ Anthropic API Connected")
except Exception as e:
    st.sidebar.error(f"❌ Anthropic API Error: {str(e)}")

# Test OpenAI API
try:
    openai_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'OpenAI test successful' briefly"}],
        max_tokens=10
    )
    st.sidebar.success("✅ OpenAI API Connected")
except Exception as e:
    st.sidebar.error(f"❌ OpenAI API Error: {str(e)}")

# Add model selector
model_choice = st.sidebar.radio(
    "Choose AI Model:",
    ["Claude (Anthropic)", "GPT (OpenAI)"]
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat messages
st.title("Business Assistant")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input():
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        # Get response based on selected model
        if model_choice == "Claude (Anthropic)":
            response = anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            assistant_response = response.content[0].text
        else:  # OpenAI
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            assistant_response = response.choices[0].message.content

        # Add assistant response to chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # Store in ChromaDB
        collection.add(
            documents=[prompt + " " + assistant_response],
            metadatas=[{"timestamp": datetime.now().isoformat()}],
            ids=[str(len(st.session_state.messages))]
        )
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Export chat button
if st.sidebar.button("Export Chat"):
    chat_export = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    st.sidebar.download_button(
        label="Download Chat",
        data=chat_export,
        file_name="chat_export.txt",
        mime="text/plain"
    )