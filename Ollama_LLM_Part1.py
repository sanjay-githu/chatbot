import streamlit as st
from groq import Groq

st.title("sanjay's Smart Chat Bot")

# 1. API Key ah Secrets la irundhu edukudhu
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 2. Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Past messages ah kaatum
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. User input
if prompt := st.chat_input("Please Enter Your queries here or summarize the file..."):
    # User msg ah save pannu
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Bot reply
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama3-8b-8192",  # Groq free fast model
            messages=st.session_state.messages,
            stream=True,
        )
        response = st.write_stream(stream)
    
    # Bot reply ah save pannu
    st.session_state.messages.append({"role": "assistant", "content": response})
