import streamlit as st
from groq import Groq
import PyPDF2
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io

st.set_page_config(page_title="sanjay's Smart Chat Bot", layout="wide")
st.title("sanjay's Smart Chat Bot 🤖🎤")

# ===== SIDEBAR =====
with st.sidebar:
    st.header("⚙️ Settings")
    model = st.selectbox("Choose Model", ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"])
    temperature = st.slider("Creativity", 0.0, 1.0, 0.7)
    speak_reply = st.checkbox("🔊 Speak Replies", value=True) # Voice reply on/off
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# API Key
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("GROQ_API_KEY not found!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Multiple PDF Upload
uploaded_files = st.file_uploader("📄 Upload PDF files", type=["pdf"], accept_multiple_files=True)
all_file_text = ""
if uploaded_files:
    for uploaded_file in uploaded_files:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text: all_file_text += text + "\n"
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===== VOICE INPUT + TEXT INPUT =====
col1, col2 = st.columns([5,1])
with col1:
    prompt = st.chat_input("Type or Use Mic...")
with col2:
    audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key="recorder")

# Mic la pesunaal adha text ah maathuren
if audio:
    # Groq ku audio anupi text ah vanguren - super fast
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio["bytes"]),
            model="whisper-large-v3",
        )
        prompt = transcription.text
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun() # Rerun panni chat la kaatradhuku
    except Exception as e:
        st.error(f"Voice Error: {e}")


if prompt:
    if not audio: # Text la type panni irundha mattum append pannu
        st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            messages_for_api = []
            if all_file_text:
                messages_for_api.append({"role": "system", "content": f"Use this PDF content: \n\n{all_file_text[:12000]}"})
            messages_for_api.extend(st.session_state.messages)

            stream = client.chat.completions.create(
                model=model, messages=messages_for_api,
                temperature=temperature, stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
            # ===== VOICE OUTPUT =====
            if speak_reply and full_response:
                tts = gTTS(text=full_response, lang='en') # 'en' ah 'ta' nu maathi Tamil pesavaikum
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                st.audio(audio_bytes, format="audio/mp3")
            
        except Exception as e:
            st.error(f"Error: {e}")
            full_response = "Sorry, something went wrong."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
