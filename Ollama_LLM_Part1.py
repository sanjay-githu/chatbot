from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser 
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, AIMessage
import streamlit as st  
import PyPDF2

st.title("sanjay's Smart Chat Bot")

# clear chat history

if  st. button("CLear Chat"):
    st.session_state.messages = []
    st.session_state.file_content = ""
    st.rerun()

# session state inite
# chat history session save
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_content" not in st.session_state:
    st.session_state.file_content = ""

# file upload side bar
with st.sidebar:
    st.header("File Upload")
    uploaded_file = st.file_uploader("PDF or TXT file upload ", type=["pdf", "txt"])

    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            st.session_state.file_content = text
            st. success("PDF file read Completed")
        else:
            st.session_state.file_content = uploaded_file.read().decode("utf-8")
            st.success("TXT file read completed")

# expouse previous chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
# user input
input_txt = st.chat_input("Please Enter Your queries Here or summarize the file....")

if input_txt:
    st.session_state.messages.append({"role": "user", "content": input_txt})
    with st.chat_message("user"):
        st.write(input_txt)

# ollama setup
llm = Ollama(model="llama3") # streaming=True

# memory  prompt setup
# file content is add in system
system_msg = "you are a helpful and friendly AI assistant named sanjay's Assistant.Talk casually like a friend."
if st.session_state.file_content:
    file_text = st.session_state.file_content[:4000]
    system_msg += f"\n\n Use this Document Content to answer:\n{file_text}"

prompt = ChatPromptTemplate.from_messages(
    [("system", system_msg),
     MessagesPlaceholder(variable_name="chat_history"),
     ("user","{query}")
                                             ])

chain = prompt | llm | StrOutputParser()


# chat history langchainnku formattukku mathu 
chat_history =[]
for msg in st.session_state.messages[:-1]:
    if msg["role"] == "user":
        chat_history.append(HumanMessage(content=msg["content"]))
    else:
        chat_history.append(AIMessage(content=msg["content"]))

# bot reply generate pannum with streaming
with st.chat_message("assistant"):
    message_placeholder = st.empty()
    full_response = ""
    for chunk in chain.stream({"chat_history": chat_history, "query": input_txt}):
        full_response += chunk
        message_placeholder.write(full_response + "| ")
    message_placeholder.write(full_response)

# bot reply + save pannu chat history
st.session_state.messages.append({"role":"assistant", "content":full_response})
# with st.chat_message("assistant"):
#     st.write(full_response)