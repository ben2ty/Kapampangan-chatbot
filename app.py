import streamlit as st
from google import genai
from google.genai import types
import requests
import os

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Awane Istuya AI", page_icon="🇵🇭", layout="centered")
st.title("🇵🇭 Awane Istuya Chatbot")
st.markdown("*Magsalita tamu king Kapampangan!* (Let's speak in Kapampangan!)")

# Clear, independent variables to prevent string merging errors
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_GOOGLE_GEMINI_KEY_HERE").strip()
ELEVENLABS_API_KEY = st.secrets.get("ELEVENLABS_API_KEY", "YOUR_ELEVENLABS_API_KEY_HERE").strip()

# DO NOT put your API key here. Use a valid voice ID string from your ElevenLabs dashboard
ELEVENLABS_VOICE_ID = st.secrets.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM").strip() 

# Initialize the official Google GenAI client
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format="audio/mp3")


# --- 3. HELPER FUNCTIONS ---
def generate_kapampangan_tts(text):
    """Sends Kapampangan text to ElevenLabs and retrieves the audio bytes."""
       # HARDCODE THE BASE URL TO PREVENT ANY CORRUPTION, AND ONLY INJECT THE VOICE_ID
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + str(ELEVENLABS_VOICE_ID)
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
    "text": text,
    "model_id": "eleven_multilingual_v2", # Do not use v1 or Turbo for regional low-resource languages
    "voice_settings": {
        "stability": 0.42,          # Drops down to allow more emotional range and natural syllable pacing
        "similarity_boost": 0.70,   # High enough to keep the accent, low enough to avoid glitchy background noise
        "style": 0.0,               # MUST remain 0 for real-time applications to prevent massive latency spikes
        "use_speaker_boost": True   # Keeps the vocal structure clean and authentic to the original file
    }
}

    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            # THIS WILL PRINT THE EXACT ELEVENLABS ERROR TO YOUR STREAMLIT INTERFACE
            st.error(f"ElevenLabs API Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"TTS Connection Error: {e}")
    return None


# --- 4. USER INTERACTION & LOGIC ---
if user_input := st.chat_input("Sumulat kayung kapampangan keni... (Write in Kapampangan here...)"):
    
    # Display user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate AI Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # Enforce strict system instructions for regional language adherence
        system_instruction = (
            "You are a proud, helpful AI assistant built to preserve the Kapampangan language (Amanung Sisuan). "
            "You must converse exclusively in fluent, grammatically correct Kapampangan. "
            "Do not switch to Tagalog or English unless there is absolutely no native term available. "
            "Keep answers relatively concise so they sound natural when read aloud."
        )
        
        try:
            # Query Gemini 1.5 Pro (highly robust for local Philippine languages)
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            )
            ai_text = response.text
            response_placeholder.markdown(ai_text)
            
            # Generate and play corresponding voice audio
            with st.spinner("Mag-generate audio..."):
                audio_bytes = generate_kapampangan_tts(ai_text)
                
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
                st.session_state.messages.append({"role": "assistant", "content": ai_text, "audio": audio_bytes})
            else:
                st.session_state.messages.append({"role": "assistant", "content": ai_text})
                
        except Exception as e:
            st.error(f"Error querying Gemini: {e}")
