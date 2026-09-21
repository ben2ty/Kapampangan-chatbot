import hashlib
import os

import requests
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Awane Istuya AI", page_icon="🇵🇭", layout="centered")
st.title("🇵🇭 Awane Istuya Chatbot")
st.markdown("*Magsalita tamu king Kapampangan!* (Let's speak in Kapampangan!)")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_GOOGLE_GEMINI_KEY_HERE").strip()
ELEVENLABS_API_KEY = st.secrets.get(
    "ELEVENLABS_API_KEY", "YOUR_ELEVENLABS_API_KEY_HERE"
).strip()
ELEVENLABS_VOICE_ID = st.secrets.get(
    "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"
).strip()

client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_audio" not in st.session_state:
    st.session_state.processed_audio = None

# The selected mode controls both input and output. Voice mode uses Gemini for STT
# and ElevenLabs for TTS; chat-only mode never calls ElevenLabs.
mode = st.radio(
    "Pili ka paraan ning pamag-istorya:",
    ("💬 Chat only", "🎙️ Casual conversation (voice)"),
    horizontal=True,
    help="Voice mode transcribes your recording and reads the Kapampangan reply aloud.",
)
voice_mode = mode.startswith("🎙️")

# Display previous chat messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("audio"):
            st.audio(message["audio"], format="audio/mp3")


# --- 3. HELPER FUNCTIONS ---
def generate_kapampangan_tts(text):
    """Send Kapampangan text to ElevenLabs and return the audio bytes."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.42,
            "similarity_boost": 0.70,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.content
        st.error(f"ElevenLabs API Error {response.status_code}: {response.text}")
    except requests.RequestException as exc:
        st.error(f"TTS Connection Error: {exc}")
    return None


def transcribe_kapampangan_audio(audio_file):
    """Use Gemini's audio understanding to turn a recording into text."""
    audio_bytes = audio_file.getvalue()
    mime_type = audio_file.type or "audio/wav"
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                (
                    "Transcribe this recording exactly. The speaker is using Kapampangan "
                    "(Amanung Sisuan). Return only the transcription, without translation, "
                    "explanation, or quotation marks."
                ),
            ],
            config=types.GenerateContentConfig(temperature=0.0),
        )
        return response.text.strip()
    except Exception as exc:
        st.error(f"STT Error: {exc}")
    return None


def respond_to_user(user_input, include_audio):
    """Generate a reply and optionally synthesize it for voice mode."""
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    system_instruction = (
        "You are a proud, helpful AI assistant built to preserve the Kapampangan language "
        "(Amanung Sisuan). You must converse exclusively in fluent, grammatically correct "
        "Kapampangan. Do not switch to Tagalog or English unless there is absolutely no "
        "native term available. Keep answers relatively concise so they sound natural when "
        "read aloud."
    )

    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                ),
            )
            ai_text = response.text
            st.markdown(ai_text)

            audio_bytes = None
            if include_audio:
                with st.spinner("Mag-generate audio..."):
                    audio_bytes = generate_kapampangan_tts(ai_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

            message = {"role": "assistant", "content": ai_text}
            if audio_bytes:
                message["audio"] = audio_bytes
            st.session_state.messages.append(message)
        except Exception as exc:
            st.error(f"Error querying Gemini: {exc}")


# --- 4. USER INTERACTION & LOGIC ---
if voice_mode:
    st.info("Pindutan ing mikropono, magsalita, at isubmit ing rekording mu.")
    with st.form("voice_form", clear_on_submit=True):
        audio_input = st.audio_input("Magsalita king Kapampangan")
        voice_submitted = st.form_submit_button("Ipadala / Send")

    if voice_submitted and audio_input:
        # Prevent the same recording from being processed twice on a rerun.
        audio_id = hashlib.sha256(audio_input.getvalue()).hexdigest()
        if audio_id != st.session_state.processed_audio:
            with st.spinner("Magsulat ning sasabian mu..."):
                transcribed_text = transcribe_kapampangan_audio(audio_input)
            if transcribed_text:
                st.session_state.processed_audio = audio_id
                respond_to_user(transcribed_text, include_audio=True)
    elif voice_submitted:
        st.warning("Magsalita ka muna bago ipadala ing rekording mu.")
else:
    if user_input := st.chat_input(
        "Sumulat kayung kapampangan keni... (Write in Kapampangan here...)"
    ):
        respond_to_user(user_input, include_audio=False)
