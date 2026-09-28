# Tech Stack & Guidelines

- **Core Language**: Python 3.x
- **Web Interface**: Streamlit (for rapid development of the interactive UI)
- **Generative AI**: Google Gemini (via `google-genai` library) for conversational capabilities and translation
- **Network/API**: `requests` for handling external API communications
- **Data Source**: Kapampangan Voice Script (primary reference for linguistic accuracy)

## Library & Module Usage Rules

### 1. UI & Interactivity
- Always use **Streamlit** primitives (`st.chat_message`, `st.text_input`, `st.button`, etc.) to build the user interface.
- Manage application state using `st.session_state` to maintain chat history and user preferences.
- Ensure the layout is responsive and suitable for both desktop and mobile web views.

### 2. AI & Conversational Logic
- Use the `google-genai` library for all interactions with the Gemini model.
- Implement prompt engineering techniques to ensure the assistant maintains the Kapampangan persona and accuracy.
- Integrate the content from `Kapampangan Voice script.txt` as context or reference for the model's responses.

### 3. Data & Networking
- Use `requests` for any necessary calls to external web services or APIs.
- Use standard Python file I/O for reading and processing local text resources like the voice script.

### 4. Project Structure
- `app.py`: The main entry and logic entry point for the Streamlit application.
- `requirements.txt`: Must contain all necessary Python dependencies.
- `Kapampangan Voice script.txt`: The core linguistic resource for the chatbot.
