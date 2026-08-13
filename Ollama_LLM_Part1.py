import streamlit as st
from groq import Groq
import PyPDF2

st.set_page_config(page_title="sanjay's Smart Chat Bot")
st.title("sanjay's Smart Chat Bot 🤖")

# API Key
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("GROQ_API_KEY not found! Please add it in Streamlit Secrets")
    st.stop()

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# File Upload
uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])
file_text = ""
if uploaded_file:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            file_text += text
    st.success(f"✅ File uploaded: {uploaded_file.name}")

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Please Enter Your queries here..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # PDF irundha, adha first message ah anupuvom
            messages_for_api = []
            if file_text:
                messages_for_api.append({"role": "system", "content": f"You are a helpful assistant. Use the following PDF content to answer questions: \n\n{file_text[:8000]}"})
            
            messages_for_api.extend(st.session_state.messages)

            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages_for_api,
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
