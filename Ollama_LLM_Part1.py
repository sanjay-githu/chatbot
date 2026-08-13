import streamlit as st
from groq import Groq
import PyPDF2

st.title("sanjay's Smart Chat Bot")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
file_text = ""
if uploaded_file:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        if page.extract_text():
            file_text += page.extract_text()
    st.success(f"File uploaded: {uploaded_file.name}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Please Enter Your queries here..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # PDF irundha system prompt ah add panren
        messages_to_send = []
        if file_text:
            messages_to_send.append({"role": "system", "content": f"PDF Content: {file_text[:4000]}"})
        messages_to_send.extend(st.session_state.messages)
        
        stream = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages_to_send,
            stream=True,
        )
        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
