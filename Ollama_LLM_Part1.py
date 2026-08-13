import streamlit as st
from groq import Groq
import PyPDF2

st.title("sanjay's Smart Chat Bot")

# 1. API Key
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 2. Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. File Upload
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
file_text = ""
if uploaded_file:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        if page.extract_text():
            file_text += page.extract_text()
    st.success(f"File uploaded: {uploaded_file.name}")

# 4. Show past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. User input
if prompt := st.chat_input("Please Enter Your queries here or summarize the file..."):
    
    # PDF irundha adhai system message ah add pannuvom
    messages_to_send = []
    if file_text:
        messages_to_send.append({"role": "system", "content": f"Use this PDF content to answer: {file_text[:3000]}"})
    
    messages_to_send.extend(st.session_state.messages)
    messages_to_send.append({"role": "user", "content": prompt})

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages_to_send,  # Clean messages ah anupuren
            stream=True,
        )
        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
