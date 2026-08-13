import streamlit as st
from groq import Groq
import PyPDF2
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io

st.set_page_config(page_title="sanjay's Smart Chat Bot", layout="wide")
st.title("sanjay's Smart Chat Bot 🤖🎤")

# ===== SIDEBAR SETTINGS =====
with st.sidebar:
    st.header("⚙️ Settings")
    model = st.selectbox("Choose Model", ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"])
    temperature = st.slider("Creativity", 0.0, 1.0, 0.7)
    speak_reply = st.checkbox("🔊 Speak Replies in English", value=True)

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_audio_id = None # Voice bug fix
        st.rerun()

# ===== API KEY =====
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("GROQ_API_KEY not found!")
    st.stop()

# ===== CHAT HISTORY =====
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ===== MULTIPLE PDF UPLOAD =====
uploaded_files = st.file_uploader("📄 Upload PDF files", type=["pdf"], accept_multiple_files=True)
all_file_text = ""
if uploaded_files:
    with st.spinner("Reading PDFs..."):
        for uploaded_file in uploaded_files:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    all_file_text += text + "\n"
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

# ===== SHOW CHAT HISTORY =====
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===== VOICE INPUT + TEXT INPUT =====
col1, col2 = st.columns([5,1])
with col1:
    prompt = st.chat_input("Type in English or Click Mic to Speak...")
with col2:
    audio = mic_recorder(start_prompt="🎤 Mic", stop_prompt="⏹️ Stop", key="recorder")

# FIX 2: Process voice only once
if audio and audio["id"]!= st.session_state.last_audio_id:
    st.session_state.last_audio_id = audio["id"]
    try:
        with st.spinner("Transcribing your voice..."):
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", audio["bytes"]),
                model="whisper-large-v3",
            )
        prompt = transcription.text
        # Add to chat immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun() # This will show the text
    except Exception as e:
        st.error(f"Voice Error: {e}")

# ===== MAIN CHAT LOGIC =====
if prompt:
    # Don't add duplicate if it came from voice
    if not audio or audio["id"] == st.session_state.last_audio_id:
        if not any(m["content"] == prompt and m["role"] == "user" for m in st.session_state.messages[-2:]):
             st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            messages_for_api = []

            # FIX 1: Don't send full history if it's just "hi hello" spam
            # Send system + last 6 messages only
            system_prompt = "You are a helpful assistant. CRITICAL RULE: Always reply in English only. Answer the user's question directly. Do not repeat the user's message."

            if all_file_text:
                system_prompt += f"\n\nUse this PDF content: \n\n{all_file_text[:12000]}"

            messages_for_api.append({"role": "system", "content": system_prompt})
            messages_for_api.extend(st.session_state.messages[-6:]) # Only last 6 messages

            stream = client.chat.completions.create(
                model=model,
                messages=messages_for_api,
                temperature=temperature,
                max_tokens=1024,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            # Voice Output
            if speak_reply and full_response:
                tts = gTTS(text=full_response, lang='en')
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                st.audio(audio_bytes, format="audio/mp3")

        except Exception as e:
            st.error(f"Error: {e}")
            full_response = "Sorry, something went wrong."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
