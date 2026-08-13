import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import io
import streamlit.components.v1 as components

st.set_page_config(page_title="sanjay's Smart Chat Bot", layout="wide")
st.title("sanjay's Smart Chat Bot 🤖🎤")

# ===== SIDEBAR =====
with st.sidebar:
    st.header("⚙️ Settings")
    model = st.selectbox("Choose Model", ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"])
    temperature = st.slider("Creativity", 0.0, 1.0, 0.7)
    speak_reply = st.checkbox("🔊 Speak Replies in English", value=True)

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
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
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# ===== PDF UPLOAD =====
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

# ===== VOICE INPUT BUTTON - BROWSER MIC =====
components.html(
    """
    <button id="startBtn" style="background:#4CAF50;color:white;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;font-size:16px;">🎤 Speak</button>
    <script>
    const startBtn = document.getElementById('startBtn');
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.continuous = false;

    startBtn.onclick = () => {
        recognition.start();
        startBtn.innerText = "⏹️ Listening...";
    }

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        window.parent.postMessage({type: "voice", text: transcript}, "*");
        startBtn.innerText = "🎤 Speak";
    }

    recognition.onerror = () => {
        startBtn.innerText = "🎤 Speak";
    }
    </script>
    """,
    height=50,
)

# Get voice text from JS
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# ===== TEXT INPUT =====
prompt = st.chat_input("Type in English or Click 🎤 Speak button above", key="chat_input")

# Check if voice came
if st.session_state.get("voice_text"):
    prompt = st.session_state.voice_text
    st.session_state.voice_text = "" # clear it

# ===== MAIN CHAT LOGIC =====
if prompt:
    # 1. Show YOUR question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Bot answers
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            messages_for_api = []
            system_prompt = "You are a helpful assistant. CRITICAL RULE: Always reply in English only."

            if all_file_text:
                system_prompt += f"\n\nUse this PDF content: \n\n{all_file_text[:12000]}"

            messages_for_api.append({"role": "system", "content": system_prompt})
            messages_for_api.extend(st.session_state.messages[-6:])

            stream = client.chat.completions.create(
                model=model, messages=messages_for_api,
                temperature=temperature, max_tokens=1024, stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

            if speak_reply and full_response:
                tts = gTTS(text=full_response, lang='en')
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                st.audio(audio_bytes, format="audio/mp3")

        except Exception as e:
            st.error(f"Error: {e}")
            full_response = "Sorry, something went wrong."
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# JS to Python bridge
components.html(
    """
    <script>
    window.addEventListener("message", (event) => {
        if (event.data.type === "voice") {
            const text = event.data.text;
            const input = window.parent.document.querySelector('input[type="text"]');
            if(input) {
                input.value = text;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
    </script>
    """,
    height=0,
)
