import streamlit as st
from groq import Groq
import PyPDF2

st.set_page_config(page_title="sanjay's Smart Chat Bot", layout="wide")
st.title("sanjay's Smart Chat Bot 🤖")

# ===== SIDEBAR SETTINGS =====
with st.sidebar:
    st.header("⚙️ Settings")
    
    model = st.selectbox(
        "Choose Model",
        ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "gemma2-9b-it"]
    )
    
    temperature = st.slider("Creativity", 0.0, 1.0, 0.7)
    
    max_tokens = st.slider("Max Reply Length", 100, 4000, 1024)
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# API Key
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("GROQ_API_KEY not found! Please add it in Streamlit Secrets")
    st.stop()

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===== MULTIPLE FILE UPLOAD =====
uploaded_files = st.file_uploader("📄 Upload PDF files", type=["pdf"], accept_multiple_files=True)
all_file_text = ""
if uploaded_files:
    for uploaded_file in uploaded_files:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                all_file_text += text + "\n"
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask anything about your PDFs..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            messages_for_api = []
            if all_file_text:
                messages_for_api.append({"role": "system", "content": f"You are a helpful assistant. Use the following PDF contents to answer questions: \n\n{all_file_text[:12000]}"})
            
            messages_for_api.extend(st.session_state.messages)

            stream = client.chat.completions.create(
                model=model, # Sidebar la select panradhu
                messages=messages_for_api,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"Error: {e}")
            full_response = "Sorry, something went wrong."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
